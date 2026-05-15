# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Model catalog stub.

A real model catalog will list models available via GSSP-GS plus any
fine-tuned models produced by Stellar. Returning 503 here so existing UI
calls fail loudly until that wiring lands.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()

_DETAIL = "Model catalog will be served from GSSP-GS / Stellar in the next pass."


@router.api_route(
    "/{path:path}",
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema = False,
)
async def _gone(path: str) -> None:  # noqa: ARG001
    raise HTTPException(status_code = 503, detail = _DETAIL)
