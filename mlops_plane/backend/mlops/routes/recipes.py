# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Recipe template gallery + run endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.db import get_db
from mlops.db.repositories import (
    ExperimentEventRepository,
    ExperimentRepository,
)
from mlops.recipes import get_recipe, list_recipe_templates, run_recipe
from mlops.schemas import (
    RecipeRunRequest,
    RecipeRunResponse,
    RecipeTemplate,
)


router = APIRouter()


@router.get("", response_model = list[RecipeTemplate])
async def list_templates() -> list[RecipeTemplate]:
    return list_recipe_templates()


@router.get("/{recipe_id}", response_model = RecipeTemplate)
async def get_template(recipe_id: str) -> RecipeTemplate:
    recipe = get_recipe(recipe_id)
    if recipe is None:
        raise HTTPException(status_code = 404, detail = "recipe not found")
    return recipe.template


@router.post(
    "/{recipe_id}/run",
    response_model = RecipeRunResponse,
    status_code = status.HTTP_202_ACCEPTED,
)
async def run_recipe_endpoint(
    recipe_id: str,
    body: RecipeRunRequest,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> RecipeRunResponse:
    recipe = get_recipe(recipe_id)
    if recipe is None:
        raise HTTPException(status_code = 404, detail = "recipe not found")

    # Validate required fields up-front so the user sees the problem before
    # the experiment is even created.
    for field in recipe.template.fields:
        if field.required and not body.fields.get(field.key):
            raise HTTPException(
                status_code = 400,
                detail = f"missing required field: {field.key}",
            )

    repo = ExperimentRepository(db)
    exp = await repo.create(
        name = body.name,
        recipe_type = recipe_id,
        config = {
            "fields": body.fields,
            "prompt_text": body.prompt_text,
            "prompt_id": str(body.prompt_id) if body.prompt_id else None,
        },
        owner_soeid = body.owner_soeid,
        prompt_id = body.prompt_id,
    )
    await ExperimentEventRepository(db).add(
        experiment_id = exp.id,
        stage = "submitted",
        event_type = "experiment.submitted",
        message = "Recipe run accepted",
        payload = {"recipe_id": recipe_id, "fields": body.fields},
    )

    # FastAPI BackgroundTasks fires after response is sent.
    background.add_task(
        _kickoff,
        experiment_id = exp.id,
        recipe_id = recipe_id,
        name = body.name,
        fields = body.fields,
        prompt_text = body.prompt_text,
        prompt_id = body.prompt_id,
        owner_soeid = body.owner_soeid,
    )

    return RecipeRunResponse(
        experiment_id = exp.id,
        status = exp.status.value,
        detail_url = f"/api/mlops/experiments/{exp.id}",
    )


async def _kickoff(
    *,
    experiment_id: uuid.UUID,
    recipe_id: str,
    name: str,
    fields: dict,
    prompt_text: str,
    prompt_id: uuid.UUID | None,
    owner_soeid: str | None,
) -> None:
    await run_recipe(
        experiment_id = experiment_id,
        recipe_id = recipe_id,
        name = name,
        fields = fields,
        prompt_text = prompt_text,
        prompt_id = prompt_id,
        owner_soeid = owner_soeid,
    )
