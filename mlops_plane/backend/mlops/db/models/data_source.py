# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""DataSource — every S3 object touched by an experiment."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, UUIDPrimaryKeyMixin, utcnow


class DataSourceRole(str, enum.Enum):
    """What the S3 object represents in the pipeline."""
    input = "input"
    chunked = "chunked"
    train = "train"
    test = "test"
    output = "output"
    artifact = "artifact"


class DataSource(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "data_sources"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey("experiments.id", ondelete = "CASCADE"),
        nullable = False,
        index = True,
    )
    role: Mapped[DataSourceRole] = mapped_column(
        Enum(DataSourceRole, name = "data_source_role"),
        nullable = False,
        index = True,
    )
    s3_bucket: Mapped[str] = mapped_column(String(255), nullable = False)
    s3_key: Mapped[str] = mapped_column(String, nullable = False)
    byte_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable = True)
    etag: Mapped[Optional[str]] = mapped_column(String(128), nullable = True)
    content_type: Mapped[Optional[str]] = mapped_column(String(128), nullable = True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = utcnow,
        nullable = False,
    )

    experiment: Mapped["Experiment"] = relationship(  # noqa: F821
        back_populates = "data_sources"
    )

    @property
    def s3_uri(self) -> str:
        return f"s3://{self.s3_bucket}/{self.s3_key}"
