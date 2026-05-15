# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Recipe base class + execution context shared across recipes."""

from __future__ import annotations

import enum
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from mlops.integrations import GsspClient, S3Client, StellarClient
from mlops.schemas import RecipeTemplate


class RecipeStage(str, enum.Enum):
    """Canonical stage names for an experiment timeline."""
    loading_data = "loading_data"
    chunking = "chunking"
    generating = "generating"
    splitting_dataset = "splitting_dataset"
    writing_output = "writing_output"
    registering_dataset = "registering_dataset"
    submitting_finetune = "submitting_finetune"


@dataclass
class RecipeContext:
    """Everything a recipe needs to run + record itself."""
    experiment_id: uuid.UUID
    name: str
    fields: dict[str, Any]
    prompt_text: str
    prompt_id: Optional[uuid.UUID]
    prompt_template: Optional[str]
    prompt_version: Optional[int]
    owner_soeid: Optional[str]
    session_factory: async_sessionmaker[AsyncSession]
    gssp: GsspClient
    s3: S3Client
    stellar: StellarClient
    extra: dict[str, Any] = field(default_factory = dict)


class Recipe(ABC):
    """Base class for every recipe template the plane offers."""

    template: RecipeTemplate

    @property
    def id(self) -> str:
        return self.template.id

    @abstractmethod
    async def run(self, ctx: RecipeContext) -> dict[str, Any]:
        """Execute the recipe end-to-end. Must return a summary dict."""
        raise NotImplementedError
