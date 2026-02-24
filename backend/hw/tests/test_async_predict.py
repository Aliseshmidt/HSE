from http import HTTPStatus
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from repositories.users import user_repository
from repositories.items import item_repository
from repositories.moderation_results import moderation_result_repository


@pytest.mark.asyncio
async def test_async_predict_create_task(async_app_client: AsyncClient):
    user = await user_repository.create(
        seller_id=1000,
        is_verified_seller=False
    )

    item = await item_repository.create(
        item_id=2000,
        seller_id=user['seller_id'],
        name="Test Item for Async",
        description="Test description",
        category=50,
        images_qty=2
    )

    with patch('routers.async_predict.get_kafka_producer') as mock_get_producer:
        mock_producer = AsyncMock()
        mock_producer.send_moderation_request = AsyncMock(return_value=None)
        mock_get_producer.return_value = mock_producer

        response = await async_app_client.post(
            "/async_predict",
            json={"item_id": item['item_id']}
        )

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert "task_id" in data
    assert data["status"] == "pending"
    assert data["message"] == "Moderation request accepted"
    assert isinstance(data["task_id"], int)

    moderation_result = await moderation_result_repository.get_by_id(data["task_id"])
    assert moderation_result is not None
    assert moderation_result["status"] == "pending"
    assert moderation_result["item_id"] == item["id"]

    mock_producer.send_moderation_request.assert_called_once_with(item['item_id'])


@pytest.mark.asyncio
async def test_async_predict_item_not_found(async_app_client: AsyncClient):
    response = await async_app_client.post(
        "/async_predict",
        json={"item_id": 99999}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    data = response.json()
    assert "не найдено" in data["detail"].lower() or "not found" in data["detail"].lower()