from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_login_success_sets_cookie(client: TestClient, monkeypatch):
    from routers import auth as auth_router_module

    mock_service = AsyncMock()
    mock_service.authenticate_user = AsyncMock(
        return_value={"id": 1, "login": "user", "is_blocked": False}
    )
    mock_service.create_access_token = lambda account: "test-token"

    def _get_auth_service_override():
        return mock_service

    app.dependency_overrides[auth_router_module.get_auth_service] = _get_auth_service_override

    response = client.post(
        "/login",
        json={"login": "user", "password": "pass"},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == 1
    assert data["login"] == "user"
    assert data["is_blocked"] is False

    cookies = response.cookies
    assert "access_token" in cookies
    assert cookies.get("access_token") == "test-token"

    app.dependency_overrides.clear()


def test_login_invalid_credentials(client: TestClient, monkeypatch):
    from routers import auth as auth_router_module
    from services.auth import AuthError

    mock_service = AsyncMock()
    mock_service.authenticate_user = AsyncMock(side_effect=AuthError("Invalid"))

    def _get_auth_service_override():
        return mock_service

    app.dependency_overrides[auth_router_module.get_auth_service] = _get_auth_service_override

    response = client.post(
        "/login",
        json={"login": "user", "password": "wrong"},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED

    app.dependency_overrides.clear()

