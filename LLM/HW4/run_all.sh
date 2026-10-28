#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false
work_dir="${1:-reproduction}"
python experiment.py --prepare --work-dir "$work_dir"
for name in base full lora lora_r16 lora_alpha32 lora_dropout01 lora_all; do
    python -u experiment.py --run "$name" --work-dir "$work_dir"
done
python experiment.py --summarize --work-dir "$work_dir"
