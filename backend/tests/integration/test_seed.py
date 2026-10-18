from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.security import verify_password
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from scripts.seed import seed_users

EXPECTED_USERS = {
    "camila": UserRole.ANALYST,
    "lucas": UserRole.ANALYST,
    "roberto": UserRole.SUPERVISOR,
    "jose": UserRole.DRIVER,
}


def _users(session: Session) -> list[User]:
    return list(session.scalars(select(User).where(User.username.in_(EXPECTED_USERS))))


def test_seed_creates_one_login_per_demo_user(db_session: Session) -> None:
    seed_users(db_session)

    users = _users(db_session)
    assert {user.username: user.role for user in users} == EXPECTED_USERS
    assert all(verify_password("logos123", user.password_hash) for user in users)


def test_seed_usernames_are_normalized(db_session: Session) -> None:
    seed_users(db_session)

    usernames = db_session.scalars(select(User.username))
    assert all(username == username.strip().lower() for username in usernames)


def test_seed_can_run_twice(db_session: Session) -> None:
    assert seed_users(db_session) == 4
    assert seed_users(db_session) == 0

    assert len(_users(db_session)) == len(EXPECTED_USERS)
