import json
from unittest.mock import AsyncMock

import pytest

from prediction_storage import PredictionStorage


@pytest.mark.asyncio
async def test_get_by_item_id_uses_correct_key_and_parses(monkeypatch):
    storage = PredictionStorage(ttl_seconds=123)

    mock_client = AsyncMock()
    payload = {"is_violation": True, "probability": 0.42}
    mock_client.get.return_value = json.dumps(payload).encode()

    monkeypatch.setattr("prediction_storage.get_redis", lambda: mock_client)

    result = await storage.get_by_item_id(555)

    mock_client.get.assert_awaited_once_with("prediction:item:555")
    assert result == (True, 0.42)


@pytest.mark.asyncio
async def test_set_by_item_id_uses_correct_key_and_ttl(monkeypatch):
    ttl = 321
    storage = PredictionStorage(ttl_seconds=ttl)

    mock_client = AsyncMock()
    monkeypatch.setattr("prediction_storage.get_redis", lambda: mock_client)

    await storage.set_by_item_id(555, True, 0.42)

    mock_client.set.assert_awaited_once()
    args, kwargs = mock_client.set.call_args

    assert args[0] == "prediction:item:555"
    stored = json.loads(args[1])
    assert stored == {"is_violation": True, "probability": 0.42}
    assert kwargs["ex"] == ttl


@pytest.mark.asyncio
async def test_get_by_task_id_uses_correct_key_and_parses(monkeypatch):
    storage = PredictionStorage(ttl_seconds=100)

    mock_client = AsyncMock()
    payload = {"status": "completed", "is_violation": False, "probability": 0.1}
    mock_client.get.return_value = json.dumps(payload).encode()

    monkeypatch.setattr("prediction_storage.get_redis", lambda: mock_client)

    result = await storage.get_by_task_id(777)

    mock_client.get.assert_awaited_once_with("prediction:task:777")
    assert result == ("completed", False, 0.1)


@pytest.mark.asyncio
async def test_set_by_task_id_uses_correct_key_and_ttl(monkeypatch):
    ttl = 50
    storage = PredictionStorage(ttl_seconds=ttl)

    mock_client = AsyncMock()
    monkeypatch.setattr("prediction_storage.get_redis", lambda: mock_client)

    await storage.set_by_task_id(777, "completed", True, 0.9)

    mock_client.set.assert_awaited_once()
    args, kwargs = mock_client.set.call_args

    assert args[0] == "prediction:task:777"
    stored = json.loads(args[1])
    assert stored == {
        "status": "completed",
        "is_violation": True,
        "probability": 0.9,
    }
    assert kwargs["ex"] == ttl


@pytest.mark.asyncio
async def test_delete_by_item_id_uses_correct_key(monkeypatch):
    storage = PredictionStorage(ttl_seconds=10)
    mock_client = AsyncMock()
    monkeypatch.setattr("prediction_storage.get_redis", lambda: mock_client)

    await storage.delete_by_item_id(111)

    mock_client.delete.assert_awaited_once_with("prediction:item:111")


@pytest.mark.asyncio
async def test_delete_by_task_id_uses_correct_key(monkeypatch):
    storage = PredictionStorage(ttl_seconds=10)
    mock_client = AsyncMock()
    monkeypatch.setattr("prediction_storage.get_redis", lambda: mock_client)

    await storage.delete_by_task_id(222)

    mock_client.delete.assert_awaited_once_with("prediction:task:222")

