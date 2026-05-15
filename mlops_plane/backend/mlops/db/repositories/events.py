# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.db.models import EventLevel, ExperimentEvent


class ExperimentEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        *,
        experiment_id: uuid.UUID,
        stage: str,
        event_type: str,
        message: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
        level: EventLevel = EventLevel.info,
    ) -> ExperimentEvent:
        evt = ExperimentEvent(
            experiment_id = experiment_id,
            stage = stage,
            event_type = event_type,
            level = level,
            message = message,
            payload = payload or {},
        )
        self.session.add(evt)
        await self.session.flush()
        return evt

    async def list_for_experiment(
        self,
        experiment_id: uuid.UUID,
        *,
        limit: int = 500,
    ) -> list[ExperimentEvent]:
        stmt = (
            select(ExperimentEvent)
            .where(ExperimentEvent.experiment_id == experiment_id)
            .order_by(ExperimentEvent.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
