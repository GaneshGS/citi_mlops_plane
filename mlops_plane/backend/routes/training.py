# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Training route stub.

The legacy local-GPU training pipeline has been removed. Real fine-tuning
runs through Stellar — see ``mlops.routes.finetune``. The endpoints here
remain so the existing Training Monitor UI keeps loading; they will be
rewired to read from the MLOps Plane PostgreSQL store (``finetune_jobs``
and ``finetune_status_snapshots``) in the next pass.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()

_DETAIL = (
    "Local training has been retired. Fine-tuning runs go through Stellar; "
    "see POST /api/mlops/finetune/submit."
)


@router.api_route(
    "/{path:path}",
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema = False,
)
async def _gone(path: str) -> None:  # noqa: ARG001
    raise HTTPException(status_code = 503, detail = _DETAIL)
