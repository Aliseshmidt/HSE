# ДЗ6. Инференс

Результаты и объяснения находятся в [REPORT.md](REPORT.md). Исходные данные находятся в `data/requests.jsonl`.

- `serve.sh` содержит четыре конфигурации, выбираемые через `CONFIG=baseline`, `chunk2048`, `graphs` или `spec`.
- `benchmark.sh` измеряет 640 запросов, нагрузка задается через `RPM`, по умолчанию 120.
- `load_test.sh` держит заданный RPM 300 секунд.
- `run_experiments.sh` последовательно запускает серверы и замеры.
- `analyze.py` собирает экспорты AIPerf в таблицу и строит графики.
- `results/metrics.csv` содержит все замеры. `results/measurements.json` сохраняет исходные JSON-экспорты, версии, GPU, ревизии моделей и хеш данных. Графики находятся в `results/plots/`.

Повторить эксперименты можно в новой рабочей папке на сервере с A100. В контейнер передается физический GPU 0. Нужен настроенный NVIDIA container runtime.

```bash
mkdir reproduce
cp Dockerfile serve.sh benchmark.sh load_test.sh run_experiments.sh analyze.py reproduce/
cp -R data reproduce/
cd reproduce
sudo docker build -t hw6-inference .
sudo docker run --rm -it --gpus device=0 --ipc=host \
  -e NVIDIA_REQUIRE_CUDA='cuda>=12.0' -e CUDA_VISIBLE_DEVICES=0 \
  -e HF_HOME=/cache -e OMP_NUM_THREADS=4 -e MAX_JOBS=4 \
  -v "$PWD":/homework -v hw6-hf-cache:/cache \
  hw6-inference bash
```

Внутри контейнера выполняются следующие команды.

```bash
bash run_experiments.sh configs
bash run_experiments.sh sweep
bash run_experiments.sh load spec 150 165
bash run_experiments.sh load spec 240
python3 analyze.py --collect
```

В режиме `load` уровни передаются по возрастанию. После первого нарушения SLA дальнейшие уровни этого вызова пропускаются.

Модель закреплена на revision `b968826d9c46dd6066d109eabc6255188de91218`, EAGLE3 на `08610ffa01dd9f16731fe8f627b85905b6aa51c4`. В данных заданы seed=42, temperature=0, максимум 512 токенов и выключенный thinking. Использованы vLLM 0.22.0 и AIPerf 0.13.0. Перед и после каждого замера очищается prefix cache, перед замерами выполняются 40 прогревочных запросов.

Сохраненные графики и CSV можно пересобрать из `measurements.json` командой `python3 analyze.py`. Все рабочие файлы новых прогонов создаются внутри `reproduce/`.
