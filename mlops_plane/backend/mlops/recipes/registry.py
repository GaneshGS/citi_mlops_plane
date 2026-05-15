# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Recipe template registry.

Adding a new recipe = drop a module under ``mlops/recipes`` that exposes a
``Recipe`` subclass + template metadata, then register it here.
"""

from __future__ import annotations

from typing import Optional

from mlops.schemas import RecipeTemplate

from .base import Recipe
from .doc_to_qa import DocumentToQARecipe, TEMPLATE as DOC_TO_QA_TEMPLATE
from .doc_to_extraction import (
    DocumentToExtractionRecipe,
    TEMPLATE as DOC_TO_EXTRACTION_TEMPLATE,
)


# Order here drives display order on the gallery page.
RECIPES: dict[str, Recipe] = {
    DOC_TO_QA_TEMPLATE.id: DocumentToQARecipe(),
    DOC_TO_EXTRACTION_TEMPLATE.id: DocumentToExtractionRecipe(),
}


def list_recipe_templates() -> list[RecipeTemplate]:
    return [r.template for r in RECIPES.values()]


def get_recipe(recipe_id: str) -> Optional[Recipe]:
    return RECIPES.get(recipe_id)
