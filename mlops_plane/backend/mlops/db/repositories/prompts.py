# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from mlops.db.models import Prompt


class PromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        name: str,
        template: str,
        version: int = 1,
        recipe_type: Optional[str] = None,
        variables: Optional[list[str]] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> Prompt:
        prompt = Prompt(
            name = name,
            version = version,
            recipe_type = recipe_type,
            template = template,
            variables = variables or [],
            description = description,
            created_by = created_by,
            extra = extra or {},
        )
        self.session.add(prompt)
        await self.session.flush()
        await self.session.refresh(prompt)
        return prompt

    async def get(self, prompt_id: uuid.UUID) -> Optional[Prompt]:
        result = await self.session.execute(
            select(Prompt).where(Prompt.id == prompt_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_active_by_name(self, name: str) -> Optional[Prompt]:
        result = await self.session.execute(
            select(Prompt)
            .where(Prompt.name == name, Prompt.is_active.is_(True))
            .order_by(desc(Prompt.version))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        recipe_type: Optional[str] = None,
        only_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Prompt]:
        stmt = (
            select(Prompt)
            .order_by(Prompt.name.asc(), desc(Prompt.version))
            .limit(limit)
            .offset(offset)
        )
        if recipe_type:
            stmt = stmt.where(Prompt.recipe_type == recipe_type)
        if only_active:
            stmt = stmt.where(Prompt.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def patch(
        self,
        prompt_id: uuid.UUID,
        *,
        template: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        variables: Optional[list[str]] = None,
    ) -> None:
        values: dict[str, Any] = {}
        if template is not None:
            values["template"] = template
        if description is not None:
            values["description"] = description
        if is_active is not None:
            values["is_active"] = is_active
        if variables is not None:
            values["variables"] = variables
        if not values:
            return
        await self.session.execute(
            update(Prompt).where(Prompt.id == prompt_id).values(**values)
        )

    async def delete(self, prompt_id: uuid.UUID) -> None:
        prompt = await self.get(prompt_id)
        if prompt is not None:
            await self.session.delete(prompt)
