# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Training history route stub.

The legacy SQLite training history store has been retired. Training run
history will be served from the MLOps Plane PostgreSQL store
(``finetune_jobs`` + ``finetune_status_snapshots``) in the next pass.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()

_DETAIL = "Training history will be served from /api/mlops/finetune/jobs in the next pass."


@router.api_route(
    "/{path:path}",
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema = False,
)
async def _gone(path: str) -> None:  # noqa: ARG001
    raise HTTPException(status_code = 503, detail = _DETAIL)
