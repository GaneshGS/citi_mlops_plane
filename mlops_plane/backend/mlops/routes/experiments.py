# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""CRUD endpoints for experiments + their event timeline + data sources."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.db import get_db
from mlops.db.models import ExperimentStatus
from mlops.db.repositories import (
    DataSourceRepository,
    ExperimentEventRepository,
    ExperimentRepository,
    LlmInvocationRepository,
)
from mlops.schemas import (
    ExperimentCreate,
    ExperimentDataSourceOut,
    ExperimentDetail,
    ExperimentEventOut,
    ExperimentOut,
    ExperimentUpdate,
)


router = APIRouter()


@router.post("", response_model = ExperimentOut, status_code = status.HTTP_201_CREATED)
async def create_experiment(
    body: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
) -> ExperimentOut:
    repo = ExperimentRepository(db)
    exp = await repo.create(
        name = body.name,
        recipe_type = body.recipe_type,
        config = body.config,
        owner_soeid = body.owner_soeid,
        prompt_id = body.prompt_id,
    )
    return ExperimentOut.model_validate(exp)


@router.get("", response_model = list[ExperimentOut])
async def list_experiments(
    recipe_type: Optional[str] = None,
    owner_soeid: Optional[str] = None,
    status_filter: Optional[ExperimentStatus] = Query(None, alias = "status"),
    limit: int = Query(50, ge = 1, le = 200),
    offset: int = Query(0, ge = 0),
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentOut]:
    repo = ExperimentRepository(db)
    rows = await repo.list(
        recipe_type = recipe_type,
        owner_soeid = owner_soeid,
        status = status_filter,
        limit = limit,
        offset = offset,
    )
    return [ExperimentOut.model_validate(r) for r in rows]


@router.get("/{experiment_id}", response_model = ExperimentDetail)
async def get_experiment(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ExperimentDetail:
    repo = ExperimentRepository(db)
    exp = await repo.get(experiment_id)
    if exp is None:
        raise HTTPException(status_code = 404, detail = "experiment not found")

    events_repo = ExperimentEventRepository(db)
    ds_repo = DataSourceRepository(db)
    events = await events_repo.list_for_experiment(experiment_id)
    sources = await ds_repo.list_for_experiment(experiment_id)

    base = ExperimentOut.model_validate(exp).model_dump()
    return ExperimentDetail(
        **base,
        events = [ExperimentEventOut.model_validate(e) for e in events],
        data_sources = [ExperimentDataSourceOut.model_validate(s) for s in sources],
    )


@router.patch("/{experiment_id}", response_model = ExperimentOut)
async def patch_experiment(
    experiment_id: uuid.UUID,
    body: ExperimentUpdate,
    db: AsyncSession = Depends(get_db),
) -> ExperimentOut:
    repo = ExperimentRepository(db)
    exp = await repo.get(experiment_id)
    if exp is None:
        raise HTTPException(status_code = 404, detail = "experiment not found")
    await repo.patch(experiment_id, name = body.name, config = body.config)
    refreshed = await repo.get(experiment_id)
    assert refreshed is not None
    return ExperimentOut.model_validate(refreshed)


@router.delete("/{experiment_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = ExperimentRepository(db)
    exp = await repo.get(experiment_id)
    if exp is None:
        raise HTTPException(status_code = 404, detail = "experiment not found")
    await repo.soft_delete(experiment_id)


@router.get("/{experiment_id}/events", response_model = list[ExperimentEventOut])
async def list_experiment_events(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentEventOut]:
    events_repo = ExperimentEventRepository(db)
    events = await events_repo.list_for_experiment(experiment_id)
    return [ExperimentEventOut.model_validate(e) for e in events]


@router.get(
    "/{experiment_id}/data-sources",
    response_model = list[ExperimentDataSourceOut],
)
async def list_experiment_data_sources(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ExperimentDataSourceOut]:
    repo = DataSourceRepository(db)
    sources = await repo.list_for_experiment(experiment_id)
    return [ExperimentDataSourceOut.model_validate(s) for s in sources]


@router.get("/{experiment_id}/llm-invocations")
async def list_experiment_llm_invocations(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = LlmInvocationRepository(db)
    invs = await repo.list_for_experiment(experiment_id)
    return [
        {
            "id": str(i.id),
            "stage": i.stage,
            "chunk_index": i.chunk_index,
            "model": i.model,
            "tokens_in": i.tokens_in,
            "tokens_out": i.tokens_out,
            "latency_ms": i.latency_ms,
            "status": i.status,
            "gssp_correlation_id": i.gssp_correlation_id,
            "rendered_prompt": i.rendered_prompt,
            "response_text": i.response_text,
            "created_at": i.created_at.isoformat(),
        }
        for i in invs
    ]
