# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.db.models import LlmInvocation


class LlmInvocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        *,
        experiment_id: uuid.UUID,
        rendered_prompt: str,
        model: str,
        params: dict[str, Any],
        stage: Optional[str] = None,
        chunk_index: Optional[int] = None,
        prompt_id: Optional[uuid.UUID] = None,
        prompt_version: Optional[int] = None,
        response_text: Optional[str] = None,
        response_json: Optional[dict[str, Any]] = None,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        latency_ms: Optional[int] = None,
        gssp_correlation_id: Optional[str] = None,
        status: str = "ok",
        error_message: Optional[str] = None,
    ) -> LlmInvocation:
        inv = LlmInvocation(
            experiment_id = experiment_id,
            rendered_prompt = rendered_prompt,
            model = model,
            params = params,
            stage = stage,
            chunk_index = chunk_index,
            prompt_id = prompt_id,
            prompt_version = prompt_version,
            response_text = response_text,
            response_json = response_json,
            tokens_in = tokens_in,
            tokens_out = tokens_out,
            latency_ms = latency_ms,
            gssp_correlation_id = gssp_correlation_id,
            status = status,
            error_message = error_message,
        )
        self.session.add(inv)
        await self.session.flush()
        return inv

    async def list_for_experiment(self, experiment_id: uuid.UUID) -> list[LlmInvocation]:
        result = await self.session.execute(
            select(LlmInvocation)
            .where(LlmInvocation.experiment_id == experiment_id)
            .order_by(LlmInvocation.created_at.asc())
        )
        return list(result.scalars().all())
