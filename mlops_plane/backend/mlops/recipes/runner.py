# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Top-level recipe runner.

Builds a ``RecipeContext`` from the request, mints / loads the experiment,
hands off to the recipe, and traps unexpected exceptions so the experiment
row always reflects the final state.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Optional

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from mlops.db import async_session_factory
from mlops.db.models import EventLevel, ExperimentStatus
from mlops.db.repositories import (
    ExperimentEventRepository,
    ExperimentRepository,
    PromptRepository,
)
from mlops.integrations import get_gssp_client, get_s3_client, get_stellar_client
from mlops.recipes.base import RecipeContext
from mlops.recipes.registry import get_recipe


log = logging.getLogger("mlops.recipes.runner")


async def run_recipe(
    *,
    experiment_id: uuid.UUID,
    recipe_id: str,
    name: str,
    fields: dict[str, Any],
    prompt_text: str,
    prompt_id: Optional[uuid.UUID],
    owner_soeid: Optional[str],
) -> dict[str, Any]:
    """Run the recipe end-to-end. Intended to be scheduled as a background task."""
    recipe = get_recipe(recipe_id)
    if recipe is None:
        await _mark_failed(experiment_id, f"unknown recipe_id: {recipe_id}")
        return {"status": "failed", "reason": "unknown_recipe"}

    session_factory: async_sessionmaker[AsyncSession] = async_session_factory()

    # Resolve prompt template (if a saved prompt was selected, use its template).
    prompt_template_text: Optional[str] = None
    prompt_version: Optional[int] = None
    if prompt_id is not None:
        async with session_factory() as session:
            prompt = await PromptRepository(session).get(prompt_id)
            if prompt is not None:
                prompt_template_text = prompt.template
                prompt_version = prompt.version

    ctx = RecipeContext(
        experiment_id = experiment_id,
        name = name,
        fields = fields,
        prompt_text = prompt_text,
        prompt_id = prompt_id,
        prompt_template = prompt_template_text,
        prompt_version = prompt_version,
        owner_soeid = owner_soeid,
        session_factory = session_factory,
        gssp = get_gssp_client(),
        s3 = get_s3_client(),
        stellar = get_stellar_client(),
    )

    try:
        result = await recipe.run(ctx)
        return result
    except Exception as exc:  # noqa: BLE001
        log.exception("recipe %s failed for experiment %s", recipe_id, experiment_id)
        await _mark_failed(experiment_id, f"{type(exc).__name__}: {exc}")
        return {"status": "failed", "reason": "exception", "error": str(exc)}


async def _mark_failed(experiment_id: uuid.UUID, reason: str) -> None:
    factory = async_session_factory()
    async with factory() as session:
        await ExperimentRepository(session).update_status(
            experiment_id,
            status = ExperimentStatus.failed,
            error_message = reason,
        )
        await ExperimentEventRepository(session).add(
            experiment_id = experiment_id,
            stage = "failure",
            event_type = "experiment.failed",
            level = EventLevel.error,
            message = reason,
        )
        await session.commit()


def schedule_recipe_run(coro) -> None:
    """Helper to fire-and-forget a recipe coroutine on the running loop."""
    asyncio.create_task(coro)
