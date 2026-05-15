# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""FinetuneStatusSnapshot — one row per status poll against Stellar."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, UUIDPrimaryKeyMixin, utcnow


class FinetuneStatusSnapshot(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "finetune_status_snapshots"

    finetune_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey("finetune_jobs.id", ondelete = "CASCADE"),
        nullable = False,
        index = True,
    )
    status: Mapped[str] = mapped_column(String(64), nullable = False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable = False, default = dict)
    raw_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable = True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = utcnow,
        nullable = False,
        index = True,
    )

    finetune_job: Mapped["FinetuneJob"] = relationship(  # noqa: F821
        back_populates = "status_snapshots"
    )
