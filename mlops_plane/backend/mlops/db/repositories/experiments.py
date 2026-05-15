# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""CRUD repository for Experiment + soft delete."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mlops.db.models import Experiment, ExperimentStatus


class ExperimentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        name: str,
        recipe_type: str,
        config: dict[str, Any],
        owner_soeid: Optional[str] = None,
        prompt_id: Optional[uuid.UUID] = None,
    ) -> Experiment:
        exp = Experiment(
            name = name,
            recipe_type = recipe_type,
            config = config,
            owner_soeid = owner_soeid,
            prompt_id = prompt_id,
        )
        self.session.add(exp)
        await self.session.flush()
        await self.session.refresh(exp)
        return exp

    async def get(self, experiment_id: uuid.UUID, *, with_events: bool = False) -> Optional[Experiment]:
        stmt = select(Experiment).where(
            Experiment.id == experiment_id,
            Experiment.is_deleted.is_(False),
        )
        if with_events:
            stmt = stmt.options(selectinload(Experiment.events))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        recipe_type: Optional[str] = None,
        owner_soeid: Optional[str] = None,
        status: Optional[ExperimentStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Experiment]:
        stmt = (
            select(Experiment)
            .where(Experiment.is_deleted.is_(False))
            .order_by(Experiment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if recipe_type:
            stmt = stmt.where(Experiment.recipe_type == recipe_type)
        if owner_soeid:
            stmt = stmt.where(Experiment.owner_soeid == owner_soeid)
        if status is not None:
            stmt = stmt.where(Experiment.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        experiment_id: uuid.UUID,
        *,
        status: ExperimentStatus,
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        values: dict[str, Any] = {"status": status}
        if current_stage is not None:
            values["current_stage"] = current_stage
        if error_message is not None:
            values["error_message"] = error_message
        await self.session.execute(
            update(Experiment).where(Experiment.id == experiment_id).values(**values)
        )

    async def patch(
        self,
        experiment_id: uuid.UUID,
        *,
        name: Optional[str] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> None:
        values: dict[str, Any] = {}
        if name is not None:
            values["name"] = name
        if config is not None:
            values["config"] = config
        if not values:
            return
        await self.session.execute(
            update(Experiment).where(Experiment.id == experiment_id).values(**values)
        )

    async def soft_delete(self, experiment_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Experiment)
            .where(Experiment.id == experiment_id)
            .values(is_deleted = True)
        )
