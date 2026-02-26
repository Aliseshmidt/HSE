import redis.asyncio as redis
from typing import Optional


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

redis_client: Optional[redis.Redis] = None


async def connect_redis() -> None:
    """
    Инициализация глобального подключения к Redis.
    Вызывается один раз при старте приложения.
    """
    global redis_client

    if redis_client is None:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
        )
        # Проверяем, что соединение установлено
        await redis_client.ping()


async def close_redis() -> None:
    """
    Корректное закрытие соединения с Redis при завершении работы приложения.
    """
    global redis_client

    if redis_client is not None:
        await redis_client.close()
        redis_client = None


def get_redis() -> redis.Redis:
    """
    Возвращает инициализированный клиент Redis.
    """
    if redis_client is None:
        raise RuntimeError("Redis ещё не инициализирован. Вызовите connect_redis() при старте приложения.")
    return redis_client

import redis.asyncio as redis
from typing import Optional

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

redis_client: Optional[redis.Redis] = None


async def connect_redis() -> None:
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
        )
        # Проверим соединение
        await redis_client.ping()


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None


def get_redis() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis еще не инициализирован. Вызовите connect_redis() при старте приложения.")
    return redis_client