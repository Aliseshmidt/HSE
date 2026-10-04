#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p output_dir/logs

run() {
  local name="$1"
  shift
  # A separate cold compiler cache makes wall-clock comparisons fair and keeps
  # every run independent from both foreign work and earlier local probes.
  TORCHINDUCTOR_CACHE_DIR="$PWD/.torchinductor/${name}" \
    python your_solution.py train --name "$name" "$@" 2>&1 | tee "output_dir/logs/${name}.log"
}

case "${1:-}" in
  prepare)
    python your_solution.py prepare 2>&1 | tee output_dir/logs/prepare.log
    ;;
  batch-probes)
    for batch_size in 8 16 32 64; do
      run "probe_bs${batch_size}" --time-budget 60 --max-steps 100000 \
        --set per_device_train_batch_size="${batch_size}" \
        --set eval_every_seconds=0 --set generate_after_training=false \
        --set full_eval=false --set save_model=false --set save_on_timeout=false
    done
    run probe_bs16_ga2 --time-budget 60 --max-steps 100000 \
      --set per_device_train_batch_size=16 --set gradient_accumulation_steps=2 \
      --set eval_every_seconds=0 --set generate_after_training=false \
      --set full_eval=false --set save_model=false --set save_on_timeout=false
    ;;
  lr-probes)
    for learning_rate in 3e-4 6e-4 1e-3; do
      run "probe_lr${learning_rate}" --time-budget 120 --max-steps 100000 \
        --set learning_rate="${learning_rate}" \
        --set eval_every_seconds=0 --set generate_after_training=false \
        --set full_eval=false --set save_model=false --set save_on_timeout=false
    done
    ;;
  scheduler-probes)
    for scheduler in constant linear cosine; do
      run "probe_sched_${scheduler}" --time-budget 120 --max-steps 100000 \
        --set time_scheduler="${scheduler}" \
        --set eval_every_seconds=0 --set generate_after_training=false \
        --set full_eval=false --set save_model=false --set save_on_timeout=false
    done
    ;;
  system-probes)
    run probe_no_compile --time-budget 60 --max-steps 100000 \
      --set torch_compile=false --set eval_every_seconds=0 --set generate_after_training=false \
      --set full_eval=false --set save_model=false --set save_on_timeout=false
    run probe_adamw_foreach --time-budget 60 --max-steps 100000 \
      --set optim=adamw_torch --set eval_every_seconds=0 --set generate_after_training=false \
      --set full_eval=false --set save_model=false --set save_on_timeout=false
    run probe_fp32_master --time-budget 60 --max-steps 100000 \
      --set fp32_master_weights=true --set eval_every_seconds=0 --set generate_after_training=false \
      --set full_eval=false --set save_model=false --set save_on_timeout=false
    run probe_no_tf32 --time-budget 60 --max-steps 100000 \
      --set tf32=false --set eval_every_seconds=0 --set generate_after_training=false \
      --set full_eval=false --set save_model=false --set save_on_timeout=false
    ;;
  baseline)
    run baseline --time-budget 900 --max-steps 100000 \
      --set per_device_train_batch_size=4 --set learning_rate=5e-5 \
      --set weight_decay=0.01 --set adam_beta2=0.999 --set time_scheduler=constant \
      --set logging_steps=1 --set generate_after_training=false \
      --set save_model=false --set save_on_timeout=false
    ;;
  final)
    run final --time-budget 900 --max-steps 100000
    ;;
  *)
    echo "Usage: $0 {prepare|batch-probes|lr-probes|scheduler-probes|system-probes|baseline|final}" >&2
    exit 2
    ;;
esac
