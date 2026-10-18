from datetime import timedelta
from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.modules.auth.service import AuthService
from app.modules.users.models import User
from app.modules.users.repository import SqlAlchemyUserRepository
from app.shared.config import get_settings
from app.shared.db.session import get_session

SESSION_COOKIE = "access_token"


def get_auth_service(session: Annotated[Session, Depends(get_session)]) -> AuthService:
    settings = get_settings()
    return AuthService(
        SqlAlchemyUserRepository(session),
        settings.jwt_secret.get_secret_value(),
        timedelta(minutes=settings.access_token_lifetime_minutes),
    )


def get_current_user(
    service: Annotated[AuthService, Depends(get_auth_service)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    return service.user_from_token(access_token)


CurrentUser = Annotated[User, Depends(get_current_user)]
