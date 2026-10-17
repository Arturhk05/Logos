from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from testcontainers.community.postgres import PostgresContainer

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, get_session, get_session_factory
from app.main import create_app

POSTGRES_IMAGE = "postgres:18-alpine"


def _clear_cached_settings() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """HTTP client without a database, for endpoints that do not access it."""
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def database_engine() -> Iterator[Engine]:
    """Start a disposable PostgreSQL container once per test run.

    The application is pointed at it through the same settings used in production,
    so tests exercise the real connection pool and timeouts.
    """
    with PostgresContainer(POSTGRES_IMAGE, driver="psycopg") as postgres, pytest.MonkeyPatch.context() as env:
        env.setenv("ENVIRONMENT", "test")
        env.setenv("DATABASE_URL", postgres.get_connection_url())
        _clear_cached_settings()

        engine = get_engine()
        Base.metadata.create_all(engine)
        yield engine
        engine.dispose()

    _clear_cached_settings()


@pytest.fixture
def db_session(database_engine: Engine) -> Iterator[Session]:
    """Per-test isolated session: everything the test writes is rolled back at the end."""
    with database_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def db_client(db_session: Session) -> Iterator[TestClient]:
    """HTTP client whose requests use the test's isolated session."""
    app = create_app()

    def override_get_session() -> Iterator[Session]:
        with db_session.begin_nested():
            yield db_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
