"""Alembic environment for real_estate_db (schema-of-record)."""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

import real_estate_svc.models  # noqa: F401  (register tables on Base.metadata)
from persistence import Base

config = context.config
_url = os.environ.get("DATABASE_URL")
if _url:
    # Alembic runs migrations synchronously; use a sync driver.
    config.set_main_option("sqlalchemy.url", _url.replace("+asyncpg", "+psycopg"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
