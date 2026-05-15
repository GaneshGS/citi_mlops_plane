# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""CRUD for versioned prompts."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.db import get_db
from mlops.db.repositories import PromptRepository
from mlops.schemas import PromptCreate, PromptOut, PromptUpdate


router = APIRouter()


@router.post("", response_model = PromptOut, status_code = status.HTTP_201_CREATED)
async def create_prompt(
    body: PromptCreate,
    db: AsyncSession = Depends(get_db),
) -> PromptOut:
    repo = PromptRepository(db)
    prompt = await repo.create(
        name = body.name,
        template = body.template,
        version = body.version,
        recipe_type = body.recipe_type,
        variables = body.variables,
        description = body.description,
        created_by = body.created_by,
        extra = body.extra,
    )
    return PromptOut.model_validate(prompt)


@router.get("", response_model = list[PromptOut])
async def list_prompts(
    recipe_type: Optional[str] = None,
    only_active: bool = True,
    limit: int = Query(100, ge = 1, le = 500),
    offset: int = Query(0, ge = 0),
    db: AsyncSession = Depends(get_db),
) -> list[PromptOut]:
    repo = PromptRepository(db)
    rows = await repo.list(
        recipe_type = recipe_type,
        only_active = only_active,
        limit = limit,
        offset = offset,
    )
    return [PromptOut.model_validate(r) for r in rows]


@router.get("/{prompt_id}", response_model = PromptOut)
async def get_prompt(
    prompt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PromptOut:
    repo = PromptRepository(db)
    prompt = await repo.get(prompt_id)
    if prompt is None:
        raise HTTPException(status_code = 404, detail = "prompt not found")
    return PromptOut.model_validate(prompt)


@router.patch("/{prompt_id}", response_model = PromptOut)
async def patch_prompt(
    prompt_id: uuid.UUID,
    body: PromptUpdate,
    db: AsyncSession = Depends(get_db),
) -> PromptOut:
    repo = PromptRepository(db)
    prompt = await repo.get(prompt_id)
    if prompt is None:
        raise HTTPException(status_code = 404, detail = "prompt not found")
    await repo.patch(
        prompt_id,
        template = body.template,
        description = body.description,
        is_active = body.is_active,
        variables = body.variables,
    )
    refreshed = await repo.get(prompt_id)
    assert refreshed is not None
    return PromptOut.model_validate(refreshed)


@router.delete("/{prompt_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = PromptRepository(db)
    prompt = await repo.get(prompt_id)
    if prompt is None:
        raise HTTPException(status_code = 404, detail = "prompt not found")
    await repo.delete(prompt_id)
