# HW1: mini-pretrain Qwen3-1B на русской Wikipedia

## Воспроизводимость

```bash
source ~/venv-hw1/bin/activate
python your_solution.py prepare
bash run_experiments.sh batch-probes
bash run_experiments.sh lr-probes
bash run_experiments.sh final
python plot_losses.py
```

Точные параметры и метрики каждого запуска автоматически сохраняются в `output_dir/runs/<name>/run_summary.json` и `trainer_state.json`.

## Неизменяемая часть эксперимента

- Dataset: `wikimedia/wikipedia`, конфигурация `20231101.ru`, split `train`.
- Validation: первые 5000 примеров; train: все последующие примеры.
- Tokenizer: `ai-forever/rugpt3small_based_on_gpt2`; `pad_token = eos_token`.
- Длина каждого блока: 512 токенов (`truncation=True`, `padding="max_length"`).
- Model: Qwen3, 12 слоёв, hidden size 2048, 16 attention heads, 8 KV heads, MLP 8192; инициализация с нуля.
- Финальный train: 900 секунд по wall clock через `TimeoutCallback`.

## Результаты

Финальный запуск: `bs=16`, `gradient_accumulation_steps=1`, `lr=1e-3`, wall-clock cosine scheduler,
BF16/TF32, fused AdamW и `torch_compile`.

- `eval_loss` на всех 5000 validation-примерах: **5.4807**;
- perplexity: **240.01**;
- 3193 шага и 26.16 млн token positions за 15 минут оптимизации;
- peak GPU memory: 16.53 GB.

Графики, таблица экспериментов, генерации и подробные выводы находятся в [report/README.md](report/README.md).
