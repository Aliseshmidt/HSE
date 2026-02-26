import json
from typing import Optional, Tuple

from redis_client import get_redis


# TTL кэша в секундах.
# 5 минут выбраны как компромисс:
# - за это время пользователь обычно успевает сделать несколько повторных запросов
#   по одному и тому же объявлению, и мы обслужим их из кэша, не нагружая БД и модель;
# - при этом, если объявление изменится или будет закрыто, устаревшие данные
#   не будут лежать в Redis слишком долго и не приведут к заметной рассинхронизации.
PREDICTION_TTL_SECONDS = 300


class PredictionStorage:
    def __init__(self, ttl_seconds: int = PREDICTION_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds

    def _item_key(self, item_id: int) -> str:
        return f"prediction:item:{item_id}"

    def _task_key(self, task_id: int) -> str:
        return f"prediction:task:{task_id}"

    async def get_by_item_id(self, item_id: int) -> Optional[Tuple[bool, float]]:
        client = get_redis()
        raw = await client.get(self._item_key(item_id))
        if raw is None:
            return None

        try:
            payload = json.loads(raw)
            return bool(payload["is_violation"]), float(payload["probability"])
        except Exception:
            return None

    async def set_by_item_id(self, item_id: int, is_violation: bool, probability: float) -> None:
        client = get_redis()
        payload = json.dumps(
            {
                "is_violation": bool(is_violation),
                "probability": float(probability),
            }
        )
        await client.set(self._item_key(item_id), payload, ex=self.ttl_seconds)

    async def delete_by_item_id(self, item_id: int) -> None:
        client = get_redis()
        await client.delete(self._item_key(item_id))

    async def get_by_task_id(self, task_id: int) -> Optional[Tuple[str, Optional[bool], Optional[float]]]:
        client = get_redis()
        raw = await client.get(self._task_key(task_id))
        if raw is None:
            return None

        try:
            payload = json.loads(raw)
            status = str(payload["status"])
            is_violation = payload.get("is_violation")
            probability = payload.get("probability")
            if is_violation is not None:
                is_violation = bool(is_violation)
            if probability is not None:
                probability = float(probability)
            return status, is_violation, probability
        except Exception:
            return None

    async def set_by_task_id(
        self,
        task_id: int,
        status: str,
        is_violation: Optional[bool],
        probability: Optional[float],
    ) -> None:
        client = get_redis()
        payload = json.dumps(
            {
                "status": status,
                "is_violation": is_violation,
                "probability": probability,
            }
        )
        await client.set(self._task_key(task_id), payload, ex=self.ttl_seconds)

    async def delete_by_task_id(self, task_id: int) -> None:
        client = get_redis()
        await client.delete(self._task_key(task_id))


prediction_storage = PredictionStorage()

