from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from dependencies.auth import get_current_account


app = FastAPI()


@app.get("/protected")
async def protected_route(account=Depends(get_current_account)):
    return {"id": account["id"], "login": account["login"]}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_current_account_success(client: TestClient, monkeypatch):
    from dependencies import auth as auth_dep_module

    mock_auth_service = AsyncMock()
    mock_auth_service.decode_token = lambda token: {"sub": "1", "login": "user"}

    mock_repo = AsyncMock()
    mock_repo.get_by_id = AsyncMock(
        return_value={"id": 1, "login": "user", "is_blocked": False}
    )

    def _get_auth_service_override():
        return mock_auth_service

    app.dependency_overrides[auth_dep_module.get_auth_service] = _get_auth_service_override

    with patch.object(auth_dep_module, "account_repository", mock_repo):
        response = client.get("/protected", cookies={"access_token": "token"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == 1
    assert data["login"] == "user"

    app.dependency_overrides.clear()


def test_get_current_account_no_cookie(client: TestClient):
    response = client.get("/protected")
    assert response.status_code == HTTPStatus.UNAUTHORIZED

