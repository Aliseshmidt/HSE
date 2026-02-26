from http import HTTPStatus

import pytest
from httpx import AsyncClient

from repositories.users import user_repository
from repositories.items import item_repository
from repositories.moderation_results import moderation_result_repository
from prediction_storage import prediction_storage
from redis_client import get_redis

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_close_item_deletes_from_db_and_redis(async_app_client: AsyncClient):
    user = await user_repository.create(
        seller_id=500,
        is_verified_seller=True,
    )
    item = await item_repository.create(
        item_id=600,
        seller_id=user["seller_id"],
        name="Close test",
        description="Close test description",
        category=10,
        images_qty=2,
    )

    moderation_result = await moderation_result_repository.create(item["id"])
    task_id = moderation_result["id"]

    await prediction_storage.set_by_item_id(item["item_id"], True, 0.9)
    await prediction_storage.set_by_task_id(task_id, "completed", True, 0.9)

    client = get_redis()
    assert await client.get(f"prediction:item:{item['item_id']}") is not None
    assert await client.get(f"prediction:task:{task_id}") is not None

    response = await async_app_client.post(
        "/close",
        json={"item_id": item["item_id"]},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["item_id"] == item["item_id"]
    assert data["status"] == "closed"

    assert await item_repository.get_by_item_id(item["item_id"]) is None
    assert await moderation_result_repository.get_by_id(task_id) is None

    assert await client.get(f"prediction:item:{item['item_id']}") is None
    assert await client.get(f"prediction:task:{task_id}") is None


@pytest.mark.asyncio
async def test_close_item_not_found(async_app_client: AsyncClient):
    response = await async_app_client.post(
        "/close",
        json={"item_id": 999999},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    data = response.json()
    assert "не найдено" in data["detail"].lower() or "not found" in data["detail"].lower()

