# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Prompt — versioned, DB-backed prompt templates.

Each (name, version) is unique; a recipe pins its prompt by (id, version) so
re-running a recipe later is reproducible even when the prompt evolves.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Prompt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "prompts"
    __table_args__ = (
        UniqueConstraint("name", "version", name = "uq_prompts_name_version"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable = False, index = True)
    version: Mapped[int] = mapped_column(Integer, nullable = False, default = 1)
    recipe_type: Mapped[Optional[str]] = mapped_column(String(64), nullable = True, index = True)
    template: Mapped[str] = mapped_column(String, nullable = False)
    variables: Mapped[list[str]] = mapped_column(JSONB, nullable = False, default = list)
    description: Mapped[Optional[str]] = mapped_column(String, nullable = True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable = False, default = True)
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable = True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable = False, default = dict)
