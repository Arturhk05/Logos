"""Create the demo users shown on the login screen. Safe to run on every deploy: existing users are kept."""

from sqlalchemy.orm import Session

from app.modules.auth.security import hash_password
from app.modules.users.enums import UserRole
from app.modules.users.models import User
from app.modules.users.repository import SqlAlchemyUserRepository
from app.shared.db.session import get_session_factory

DEMO_PASSWORD = "logos123"  # noqa: S105 (public demo credential, shown on the login screen)

DEMO_USERS: tuple[tuple[str, UserRole], ...] = (
    ("camila", UserRole.ANALYST),
    ("lucas", UserRole.ANALYST),
    ("roberto", UserRole.SUPERVISOR),
    ("jose", UserRole.DRIVER),
)


def seed_users(session: Session) -> int:
    """Create the demo users that do not exist yet and return how many were created."""
    users = SqlAlchemyUserRepository(session)
    missing = [(username, role) for username, role in DEMO_USERS if users.get_by_username(username) is None]
    for username, role in missing:
        session.add(User(username=username, password_hash=hash_password(DEMO_PASSWORD), role=role))
    session.flush()
    return len(missing)


def main() -> None:
    with get_session_factory().begin() as session:
        created = seed_users(session)
    print(f"Demo users created: {created}")


if __name__ == "__main__":
    main()
