# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mlops.db.models import FinetuneJob, FinetuneStatus, FinetuneStatusSnapshot


class FinetuneJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        experiment_id: uuid.UUID,
        base_model: Optional[str],
        hyperparams: dict[str, Any],
        train_stellar_dataset_id: Optional[str] = None,
        test_stellar_dataset_id: Optional[str] = None,
    ) -> FinetuneJob:
        job = FinetuneJob(
            experiment_id = experiment_id,
            base_model = base_model,
            hyperparams = hyperparams,
            train_stellar_dataset_id = train_stellar_dataset_id,
            test_stellar_dataset_id = test_stellar_dataset_id,
        )
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def mark_submitted(
        self,
        job_id: uuid.UUID,
        *,
        stellar_job_id: str,
        submitted_at: datetime,
    ) -> None:
        await self.session.execute(
            update(FinetuneJob)
            .where(FinetuneJob.id == job_id)
            .values(
                stellar_job_id = stellar_job_id,
                submitted_at = submitted_at,
                status = FinetuneStatus.queued,
            )
        )

    async def get(self, job_id: uuid.UUID, *, with_snapshots: bool = False) -> Optional[FinetuneJob]:
        stmt = select(FinetuneJob).where(FinetuneJob.id == job_id)
        if with_snapshots:
            stmt = stmt.options(selectinload(FinetuneJob.status_snapshots))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_experiment(self, experiment_id: uuid.UUID) -> list[FinetuneJob]:
        result = await self.session.execute(
            select(FinetuneJob)
            .where(FinetuneJob.experiment_id == experiment_id)
            .order_by(FinetuneJob.created_at.asc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        job_id: uuid.UUID,
        *,
        status: FinetuneStatus,
        result_model_uri: Optional[str] = None,
        finished_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ) -> None:
        values: dict[str, Any] = {"status": status}
        if result_model_uri is not None:
            values["result_model_uri"] = result_model_uri
        if finished_at is not None:
            values["finished_at"] = finished_at
        if error_message is not None:
            values["error_message"] = error_message
        await self.session.execute(
            update(FinetuneJob).where(FinetuneJob.id == job_id).values(**values)
        )


class FinetuneStatusSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        *,
        finetune_job_id: uuid.UUID,
        status: str,
        metrics: dict[str, Any],
        raw_payload: Optional[dict[str, Any]] = None,
    ) -> FinetuneStatusSnapshot:
        snap = FinetuneStatusSnapshot(
            finetune_job_id = finetune_job_id,
            status = status,
            metrics = metrics,
            raw_payload = raw_payload,
        )
        self.session.add(snap)
        await self.session.flush()
        return snap

    async def list_for_job(self, finetune_job_id: uuid.UUID) -> list[FinetuneStatusSnapshot]:
        result = await self.session.execute(
            select(FinetuneStatusSnapshot)
            .where(FinetuneStatusSnapshot.finetune_job_id == finetune_job_id)
            .order_by(FinetuneStatusSnapshot.captured_at.asc())
        )
        return list(result.scalars().all())
