"""Alembic migrations for ScoutMonitor AI PostgreSQL databases.

Only initialize a new empty database here. Existing legacy databases must not
be stamped or migrated without a separately reviewed adoption procedure.
"""

import os
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

target_metadata = None


def build_database_url():
    explicit_url = os.getenv("SCOUTMONITOR_DATABASE_URL")
    if explicit_url:
        if not explicit_url.startswith("postgresql+psycopg://"):
            raise RuntimeError("SCOUTMONITOR_DATABASE_URL must use postgresql+psycopg.")
        return explicit_url

    fields = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [key for key in fields if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Database migration settings are missing: " + ", ".join(missing)
        )
    return URL.create(
        "postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )


def run_migrations_online() -> None:
    engine = create_engine(build_database_url(), poolclass=NullPool)
    try:
        confirmed_database = os.getenv("SCOUTMONITOR_MIGRATION_DATABASE")
        if not confirmed_database or confirmed_database != engine.url.database:
            raise RuntimeError(
                "Migration cancelled. Set SCOUTMONITOR_MIGRATION_DATABASE to the "
                "exact name of a NEW EMPTY target database before running Alembic."
            )
        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names(schema="public"))
            # Refuse existing manually created schemas before Alembic writes metadata.
            if tables and "alembic_version" not in tables:
                raise RuntimeError(
                    "Existing database tables detected. Migration cancelled. "
                    "Use a NEW EMPTY database; never upgrade or stamp the "
                    "existing ScoutMonitor AI development database without review."
                )
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                transactional_ddl=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Offline migrations are disabled for database safety.")
else:
    run_migrations_online()
