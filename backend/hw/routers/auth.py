from http import HTTPStatus

from fastapi import APIRouter, Depends, Response, HTTPException
from pydantic import BaseModel

from services.auth import get_auth_service, AuthService, AuthError


router = APIRouter(prefix="", tags=["auth"])


class LoginInDto(BaseModel):
    login: str
    password: str


class LoginOutDto(BaseModel):
    id: int
    login: str
    is_blocked: bool


@router.post("/login", response_model=LoginOutDto)
async def login(
    dto: LoginInDto,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginOutDto:
    try:
        account = await auth_service.authenticate_user(
            login=dto.login,
            password=dto.password,
        )
    except AuthError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = auth_service.create_access_token(account)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
    )

    return LoginOutDto(
        id=account["id"],
        login=account["login"],
        is_blocked=account["is_blocked"],
    )

