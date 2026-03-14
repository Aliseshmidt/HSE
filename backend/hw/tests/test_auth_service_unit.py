from datetime import datetime, timedelta, timezone

import jwt
import pytest
from unittest.mock import AsyncMock, patch

from services.auth import AuthService, AuthError


@pytest.mark.asyncio
async def test_authenticate_user_success():
    from services import auth as auth_module

    mock_repo = AsyncMock()
    account = {"id": 1, "login": "user", "password": "pass", "is_blocked": False}
    mock_repo.get_by_login_and_password = AsyncMock(return_value=account)

    with patch.object(auth_module, "account_repository", mock_repo):
        service = AuthService(secret_key="secret")
        result = await service.authenticate_user("user", "pass")

    assert result == account
    mock_repo.get_by_login_and_password.assert_awaited_once_with(
        login="user",
        password="pass",
    )


@pytest.mark.asyncio
async def test_authenticate_user_invalid_credentials():
    from services import auth as auth_module

    mock_repo = AsyncMock()
    mock_repo.get_by_login_and_password = AsyncMock(return_value=None)

    with patch.object(auth_module, "account_repository", mock_repo):
        service = AuthService(secret_key="secret")
        with pytest.raises(AuthError):
            await service.authenticate_user("user", "wrong")


@pytest.mark.asyncio
async def test_authenticate_user_blocked_account():
    from services import auth as auth_module

    mock_repo = AsyncMock()
    mock_repo.get_by_login_and_password = AsyncMock(
        return_value={"id": 1, "login": "user", "password": "pass", "is_blocked": True}
    )

    with patch.object(auth_module, "account_repository", mock_repo):
        service = AuthService(secret_key="secret")
        with pytest.raises(AuthError):
            await service.authenticate_user("user", "pass")


def test_create_and_decode_token_roundtrip():
    account = {"id": 1, "login": "user"}
    service = AuthService(secret_key="secret", access_token_expires_minutes=5)

    token = service.create_access_token(account)
    payload = service.decode_token(token)

    assert payload["sub"] == "1"
    assert payload["login"] == "user"
    assert "exp" in payload


def test_decode_token_expired():
    secret = "secret"
    service = AuthService(secret_key=secret)

    now = datetime.now(timezone.utc)
    expired = now - timedelta(minutes=1)
    payload = {
        "sub": "1",
        "login": "user",
        "exp": expired,
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    with pytest.raises(AuthError):
        service.decode_token(token)


def test_decode_token_invalid_signature():
    service = AuthService(secret_key="correct-secret")

    payload = {
        "sub": "1",
        "login": "user",
    }
    token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

    with pytest.raises(AuthError):
        service.decode_token(token)

