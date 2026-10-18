from sqlalchemy import text
from sqlalchemy.orm import Session


def test_connects_to_postgresql_18(db_session: Session) -> None:
    version = db_session.execute(text("select version()")).scalar_one()

    assert version.startswith("PostgreSQL 18")


def test_statement_timeout_is_applied_to_connections(db_session: Session) -> None:
    timeout = db_session.execute(text("show statement_timeout")).scalar_one()

    assert timeout == "5s"


def test_connections_use_utc(db_session: Session) -> None:
    timezone = db_session.execute(text("show timezone")).scalar_one()

    assert timezone == "UTC"
