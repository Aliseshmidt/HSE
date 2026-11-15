"""Collect original AIPerf exports and reproduce the summary and two figures."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

DATA_SHA256 = "67c48379e5ae2608f7ca08650fd346facdc01f766a3e8eecea6459d7cec00ebc"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
DRAFT_REVISION = "08610ffa01dd9f16731fe8f627b85905b6aa51c4"


def collect(root):
    dataset_hash = hashlib.sha256(
        (root / "data/requests.jsonl").read_bytes()
    ).hexdigest()
    assert dataset_hash == DATA_SHA256
    exports = sorted((root / "results").glob("*/profile/profile_export_aiperf.json"))
    assert exports, "No completed AIPerf exports found"
    runs = []
    for path in exports:
        run = dict(name=path.parent.parent.name, aiperf=json.loads(path.read_text()))
        counters_path = path.parent.parent / "engine_metrics.txt"
        if counters_path.exists():
            counters = re.findall(
                r"^vllm:(spec_decode_num_(?:drafts|draft_tokens|accepted_tokens)_total)\{[^\n]*\} ([0-9.e+\-]+)$",
                counters_path.read_text(),
                re.MULTILINE,
            )
            run["server_counters_cumulative_including_warmup"] = {
                name: float(value) for name, value in counters
            }
        runs.append(run)
    gpu = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=name,uuid,driver_version,memory.total",
            "--format=csv,noheader",
            "--id=0",
        ],
        text=True,
    ).strip()
    engine = json.loads(
        subprocess.check_output(
            [
                "/usr/bin/python3",
                "-c",
                "import json; from importlib.metadata import version; "
                "print(json.dumps({p:version(p) for p in ['vllm','torch','transformers']}))",
            ],
            text=True,
        )
    )
    result = dict(
        target="Qwen/Qwen3-8B",
        target_revision=MODEL_REVISION,
        draft="RedHatAI/Qwen3-8B-speculator.eagle3",
        draft_revision=DRAFT_REVISION,
        dataset_sha256=dataset_hash,
        dataset_rows=640,
        gpu=gpu,
        engine_versions=engine,
        scripts_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.glob("*.sh")
        },
        runs=runs,
    )
    (root / "results/measurements.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    return result


def normalize(data):
    rows = []
    for run in data["runs"]:
        match = re.fullmatch(r"(load-)?([a-z0-9]+)-(\d+)rpm", run["name"])
        assert match, run["name"]
        is_load, config, rpm = match.groups()
        export = run["aiperf"]
        assert export["aiperf_version"] == "0.13.0"
        assert export["request_latency"]["unit"] == "ms"
        phase = next(
            p for p in export["input_config"]["phases"] if p["kind"] == "profiling"
        )
        assert abs(phase["rate"] * 60 - int(rpm)) < 0.001
        requests = int(export["request_count"]["avg"])
        errors = int(export.get("error_request_count", {}).get("avg", 0))
        complete = bool(export["is_complete"] and not export["was_cancelled"])
        latency = export["request_latency"]
        if not is_load:
            assert phase["requests"] == 640
            assert requests + errors == 640
        assert export["usage_completion_tokens"]["max"] <= 512
        duration = phase.get("duration")
        rows.append(
            dict(
                run=run["name"],
                kind="load" if is_load else "benchmark",
                config=config,
                rpm=int(rpm),
                requests=requests,
                errors=errors,
                complete=complete,
                requested_duration_s=duration,
                elapsed_s=export["benchmark_duration"]["avg"],
                mean_latency_s=latency["avg"] / 1000,
                p90_latency_s=latency["p90"] / 1000,
                achieved_rpm=export["request_throughput"]["avg"] * 60,
                mean_output_tokens=export["usage_completion_tokens"]["avg"],
                sla_pass=bool(
                    is_load
                    and duration == 300
                    and complete
                    and errors == 0
                    and latency["p90"] < 15000
                ),
            )
        )
    rows.sort(key=lambda r: (r["kind"], r["config"], r["rpm"]))
    baseline = next(r for r in rows if r["config"] == "baseline" and r["rpm"] == 120)
    for row in rows:
        row["speedup_mean_120"] = (
            baseline["mean_latency_s"] / row["mean_latency_s"]
            if row["rpm"] == 120 and row["kind"] == "benchmark"
            else None
        )
    return rows


def plot(rows, root):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "figure.dpi": 150})
    folder = root / "results/plots"
    folder.mkdir(parents=True, exist_ok=True)
    points = {(r["config"], r["rpm"]): r for r in rows if r["kind"] == "benchmark"}
    rates = sorted(
        {
            rpm
            for config, rpm in points
            if config == "graphs" and ("spec", rpm) in points
        }
    )
    if rates:
        figure, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
        for config, label in [
            ("graphs", "Without speculation"),
            ("spec", "EAGLE3, k=3"),
        ]:
            axes[0].plot(
                rates,
                [points[config, r]["p90_latency_s"] for r in rates],
                marker="o",
                label=label,
            )
            timed_out = [rpm for rpm in rates if points[config, rpm]["errors"]]
            if timed_out:
                axes[0].scatter(
                    timed_out,
                    [points[config, rpm]["p90_latency_s"] for rpm in timed_out],
                    marker="x",
                    color="red",
                    s=70,
                    zorder=4,
                    label="Request timeouts",
                )
        axes[0].set(xlabel="Offered load, RPM", ylabel="P90 E2E latency, s")
        axes[0].legend()
        speedups = [
            points["graphs", r]["p90_latency_s"] / points["spec", r]["p90_latency_s"]
            for r in rates
        ]
        axes[1].plot(rates, speedups, marker="o")
        axes[1].axhline(1, color="red", ls="--", lw=1)
        axes[1].set(
            xlabel="Offered load, RPM", ylabel="P90 speedup, plain / speculative"
        )
        first_slower = next((i for i, value in enumerate(speedups) if value < 1), None)
        if first_slower is not None:
            rpm = rates[first_slower]
            axes[1].scatter([rpm], [speedups[first_slower]], color="red", zorder=4)
            axes[1].annotate(
                f"First slower: {rpm} RPM",
                (rpm, speedups[first_slower]),
                xytext=(0.45, 0.80),
                textcoords="axes fraction",
                arrowprops={"arrowstyle": "->", "linewidth": 0.8},
            )
            if first_slower > 0:
                for ax in axes:
                    ax.axvspan(rates[first_slower - 1], rpm, color="grey", alpha=0.12)
        for ax in axes:
            ax.grid(alpha=0.25)
        figure.savefig(folder / "speculation.png")
        plt.close(figure)

    loads = [r for r in rows if r["kind"] == "load"]
    if loads:
        loads.sort(key=lambda r: r["rpm"])
        assert len({r["config"] for r in loads}) == 1
        figure, ax = plt.subplots(figsize=(7, 4), layout="constrained")
        ax.plot(
            [r["rpm"] for r in loads],
            [r["mean_latency_s"] for r in loads],
            marker="o",
            label="Mean",
        )
        ax.plot(
            [r["rpm"] for r in loads],
            [r["p90_latency_s"] for r in loads],
            marker="o",
            label="P90",
        )
        ax.axhline(15, color="red", ls="--", label="SLA, P90 < 15 s")
        passed = [r for r in loads if r["sla_pass"]]
        if passed:
            best = max(passed, key=lambda r: r["rpm"])
            ax.scatter(
                [best["rpm"]],
                [best["p90_latency_s"]],
                s=90,
                color="green",
                zorder=4,
                label=f"Max passed: {best['rpm']} RPM",
            )
        failed = [r for r in loads if not r["sla_pass"]]
        if failed:
            ax.scatter(
                [row["rpm"] for row in failed],
                [row["p90_latency_s"] for row in failed],
                marker="x",
                s=80,
                color="red",
                zorder=4,
                label="SLA failed",
            )
        ax.set(
            xlabel="Offered load, RPM",
            ylabel="E2E latency, s",
            title=loads[0]["config"] + ", 300-second tests",
        )
        ax.grid(alpha=0.25)
        ax.legend()
        figure.savefig(folder / "load.png")
        plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Read original AIPerf run directories inside the GPU container",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    data = (
        collect(root)
        if args.collect
        else json.loads((root / "results/measurements.json").read_text())
    )
    rows = normalize(data)
    with (root / "results/metrics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    plot(rows, root)
    for row in rows:
        print(
            row["run"],
            f"mean={row['mean_latency_s']:.3f}s p90={row['p90_latency_s']:.3f}s",
            f"requests={row['requests']} errors={row['errors']}",
        )


if __name__ == "__main__":
    main()
