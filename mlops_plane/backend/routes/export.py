# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Export route stub.

Local model export (GGUF, etc.) has been retired. Fine-tuned model
artifacts are produced by Stellar and addressed by their Stellar URIs.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()

_DETAIL = "Model artifacts are produced by Stellar; local export has been retired."


@router.api_route(
    "/{path:path}",
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema = False,
)
async def _gone(path: str) -> None:  # noqa: ARG001
    raise HTTPException(status_code = 503, detail = _DETAIL)
