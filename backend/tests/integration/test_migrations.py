from alembic import command
from alembic.config import Config
from sqlalchemy import Engine


def test_migrations_are_in_sync_with_models(alembic_config: Config, database_engine: Engine) -> None:
    command.check(alembic_config)
