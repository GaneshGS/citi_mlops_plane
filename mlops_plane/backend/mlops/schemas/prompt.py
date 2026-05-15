# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class PromptCreate(BaseModel):
    name: str = Field(..., min_length = 1, max_length = 128)
    template: str = Field(..., min_length = 1)
    version: int = 1
    recipe_type: Optional[str] = None
    variables: list[str] = Field(default_factory = list)
    description: Optional[str] = None
    created_by: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory = dict)


class PromptUpdate(BaseModel):
    template: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    variables: Optional[list[str]] = None


class PromptOut(BaseModel):
    id: uuid.UUID
    name: str
    version: int
    recipe_type: Optional[str]
    template: str
    variables: list[str]
    description: Optional[str]
    is_active: bool
    created_by: Optional[str]
    extra: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes = True)
