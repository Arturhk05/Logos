from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.modules.auth.dependencies import SESSION_COOKIE, CurrentUser, get_auth_service
from app.modules.auth.schemas import LoginRequest, UserResponse
from app.modules.auth.service import AuthService

COOKIE_PATH = "/api"

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=UserResponse)
def login(credentials: LoginRequest, response: Response, service: Annotated[AuthService, Depends(get_auth_service)]) -> UserResponse:
    user = service.authenticate(credentials.username, credentials.password)
    response.set_cookie(
        SESSION_COOKIE,
        service.issue_token(user),
        max_age=int(service.token_lifetime.total_seconds()),
        path=COOKIE_PATH,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return UserResponse.model_validate(user)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    # The path must match login's, otherwise the browser keeps the original cookie.
    response.delete_cookie(SESSION_COOKIE, path=COOKIE_PATH, httponly=True, secure=True, samesite="strict")


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)
