# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Experiment — the top-level transactional thread."""

from __future__ import annotations

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ExperimentStatus(str, enum.Enum):
    """Lifecycle states for an experiment."""

    pending = "pending"
    loading_data = "loading_data"
    preparing_dataset = "preparing_dataset"
    registering_dataset = "registering_dataset"
    submitted_finetune = "submitted_finetune"
    training = "training"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Experiment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(255), nullable = False)
    recipe_type: Mapped[str] = mapped_column(String(64), nullable = False, index = True)
    owner_soeid: Mapped[Optional[str]] = mapped_column(String(64), nullable = True)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus, name = "experiment_status"),
        nullable = False,
        default = ExperimentStatus.pending,
        index = True,
    )
    current_stage: Mapped[Optional[str]] = mapped_column(String(64), nullable = True)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable = False, default = dict)
    prompt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey("prompts.id", ondelete = "SET NULL"),
        nullable = True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable = True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable = False, default = False)

    # Relationships
    events: Mapped[list["ExperimentEvent"]] = relationship(  # noqa: F821
        back_populates = "experiment",
        cascade = "all, delete-orphan",
        order_by = "ExperimentEvent.created_at",
    )
    data_sources: Mapped[list["DataSource"]] = relationship(  # noqa: F821
        back_populates = "experiment",
        cascade = "all, delete-orphan",
    )
    llm_invocations: Mapped[list["LlmInvocation"]] = relationship(  # noqa: F821
        back_populates = "experiment",
        cascade = "all, delete-orphan",
    )
    stellar_datasets: Mapped[list["StellarDataset"]] = relationship(  # noqa: F821
        back_populates = "experiment",
        cascade = "all, delete-orphan",
    )
    finetune_jobs: Mapped[list["FinetuneJob"]] = relationship(  # noqa: F821
        back_populates = "experiment",
        cascade = "all, delete-orphan",
    )
