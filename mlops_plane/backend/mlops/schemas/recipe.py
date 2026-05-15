# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

from __future__ import annotations

import uuid
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


FieldType = Literal["string", "integer", "number", "boolean", "select", "textarea", "s3_uri"]


class RecipeFieldSchema(BaseModel):
    key: str
    label: str
    type: FieldType
    description: Optional[str] = None
    required: bool = False
    default: Any = None
    placeholder: Optional[str] = None
    options: Optional[list[dict[str, Any]]] = None
    min: Optional[float] = None
    max: Optional[float] = None


class RecipeTemplate(BaseModel):
    """Metadata for a recipe shown on the templates gallery + configure page."""
    id: str                        # stable key (e.g. "doc_to_qa")
    name: str
    category: str                  # e.g. "Training Dataset Recipes"
    description: str
    fields: list[RecipeFieldSchema]
    prompt_field_label: str = "Use-case prompt"
    prompt_placeholder: str = (
        "Describe what you want the model to learn (audience, tone, "
        "kinds of questions to generate, edge cases to cover, ...)"
    )


class RecipeRunRequest(BaseModel):
    """Payload for ``POST /api/mlops/recipes/{recipe_id}/run``."""
    name: str = Field(..., min_length = 1)
    fields: dict[str, Any]         # values for the recipe's RecipeFieldSchema
    prompt_text: str = ""          # the user's free-form use-case prompt
    prompt_id: Optional[uuid.UUID] = None
    owner_soeid: Optional[str] = None


class RecipeRunResponse(BaseModel):
    experiment_id: uuid.UUID
    status: str
    detail_url: str
