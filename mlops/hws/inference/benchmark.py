import asyncio
import time
import json
import statistics
import psutil
import os
from typing import List, Dict, Any
import aiohttp

URL = "http://localhost:8002/embed"
CONCURRENCY = 50
TOTAL_REQUESTS = 1000
TEXTS = [
    "Привет, мир!",
    "Как дела?",
    "Это тестовый текст для бенчмарка.",
    "Еще один текст, чтобы проверить производительность.",
    "Модель rubert-mini-frida создана для русского языка."
] * 10000

async def send_request(session, text):
    start = time.perf_counter()
    async with session.post(URL, json={"text": text}) as resp:
        await resp.json()
    end = time.perf_counter()
    return end - start

async def run_benchmark():
    process = psutil.Process(os.getpid())
    cpu_start = process.cpu_percent(interval=None)
    mem_start = process.memory_info().rss / 1024 / 1024

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def bounded_request(text):
            async with semaphore:
                return await send_request(session, text)

        tasks = [bounded_request(TEXTS[i % len(TEXTS)]) for i in range(TOTAL_REQUESTS)]
        start_time = time.perf_counter()
        latencies = await asyncio.gather(*tasks)
        end_time = time.perf_counter()

    total_time = end_time - start_time
    rps = TOTAL_REQUESTS / total_time

    cpu_end = process.cpu_percent(interval=None)
    mem_end = process.memory_info().rss / 1024 / 1024

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.5)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    print(f"Total requests: {TOTAL_REQUESTS}, concurrency: {CONCURRENCY}")
    print(f"Throughput: {rps:.2f} req/s")
    print(f"Latency (s): avg={statistics.mean(latencies):.3f}, p50={p50:.3f}, p95={p95:.3f}, p99={p99:.3f}")
    print(f"CPU usage: start={cpu_start:.1f}%, end={cpu_end:.1f}%")
    print(f"Memory usage: start={mem_start:.1f} MB, end={mem_end:.1f} MB")

if __name__ == "__main__":
    asyncio.run(run_benchmark())