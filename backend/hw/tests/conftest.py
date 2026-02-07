from typing import Any, Mapping, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from main import app
from http import HTTPStatus
from model import ensure_model_exists
from database import db
from repositories.users import user_repository
from repositories.items import item_repository
import asyncio
import os
from urllib.parse import quote_plus


@pytest.fixture(scope="session", autouse=True)
def load_model_for_tests():
    ensure_model_exists()
    model = ensure_model_exists()
    app.state.model = model
    yield


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    test_db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://user:%20@localhost:5432/backend_avito"
    )
    os.environ["DATABASE_URL"] = test_db_url

    try:
        await db.connect()
        yield
        try:
            await db.execute("TRUNCATE TABLE items, users RESTART IDENTITY CASCADE")
        except Exception as e:
            print(f"Ошибка при очистке БД: {e}")
    finally:
        await db.disconnect()


@pytest.fixture
def app_client() -> Generator[TestClient, None, None]:
    if not hasattr(app.state, 'model') or app.state.model is None:
        model = ensure_model_exists()
        app.state.model = model
    return TestClient(app)


@pytest_asyncio.fixture
async def async_app_client():
    if not hasattr(app.state, 'model') or app.state.model is None:
        model = ensure_model_exists()
        app.state.model = model

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user():
    user = await user_repository.create(
        seller_id=1,
        is_verified_seller=True
    )
    return user


@pytest_asyncio.fixture
async def test_item(test_user):
    item = await item_repository.create(
        item_id=100,
        seller_id=test_user['seller_id'],
        name="Test 0",
        description="Test 0",
        category=50,
        images_qty=5
    )
    return item