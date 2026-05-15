# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.db.models import StellarDataset, StellarDatasetRole


class StellarDatasetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        *,
        experiment_id: uuid.UUID,
        role: StellarDatasetRole,
        stellar_dataset_id: str,
        source_s3_uri: Optional[str] = None,
        byte_count: Optional[int] = None,
        row_count: Optional[int] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> StellarDataset:
        ds = StellarDataset(
            experiment_id = experiment_id,
            role = role,
            stellar_dataset_id = stellar_dataset_id,
            source_s3_uri = source_s3_uri,
            byte_count = byte_count,
            row_count = row_count,
            extra = extra or {},
        )
        self.session.add(ds)
        await self.session.flush()
        return ds

    async def list_for_experiment(self, experiment_id: uuid.UUID) -> list[StellarDataset]:
        result = await self.session.execute(
            select(StellarDataset)
            .where(StellarDataset.experiment_id == experiment_id)
            .order_by(StellarDataset.registered_at.asc())
        )
        return list(result.scalars().all())
