from http import HTTPStatus
from httpx import AsyncClient
import pytest
from repositories.users import user_repository
from repositories.items import item_repository

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_simple_predict_positive(async_app_client: AsyncClient):
    user = await user_repository.create(
        seller_id=1,
        is_verified_seller=False
    )
    item = await item_repository.create(
        item_id=101,
        seller_id=user['seller_id'],
        name="Test 1",
        description="Test 1",
        category=50,
        images_qty=1
    )

    response = await async_app_client.post(f"/simple_predict/{item['item_id']}")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert isinstance(data["is_violation"], bool)
    assert isinstance(data["probability"], float)


@pytest.mark.asyncio
async def test_simple_predict_negative(async_app_client: AsyncClient):
    user = await user_repository.create(
        seller_id=2,
        is_verified_seller=True
    )
    item = await item_repository.create(
        item_id=102,
        seller_id=user['seller_id'],
        name="Test 2",
        description="Test 2",
        category=30,
        images_qty=5
    )

    response = await async_app_client.post(f"/simple_predict/{item['item_id']}")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data


@pytest.mark.asyncio
async def test_simple_predict_not_found(async_app_client: AsyncClient):
    response = await async_app_client.post("/simple_predict/99999")

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio
async def test_create_user_and_item(async_app_client: AsyncClient):
    user = await user_repository.create(
        seller_id=3,
        is_verified_seller=True
    )
    assert user['seller_id'] == 3
    assert user['is_verified_seller'] is True

    item = await item_repository.create(
        item_id=103,
        seller_id=user['seller_id'],
        name="Test 3",
        description="Test 3",
        category=10,
        images_qty=3
    )
    assert item['item_id'] == 103
    assert item['seller_id'] == 3

    retrieved_item = await item_repository.get_by_item_id(103)
    assert retrieved_item is not None
    assert retrieved_item['name'] == "Test 3"
    assert retrieved_item['is_verified_seller'] is True