import pytest

from prediction_storage import prediction_storage, PREDICTION_TTL_SECONDS
from redis_client import get_redis

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_prediction_storage_item_roundtrip_with_real_redis():
    client = get_redis()

    item_id = 12345
    is_violation = True
    probability = 0.77

    await prediction_storage.set_by_item_id(item_id, is_violation, probability)

    raw = await client.get(f"prediction:item:{item_id}")
    assert raw is not None

    cached = await prediction_storage.get_by_item_id(item_id)
    assert cached == (is_violation, probability)

    ttl = await client.ttl(f"prediction:item:{item_id}")
    assert ttl > 0
    assert ttl <= PREDICTION_TTL_SECONDS

    await prediction_storage.delete_by_item_id(item_id)
    assert await client.get(f"prediction:item:{item_id}") is None


@pytest.mark.asyncio
async def test_prediction_storage_task_roundtrip_with_real_redis():
    client = get_redis()

    task_id = 999
    status = "completed"
    is_violation = False
    probability = 0.12

    await prediction_storage.set_by_task_id(task_id, status, is_violation, probability)

    raw = await client.get(f"prediction:task:{task_id}")
    assert raw is not None

    cached = await prediction_storage.get_by_task_id(task_id)
    assert cached == (status, is_violation, probability)

    ttl = await client.ttl(f"prediction:task:{task_id}")
    assert ttl > 0
    assert ttl <= PREDICTION_TTL_SECONDS

    await prediction_storage.delete_by_task_id(task_id)
    assert await client.get(f"prediction:task:{task_id}") is None

