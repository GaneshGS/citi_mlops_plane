# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""All MLOps plane FastAPI routers, aggregated under ``/api/mlops``."""

from fastapi import APIRouter

from .experiments import router as experiments_router
from .prompts import router as prompts_router
from .recipes import router as recipes_router
from .finetune import router as finetune_router

router = APIRouter()
router.include_router(experiments_router, prefix = "/experiments", tags = ["mlops-experiments"])
router.include_router(prompts_router, prefix = "/prompts", tags = ["mlops-prompts"])
router.include_router(recipes_router, prefix = "/recipes", tags = ["mlops-recipes"])
router.include_router(finetune_router, prefix = "/finetune", tags = ["mlops-finetune"])

__all__ = ["router"]
