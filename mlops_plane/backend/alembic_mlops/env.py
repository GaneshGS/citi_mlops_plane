# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Alembic env for the Citi MLOps plane.

Uses the same MLOps settings module as the runtime, so a single
``MLOPS_POSTGRES_DSN`` env var configures both.
"""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

# Make ``mlops`` importable regardless of cwd.
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from mlops.db import Base  # noqa: E402
from mlops.db import models  # noqa: F401, E402  — register tables on metadata
from mlops.config import get_settings  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Pull DSN from env (via the settings module) — never hard-code.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.db.dsn)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url = settings.db.dsn,
        target_metadata = target_metadata,
        literal_binds = True,
        dialect_opts = {"paramstyle": "named"},
        compare_type = True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection = connection,
        target_metadata = target_metadata,
        compare_type = True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix = "sqlalchemy.",
        poolclass = pool.NullPool,
        future = True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
