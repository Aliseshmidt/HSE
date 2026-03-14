from http import HTTPStatus
from typing import Dict, Any, Optional

from fastapi import Cookie, Depends, HTTPException

from repositories.accounts import account_repository
from services.auth import get_auth_service, AuthService, AuthError


async def get_current_account(
    access_token: Optional[str] = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> Dict[str, Any]:
    if not access_token:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = auth_service.decode_token(access_token)
    except AuthError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid token",
        )

    account_id = int(payload["sub"])
    account = await account_repository.get_by_id(account_id)
    if account is None or account.get("is_blocked"):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Account not found or blocked",
        )

    return account

