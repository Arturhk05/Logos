from sqlalchemy.orm import Session

from app.modules.users.repository import SqlAlchemyUserRepository
from tests.factories import create_user


def test_get_returns_the_user(db_session: Session) -> None:
    user = create_user(db_session)

    assert SqlAlchemyUserRepository(db_session).get(user.id) is user


def test_get_returns_none_for_unknown_id(db_session: Session) -> None:
    assert SqlAlchemyUserRepository(db_session).get(999_999) is None


def test_get_by_username_returns_the_user(db_session: Session) -> None:
    user = create_user(db_session, username="motorista")

    assert SqlAlchemyUserRepository(db_session).get_by_username("motorista") is user


def test_get_by_username_returns_none_for_unknown_user(db_session: Session) -> None:
    create_user(db_session, username="motorista")

    assert SqlAlchemyUserRepository(db_session).get_by_username("ninguem") is None
