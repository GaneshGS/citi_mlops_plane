# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.db.models import DataSource, DataSourceRole


class DataSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        *,
        experiment_id: uuid.UUID,
        role: DataSourceRole,
        s3_bucket: str,
        s3_key: str,
        byte_count: Optional[int] = None,
        etag: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> DataSource:
        ds = DataSource(
            experiment_id = experiment_id,
            role = role,
            s3_bucket = s3_bucket,
            s3_key = s3_key,
            byte_count = byte_count,
            etag = etag,
            content_type = content_type,
        )
        self.session.add(ds)
        await self.session.flush()
        return ds

    async def list_for_experiment(self, experiment_id: uuid.UUID) -> list[DataSource]:
        result = await self.session.execute(
            select(DataSource)
            .where(DataSource.experiment_id == experiment_id)
            .order_by(DataSource.registered_at.asc())
        )
        return list(result.scalars().all())
