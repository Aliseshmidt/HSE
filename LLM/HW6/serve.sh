#!/usr/bin/env bash
set -euo pipefail

export VLLM_SERVER_DEV_MODE=1
config="${CONFIG:-baseline}"
args=(--seed 42 --revision b968826d9c46dd6066d109eabc6255188de91218)

case "$config" in
    baseline)
        ;;
    chunk2048)
        args+=(--max-num-batched-tokens 2048)
        ;;
    graphs|spec)
        args+=(--max-num-batched-tokens 2048 --max-num-seqs 128)
        args+=(--compilation-config '{"cudagraph_capture_sizes":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,48,64,96,128]}')
        if [[ "$config" == spec ]]; then
            draft="$(python3 -c 'from huggingface_hub import snapshot_download; print(snapshot_download("RedHatAI/Qwen3-8B-speculator.eagle3",revision="08610ffa01dd9f16731fe8f627b85905b6aa51c4"))')"
            args+=(--speculative-config "{\"method\":\"eagle3\",\"model\":\"$draft\",\"num_speculative_tokens\":3}")
        fi
        ;;
    *)
        echo "Unknown CONFIG: $config" >&2
        exit 2
        ;;
esac

exec vllm serve Qwen/Qwen3-8B "${args[@]}" "$@"
