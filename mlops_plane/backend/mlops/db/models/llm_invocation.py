# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""LlmInvocation — every GSSP-GS call we make from a recipe run."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, UUIDPrimaryKeyMixin, utcnow


class LlmInvocation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "llm_invocations"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey("experiments.id", ondelete = "CASCADE"),
        nullable = False,
        index = True,
    )
    prompt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid = True),
        ForeignKey("prompts.id", ondelete = "SET NULL"),
        nullable = True,
    )
    prompt_version: Mapped[Optional[int]] = mapped_column(Integer, nullable = True)

    stage: Mapped[Optional[str]] = mapped_column(String(64), nullable = True, index = True)
    chunk_index: Mapped[Optional[int]] = mapped_column(Integer, nullable = True)

    rendered_prompt: Mapped[str] = mapped_column(String, nullable = False)
    model: Mapped[str] = mapped_column(String(128), nullable = False)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable = False, default = dict)

    response_text: Mapped[Optional[str]] = mapped_column(String, nullable = True)
    response_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable = True)

    tokens_in: Mapped[Optional[int]] = mapped_column(Integer, nullable = True)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer, nullable = True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable = True)

    gssp_correlation_id: Mapped[Optional[str]] = mapped_column(String(128), nullable = True)
    status: Mapped[str] = mapped_column(String(32), nullable = False, default = "ok")
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable = True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True),
        default = utcnow,
        nullable = False,
        index = True,
    )

    experiment: Mapped["Experiment"] = relationship(  # noqa: F821
        back_populates = "llm_invocations"
    )
