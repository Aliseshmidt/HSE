from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt

from repositories.accounts import account_repository


class AuthError(Exception):
    pass


class AuthService:
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expires_minutes: int = 60,
    ):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expires_minutes = access_token_expires_minutes

    async def authenticate_user(self, login: str, password: str) -> Dict[str, Any]:
        account = await account_repository.get_by_login_and_password(
            login=login,
            password=password,
        )
        if account is None or account.get("is_blocked"):
            raise AuthError("Invalid credentials or account blocked")
        return account

    def create_access_token(self, account: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self._access_token_expires_minutes)

        payload = {
            "sub": str(account["id"]),
            "login": account["login"],
            "exp": expire,
        }
        token = jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
        return token

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError("Invalid token") from exc
        return payload


def get_auth_service() -> AuthService:
    secret_key = "very-secret-key"
    return AuthService(secret_key=secret_key)

