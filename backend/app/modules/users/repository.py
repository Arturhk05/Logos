from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.models import User


class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None:
        """Return the user with this id, or None if it does not exist."""
        ...

    def get_by_username(self, username: str) -> User | None:
        """Return the user with exactly this username, or None. Usernames are stored lowercase, so callers normalize first."""
        ...


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self._session.scalars(select(User).where(User.username == username)).one_or_none()
