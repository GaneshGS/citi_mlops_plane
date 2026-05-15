# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""StellarDataset — dataset registration record returned by Stellar."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, UUIDPrimaryKeyMixin, utcnow


class StellarDatasetRole(str, enum.Enum):
    train = "train"
    test = "test"
    validation = "validation"


class StellarDataset(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "stellar_datasets"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey("experiments.id", ondelete = "CASCADE"),
        nullable = False,
        index = True,
    )
    role: Mapped[StellarDatasetRole] = mapped_column(
        Enum(StellarDatasetRole, name = "stellar_dataset_role"),
        nullable = False,
    )
    stellar_dataset_id: Mapped[str] = mapped_column(String(255), nullable = False, index = True)
    source_s3_uri: Mapped[Optional[str]] = mapped_column(String, nullable = True)
    byte_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable = True)
    row_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable = True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable = False, default = dict)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = utcnow,
        nullable = False,
    )

    experiment: Mapped["Experiment"] = relationship(  # noqa: F821
        back_populates = "stellar_datasets"
    )
