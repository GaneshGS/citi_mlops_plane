# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""FinetuneJob — Stellar fine-tune submission record."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class FinetuneStatus(str, enum.Enum):
    pending = "pending"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class FinetuneJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "finetune_jobs"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey("experiments.id", ondelete = "CASCADE"),
        nullable = False,
        index = True,
    )
    stellar_job_id: Mapped[Optional[str]] = mapped_column(String(255), nullable = True, index = True)
    train_stellar_dataset_id: Mapped[Optional[str]] = mapped_column(String(255), nullable = True)
    test_stellar_dataset_id: Mapped[Optional[str]] = mapped_column(String(255), nullable = True)
    base_model: Mapped[Optional[str]] = mapped_column(String(255), nullable = True)
    hyperparams: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable = False, default = dict)
    status: Mapped[FinetuneStatus] = mapped_column(
        Enum(FinetuneStatus, name = "finetune_status"),
        nullable = False,
        default = FinetuneStatus.pending,
        index = True,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone = True), nullable = True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone = True), nullable = True
    )
    result_model_uri: Mapped[Optional[str]] = mapped_column(String, nullable = True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable = True)

    experiment: Mapped["Experiment"] = relationship(  # noqa: F821
        back_populates = "finetune_jobs"
    )
    status_snapshots: Mapped[list["FinetuneStatusSnapshot"]] = relationship(  # noqa: F821
        back_populates = "finetune_job",
        cascade = "all, delete-orphan",
        order_by = "FinetuneStatusSnapshot.captured_at",
    )
