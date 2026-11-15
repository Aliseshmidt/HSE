#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export URL="${URL:-http://localhost:8000}"
mkdir -p logs results
server_pid=""

stop_server() {
    if [[ -n "$server_pid" ]]; then
        kill -TERM -- "-$server_pid" 2>/dev/null || true
        for attempt in {1..20}; do
            if ! kill -0 "$server_pid" 2>/dev/null; then break; fi
            sleep 1
        done
        kill -KILL -- "-$server_pid" 2>/dev/null || true
        wait "$server_pid" 2>/dev/null || true
        server_pid=""
    fi
}
trap stop_server EXIT

start_server() {
    local config="$1"
    local stamp
    stamp="$(date +%Y%m%d-%H%M%S)"
    stop_server
    echo "Starting $config at $stamp"
    setsid env CONFIG="$config" bash serve.sh > "logs/server-${config}-${stamp}.log" 2>&1 &
    server_pid=$!
    for attempt in {1..450}; do
        if curl -fsS "$URL/health" >/dev/null 2>&1; then
            echo "Ready $config"
            return
        fi
        if ! kill -0 "$server_pid" 2>/dev/null; then
            tail -n 40 "logs/server-${config}-${stamp}.log"
            return 1
        fi
        sleep 2
    done
    echo "Server readiness timeout" >&2
    return 1
}

benchmark() {
    local config="$1" rpm="$2"
    local output="results/${config}-${rpm}rpm"
    if [[ -f "$output/profile/profile_export_aiperf.json" ]]; then
        echo "Already measured $output"
        return
    fi
    echo "Benchmark $config at $rpm RPM"
    RPM="$rpm" bash benchmark.sh "$output" > "logs/benchmark-${config}-${rpm}.log" 2>&1
    curl -fsS "$URL/metrics" > "$output/engine_metrics.txt"
}

case "${1:-configs}" in
    configs)
        for config in baseline chunk2048 graphs spec; do
            if [[ -f "results/${config}-120rpm/profile/profile_export_aiperf.json" ]]; then continue; fi
            start_server "$config"
            benchmark "$config" 120
        done
        ;;
    sweep)
        for config in graphs spec; do
            start_server "$config"
            for rpm in 240 480 720; do benchmark "$config" "$rpm"; done
        done
        ;;
    load)
        config="${2:?Specify the selected configuration}"
        shift 2
        start_server "$config"
        for rpm in "$@"; do
            output="results/load-${config}-${rpm}rpm"
            echo "Load test $config at $rpm RPM for 300 seconds"
            bash load_test.sh "$rpm" "$output" > "logs/load-${config}-${rpm}.log" 2>&1
            curl -fsS "$URL/metrics" > "$output/engine_metrics.txt"
            if python3 - "$output/profile/profile_export_aiperf.json" <<'PY'
import json
from pathlib import Path
import sys

result = json.loads(Path(sys.argv[1]).read_text())
failed = (
    result["request_latency"]["p90"] >= 15000
    or result.get("error_request_count", {}).get("avg", 0) > 0
    or not result["is_complete"]
)
sys.exit(0 if failed else 1)
PY
            then
                echo "SLA failed at $rpm RPM; stopping higher load levels"
                break
            fi
        done
        ;;
    *)
        echo "Use configs, sweep or load CONFIG RPM..." >&2
        exit 2
        ;;
esac
