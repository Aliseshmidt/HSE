import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_run(run_dir):
    summary_path = run_dir / "run_summary.json"
    state_path = run_dir / "trainer_state.json"
    if not summary_path.exists() or not state_path.exists():
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    summary["history"] = state["log_history"]
    return summary


def smooth(values, window=15):
    result = []
    for index in range(len(values)):
        start = max(0, index - window + 1)
        result.append(sum(values[start:index + 1]) / (index - start + 1))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="output_dir/runs")
    parser.add_argument("--report-dir", default="report")
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    runs = {path.name: load_run(path) for path in sorted(runs_dir.iterdir()) if path.is_dir()}
    runs = {name: run for name, run in runs.items() if run is not None}

    rows = []
    for name, run in runs.items():
        rows.append({
            "run": name,
            "time_budget_s": run["time_budget_seconds"],
            "batch_size": run["training_config"]["per_device_train_batch_size"],
            "gradient_accumulation": run["training_config"]["gradient_accumulation_steps"],
            "learning_rate": run["training_config"]["learning_rate"],
            "scheduler": run["experiment_config"]["time_scheduler"],
            "torch_compile": run["training_config"]["torch_compile"],
            "optim": run["training_config"]["optim"],
            "steps": run["global_step"],
            "tokens_per_second": round(run["train_tokens_per_second"], 1),
            "eval_loss": run["eval_loss"],
            "perplexity": run["perplexity"],
            "peak_gpu_memory_gb": round(run["peak_gpu_memory_gb"], 2),
        })
    if rows:
        with (report_dir / "results.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    final = runs.get("final")
    if final:
        train_logs = [item for item in final["history"] if "loss" in item]
        x = [item["elapsed_sec"] for item in train_logs]
        y = [item["loss"] for item in train_logs]
        fig, axis = plt.subplots(figsize=(10, 5.5))
        axis.plot(x, y, alpha=0.25, linewidth=0.8, label="train loss")
        axis.plot(x, smooth(y), linewidth=2, label="train loss, moving average")
        evaluations = [item for item in final["history"] if "eval_loss" in item]
        if evaluations:
            axis.scatter(
                [item["elapsed_sec"] for item in evaluations],
                [item["eval_loss"] for item in evaluations],
                marker="o",
                s=45,
                label="eval loss",
            )
        axis.set(title="Qwen3-1B mini-pretrain: loss over time", xlabel="Training time, seconds", ylabel="Loss")
        axis.grid(alpha=0.25)
        axis.legend()
        fig.tight_layout()
        fig.savefig(report_dir / "loss_curves.png", dpi=180)
        plt.close(fig)

    probes = [(name, run) for name, run in runs.items() if name.startswith("probe_")]
    if probes:
        names = [name.removeprefix("probe_") for name, _ in probes]
        losses = [run["eval_loss"] for _, run in probes]
        fig, axis = plt.subplots(figsize=(12, 5.5))
        bars = axis.bar(names, losses)
        axis.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
        axis.set(title="Short-run hyperparameter probes", ylabel="Eval loss (500-example subset)")
        axis.tick_params(axis="x", rotation=35)
        axis.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(report_dir / "probe_eval_loss.png", dpi=180)
        plt.close(fig)

    print(f"Loaded {len(runs)} runs; wrote artifacts to {report_dir}")


if __name__ == "__main__":
    main()
