# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from mlops.db.models import EventLevel, ExperimentStatus


class ExperimentBase(BaseModel):
    name: str = Field(..., min_length = 1, max_length = 255)
    recipe_type: str = Field(..., min_length = 1, max_length = 64)
    config: dict[str, Any] = Field(default_factory = dict)
    owner_soeid: Optional[str] = None


class ExperimentCreate(ExperimentBase):
    prompt_id: Optional[uuid.UUID] = None


class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict[str, Any]] = None


class ExperimentOut(ExperimentBase):
    id: uuid.UUID
    status: ExperimentStatus
    current_stage: Optional[str]
    prompt_id: Optional[uuid.UUID]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes = True)


class ExperimentEventOut(BaseModel):
    id: uuid.UUID
    experiment_id: uuid.UUID
    stage: str
    event_type: str
    level: EventLevel
    message: Optional[str]
    payload: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes = True)


class ExperimentDataSourceOut(BaseModel):
    id: uuid.UUID
    role: str
    s3_bucket: str
    s3_key: str
    byte_count: Optional[int]
    content_type: Optional[str]
    registered_at: datetime

    model_config = ConfigDict(from_attributes = True)


class ExperimentDetail(ExperimentOut):
    events: list[ExperimentEventOut] = Field(default_factory = list)
    data_sources: list[ExperimentDataSourceOut] = Field(default_factory = list)
