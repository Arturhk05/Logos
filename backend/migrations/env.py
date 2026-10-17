import logging

from alembic import context
from sqlalchemy import create_engine, pool

import app.models  # noqa: F401  # registers every model on Base.metadata for autogenerate
from app.core.config import get_settings
from app.db.base import Base

logging.basicConfig(level=logging.INFO, format="%(levelname)-5.5s [%(name)s] %(message)s")

target_metadata = Base.metadata
database_url = str(get_settings().database_url)


def run_migrations_offline() -> None:
    """Render migrations as SQL scripts without connecting to the database."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations directly to the database."""
    engine = create_engine(database_url, poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
