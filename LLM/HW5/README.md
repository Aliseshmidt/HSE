# ДЗ5. RL для Function Calling

Отчет с таблицами, графиками и ответами на вопросы находится в [REPORT.md](REPORT.md).

`prepare_data.py` готовит ToolACE, `rewards.py` считает награду, `train_rl.py` обучает модель через TRL, `export_model.py` объединяет LoRA с исходными весами. Фактические конфиги трех запусков собраны в `configs.json`. Для повторения оценки приложены исходные `evaluate.py`, `bfcl.jsonl` и Dockerfile с версиями библиотек.

Seed и data_seed равны **42**. Модель `Qwen/Qwen3.5-2B` закреплена на revision `15852e8c16360a2fea060d615a32b45270f8a8fc`, данные `Team-ACE/ToolACE` на revision `6bda777c88d21e5a204703c1ee45597a8fa4f734`. Целые диалоги разделены до нарезки на префиксы. Подготовлены 1536 train и 128 validation.

| Запуск | Loss | Награда | Нормировка наград |
|---|---|---|---|
| rl1_exact | GRPO | exact | group std |
| rl2_dense | GRPO | dense | group std |
| rl3_drgrpo | Dr. GRPO | dense | none |

Во всех запусках 16 шагов, LR 1e-5, warmup 2, beta 0.01, epsilon 0.2, batch 2, accumulation 4, четыре генерации на запрос, temperature 0.8, top_p 0.95, максимум 512 новых токенов, BF16. LoRA использует r=16, alpha=32, dropout=0 и language-MLP gate/up/down. Выбран последний шаг 16. Дополнительная ToolACE-валидация завершена для RL-1, остановлена после сохранения адаптера RL-2 и пропущена для RL-3.

Все четыре модели проверены на 350 запросах BFCL. Результаты лежат в `results/base/`, `results/rl1_exact/`, `results/rl2_dense/`, `results/rl3_drgrpo/`. В каждой папке есть `metrics.json` и `predictions.jsonl`. Финальная оценка использует объединенные веса, temperature=0, максимум 1024 токена, seed=42 и выключенный thinking.

Повторить эксперимент можно в новой рабочей папке на одной A100. Команды рассчитаны на Docker с настроенным NVIDIA container runtime. В контейнер передается физический GPU 1, внутри он получает индекс 0.

```bash
mkdir reproduction
cp Dockerfile evaluate.py bfcl.jsonl prepare_data.py rewards.py train_rl.py export_model.py reproduction/
cd reproduction
docker build -t rlvr-homework .
docker run --rm --gpus device=1 --ipc=host \
  -e CUDA_VISIBLE_DEVICES=0 -e OMP_NUM_THREADS=4 \
  -v "$PWD":/workspace -v rlvr-hf-cache:/cache \
  rlvr-homework bash -lc '
set -e
python3 prepare_data.py
python3 evaluate.py Qwen/Qwen3.5-2B --output results/base
for name in rl1_exact rl2_dense rl3_drgrpo; do
    python3 train_rl.py --config "$name" --steps 16 --skip-validation
    python3 export_model.py "$name"
    python3 evaluate.py "./checkpoints/$name" --output "results/$name"
done
'
```

Окружение основных запусков содержит Python 3.12, torch 2.11.0+cu129, TRL 1.16.0, Transformers 5.9.0, PEFT 0.18.1, vLLM 0.22.0+cu129 и bfcl-eval 2026.3.23. Подготовка данных, обучение и экспорт создают рабочие файлы внутри новой папки `reproduction/`.
