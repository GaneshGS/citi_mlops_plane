# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Fine-tune submission + status — routed through Stellar."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.db import get_db
from mlops.db.models import (
    DataSourceRole,
    ExperimentStatus,
    FinetuneStatus,
    StellarDatasetRole,
)
from mlops.db.repositories import (
    DataSourceRepository,
    ExperimentEventRepository,
    ExperimentRepository,
    FinetuneJobRepository,
    FinetuneStatusSnapshotRepository,
    StellarDatasetRepository,
)
from mlops.integrations import get_stellar_client
from mlops.integrations.s3_client import parse_s3_uri
from mlops.schemas import (
    FinetuneJobOut,
    FinetuneStatusSnapshotOut,
    FinetuneSubmitRequest,
)


router = APIRouter()


@router.post("/submit", response_model = FinetuneJobOut)
async def submit_finetune(
    body: FinetuneSubmitRequest,
    db: AsyncSession = Depends(get_db),
) -> FinetuneJobOut:
    exp = await ExperimentRepository(db).get(body.experiment_id)
    if exp is None:
        raise HTTPException(status_code = 404, detail = "experiment not found")

    stellar = get_stellar_client()

    # Register train + test with Stellar.
    train_reg = await stellar.register_dataset(
        s3_uri = body.train_s3_uri,
        role = "train",
        experiment_id = str(body.experiment_id),
    )
    await StellarDatasetRepository(db).add(
        experiment_id = body.experiment_id,
        role = StellarDatasetRole.train,
        stellar_dataset_id = train_reg.stellar_dataset_id,
        source_s3_uri = body.train_s3_uri,
    )

    test_dataset_id: str | None = None
    if body.test_s3_uri:
        test_reg = await stellar.register_dataset(
            s3_uri = body.test_s3_uri,
            role = "test",
            experiment_id = str(body.experiment_id),
        )
        await StellarDatasetRepository(db).add(
            experiment_id = body.experiment_id,
            role = StellarDatasetRole.test,
            stellar_dataset_id = test_reg.stellar_dataset_id,
            source_s3_uri = body.test_s3_uri,
        )
        test_dataset_id = test_reg.stellar_dataset_id

    # Create the local FT job row.
    job_repo = FinetuneJobRepository(db)
    job = await job_repo.create(
        experiment_id = body.experiment_id,
        base_model = body.base_model,
        hyperparams = body.hyperparams,
        train_stellar_dataset_id = train_reg.stellar_dataset_id,
        test_stellar_dataset_id = test_dataset_id,
    )

    # Submit to Stellar.
    submission = await stellar.submit_finetune(
        experiment_id = str(body.experiment_id),
        train_dataset_id = train_reg.stellar_dataset_id,
        test_dataset_id = test_dataset_id,
        base_model = body.base_model,
        hyperparams = body.hyperparams,
    )
    submitted_at = _parse_iso(submission.submitted_at_iso) or datetime.utcnow()
    await job_repo.mark_submitted(
        job.id,
        stellar_job_id = submission.stellar_job_id,
        submitted_at = submitted_at,
    )

    await ExperimentRepository(db).update_status(
        body.experiment_id,
        status = ExperimentStatus.submitted_finetune,
        current_stage = "submitting_finetune",
    )
    await ExperimentEventRepository(db).add(
        experiment_id = body.experiment_id,
        stage = "submitting_finetune",
        event_type = "stage.completed",
        message = f"Stellar job {submission.stellar_job_id} submitted",
        payload = {
            "stellar_job_id": submission.stellar_job_id,
            "train_stellar_dataset_id": train_reg.stellar_dataset_id,
            "test_stellar_dataset_id": test_dataset_id,
            "base_model": body.base_model,
        },
    )

    refreshed = await job_repo.get(job.id, with_snapshots = True)
    assert refreshed is not None
    return FinetuneJobOut.model_validate(refreshed)


@router.post("/jobs/{job_id}/poll", response_model = FinetuneStatusSnapshotOut)
async def poll_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FinetuneStatusSnapshotOut:
    job_repo = FinetuneJobRepository(db)
    job = await job_repo.get(job_id)
    if job is None or job.stellar_job_id is None:
        raise HTTPException(status_code = 404, detail = "finetune job not found")

    stellar = get_stellar_client()
    status_obj = await stellar.get_status(job.stellar_job_id)

    snap = await FinetuneStatusSnapshotRepository(db).add(
        finetune_job_id = job.id,
        status = status_obj.status,
        metrics = status_obj.metrics,
        raw_payload = status_obj.raw,
    )

    # Map Stellar status onto our enum where we can.
    mapped: FinetuneStatus | None = _map_status(status_obj.status)
    if mapped is not None:
        await job_repo.update_status(
            job.id,
            status = mapped,
            result_model_uri = status_obj.result_model_uri,
            finished_at = datetime.utcnow() if mapped in (
                FinetuneStatus.succeeded,
                FinetuneStatus.failed,
                FinetuneStatus.cancelled,
            ) else None,
        )

    return FinetuneStatusSnapshotOut.model_validate(snap)


@router.get("/jobs/{job_id}", response_model = FinetuneJobOut)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FinetuneJobOut:
    job = await FinetuneJobRepository(db).get(job_id, with_snapshots = True)
    if job is None:
        raise HTTPException(status_code = 404, detail = "finetune job not found")
    return FinetuneJobOut.model_validate(job)


@router.get(
    "/experiments/{experiment_id}/jobs",
    response_model = list[FinetuneJobOut],
)
async def list_jobs_for_experiment(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FinetuneJobOut]:
    rows = await FinetuneJobRepository(db).list_for_experiment(experiment_id)
    return [FinetuneJobOut.model_validate(r) for r in rows]


def _map_status(stellar_status: str) -> FinetuneStatus | None:
    s = (stellar_status or "").lower()
    table: dict[str, FinetuneStatus] = {
        "pending": FinetuneStatus.pending,
        "queued": FinetuneStatus.queued,
        "running": FinetuneStatus.running,
        "in_progress": FinetuneStatus.running,
        "succeeded": FinetuneStatus.succeeded,
        "success": FinetuneStatus.succeeded,
        "completed": FinetuneStatus.succeeded,
        "failed": FinetuneStatus.failed,
        "error": FinetuneStatus.failed,
        "cancelled": FinetuneStatus.cancelled,
        "canceled": FinetuneStatus.cancelled,
    }
    return table.get(s)


def _parse_iso(iso: str) -> datetime | None:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


# Silence unused-import lint — kept in case future endpoints need them.
_ = (DataSourceRepository, DataSourceRole, parse_s3_uri)
