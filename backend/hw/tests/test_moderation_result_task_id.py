from http import HTTPStatus
import pytest
from httpx import AsyncClient
from repositories.users import user_repository
from repositories.items import item_repository
from repositories.moderation_results import moderation_result_repository


@pytest.mark.asyncio
async def test_get_moderation_result_pending(async_app_client: AsyncClient):
    user = await user_repository.create(
        seller_id=100,
        is_verified_seller=False
    )
    item = await item_repository.create(
        item_id=200,
        seller_id=user['seller_id'],
        name="Test Item",
        description="Test Description",
        category=50,
        images_qty=1
    )

    moderation_result = await moderation_result_repository.create(item['id'])
    task_id = moderation_result['id']

    response = await async_app_client.get(f"/moderation_result/{task_id}")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "pending"
    assert data["is_violation"] is None
    assert data["probability"] is None


@pytest.mark.asyncio
async def test_get_moderation_result_completed(async_app_client: AsyncClient):
    user = await user_repository.create(
        seller_id=101,
        is_verified_seller=False
    )
    item = await item_repository.create(
        item_id=201,
        seller_id=user['seller_id'],
        name="Test Item",
        description="Test Description",
        category=50,
        images_qty=1
    )

    moderation_result = await moderation_result_repository.create(item['id'])
    task_id = moderation_result['id']

    await moderation_result_repository.update_status(
        moderation_id=task_id,
        status="completed",
        is_violation=True,
        probability=0.87
    )

    response = await async_app_client.get(f"/moderation_result/{task_id}")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] == "completed"
    assert data["is_violation"] is True
    assert data["probability"] == 0.87


@pytest.mark.asyncio
async def test_get_moderation_result_not_found(async_app_client: AsyncClient):
    response = await async_app_client.get("/moderation_result/99999")

    assert response.status_code == HTTPStatus.NOT_FOUND
    data = response.json()
    assert "не найдена" in data["detail"].lower() or "not found" in data["detail"].lower()