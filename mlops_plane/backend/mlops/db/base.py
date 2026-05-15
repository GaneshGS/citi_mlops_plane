# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""SQLAlchemy declarative base and common column types."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, MetaData, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


# Naming convention so Alembic-generated constraint names are predictable
# across environments.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Shared declarative base for all MLOps ORM models."""

    metadata = MetaData(naming_convention = NAMING_CONVENTION)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class TimestampMixin:
    """Adds created_at / updated_at to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = utcnow,
        nullable = False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = utcnow,
        onupdate = utcnow,
        nullable = False,
    )


class UUIDPrimaryKeyMixin:
    """Adds a UUID PK column named ``id``."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True),
        primary_key = True,
        default = new_uuid,
    )


__all__ = [
    "Base",
    "JSONB",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "new_uuid",
    "utcnow",
    # Re-exported so model modules don't reach into SQLAlchemy internals.
    "String",
]
