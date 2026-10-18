from collections.abc import Callable
from datetime import timedelta
from typing import Annotated

from fastapi import Cookie, Depends

from app.modules.auth.service import AuthService
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.users.repository import SqlAlchemyUserRepository
from app.shared.config import get_settings
from app.shared.db.session import SessionDep
from app.shared.errors import PermissionDeniedError

SESSION_COOKIE = "access_token"
FORBIDDEN_MESSAGE = "Você não tem permissão para realizar esta ação."


def get_auth_service(session: SessionDep) -> AuthService:
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


def require_role(role: UserRole, *roles: UserRole) -> Callable[[User], User]:
    """Dependency that lets only users with one of the given roles through."""
    allowed = {role, *roles}

    def check_role(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise PermissionDeniedError(FORBIDDEN_MESSAGE)
        return user

    return check_role
