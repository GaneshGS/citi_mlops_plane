# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Datasets route stub.

Local dataset orchestration has been retired. Dataset management is now
performed end-to-end through the MLOps Plane (S3 ingest → GSSP-GS labelling
→ Stellar dataset registration) — see ``mlops.routes.recipes`` and
``mlops.routes.finetune``.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()

_DETAIL = "Datasets are managed end-to-end via /api/mlops/recipes and Stellar."


@router.api_route(
    "/{path:path}",
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema = False,
)
async def _gone(path: str) -> None:  # noqa: ARG001
    raise HTTPException(status_code = 503, detail = _DETAIL)
