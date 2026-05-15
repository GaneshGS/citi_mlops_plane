# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Append-only stage event log for an experiment."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, UUIDPrimaryKeyMixin, utcnow


class EventLevel(str, enum.Enum):
    info = "info"
    warn = "warn"
    error = "error"


class ExperimentEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "experiment_events"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey("experiments.id", ondelete = "CASCADE"),
        nullable = False,
        index = True,
    )
    stage: Mapped[str] = mapped_column(String(64), nullable = False, index = True)
    event_type: Mapped[str] = mapped_column(String(64), nullable = False)
    level: Mapped[EventLevel] = mapped_column(
        Enum(EventLevel, name = "event_level"),
        nullable = False,
        default = EventLevel.info,
    )
    message: Mapped[Optional[str]] = mapped_column(String, nullable = True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable = False, default = dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = utcnow,
        nullable = False,
        index = True,
    )

    experiment: Mapped["Experiment"] = relationship(  # noqa: F821
        back_populates = "events"
    )
