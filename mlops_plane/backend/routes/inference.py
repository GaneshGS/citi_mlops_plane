# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Inference route stub.

Local model inference has been retired. The Chat and Compare Models pages
will be rewired to route their completions through GSSP-GS in the next
pass — see ``mlops.integrations.gssp_client``.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()

_DETAIL = (
    "Local inference has been retired. Chat / Compare Models will route "
    "through GSSP-GS in the next pass."
)


@router.api_route(
    "/{path:path}",
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema = False,
)
async def _gone(path: str) -> None:  # noqa: ARG001
    raise HTTPException(status_code = 503, detail = _DETAIL)
