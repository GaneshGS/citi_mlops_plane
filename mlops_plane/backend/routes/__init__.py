# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""HTTP route modules for the Citi MLOps Plane backend.

The MLOps surface (recipes, experiments, prompts, fine-tune) lives under
``mlops.routes``. The legacy ``training`` / ``inference`` / ``models`` /
``datasets`` / ``export`` route shells are kept here as 503 stubs so the
existing UI pages (Chat, Compare Models, Training Monitor) don't 404 while
the GSSP-GS / Stellar wiring lands in the next pass.
"""

from routes.auth import router as auth_router
from routes.datasets import router as datasets_router
from routes.export import router as export_router
from routes.inference import router as inference_router
from routes.models import router as models_router
from routes.training import router as training_router
from routes.training_history import router as training_history_router

__all__ = [
    "auth_router",
    "datasets_router",
    "export_router",
    "inference_router",
    "models_router",
    "training_router",
    "training_history_router",
]
