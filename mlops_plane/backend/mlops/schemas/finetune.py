# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from mlops.db.models import FinetuneStatus


class FinetuneSubmitRequest(BaseModel):
    experiment_id: uuid.UUID
    base_model: str
    train_s3_uri: str
    test_s3_uri: Optional[str] = None
    hyperparams: dict[str, Any] = Field(default_factory = dict)


class FinetuneStatusSnapshotOut(BaseModel):
    id: uuid.UUID
    status: str
    metrics: dict[str, Any]
    captured_at: datetime

    model_config = ConfigDict(from_attributes = True)


class FinetuneJobOut(BaseModel):
    id: uuid.UUID
    experiment_id: uuid.UUID
    stellar_job_id: Optional[str]
    base_model: Optional[str]
    hyperparams: dict[str, Any]
    status: FinetuneStatus
    submitted_at: Optional[datetime]
    finished_at: Optional[datetime]
    result_model_uri: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    snapshots: list[FinetuneStatusSnapshotOut] = Field(default_factory = list)

    model_config = ConfigDict(from_attributes = True)
