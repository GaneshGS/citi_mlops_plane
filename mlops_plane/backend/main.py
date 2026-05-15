# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""FastAPI entrypoint for the Citi MLOps Plane backend."""

from __future__ import annotations

import os
import sys
import warnings
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

# Make sibling packages importable when launched as `uvicorn main:app`.
_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# Suppress noisy dependency warnings in production.
if os.getenv("ENVIRONMENT_TYPE", "production") == "production":
    warnings.filterwarnings("ignore")

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from auth import storage
from auth.authentication import get_current_subject
from loggers.config import LogConfig
from loggers.handlers import LoggingMiddleware
from mlops import __version__ as MLOPS_VERSION
from mlops.db import shutdown_engine as mlops_shutdown_engine
from mlops.routes import router as mlops_router
from routes import (
    auth_router,
    datasets_router,
    export_router,
    inference_router,
    models_router,
    training_history_router,
    training_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed the default admin (if needed) and dispose the DB engine on exit."""
    if storage.ensure_default_admin():
        bootstrap_pw = storage.get_bootstrap_password()
        app.state.bootstrap_password = bootstrap_pw
        print("\n" + "=" * 60)
        print("DEFAULT ADMIN ACCOUNT CREATED")
        print(f"    username: {storage.DEFAULT_ADMIN_USERNAME}")
        print("    Open the Citi MLOps Plane UI to sign in and change it.")
        print("=" * 60 + "\n")
    else:
        app.state.bootstrap_password = storage.get_bootstrap_password()
    yield
    try:
        await mlops_shutdown_engine()
    except Exception:  # noqa: BLE001 — never block shutdown on DB cleanup
        pass


app = FastAPI(
    title = "Citi MLOps Plane",
    version = MLOPS_VERSION,
    description = (
        "Citi MLOps Plane — recipes, experiments, prompts, and Stellar-driven "
        "fine-tuning. All LLM calls route through GSSP-GS; all fine-tuning "
        "routes through Stellar; all data flows through S3."
    ),
    lifespan = lifespan,
)

# Structured logging.
LogConfig.setup_logging(
    service_name = "citi-mlops-plane-backend",
    env = os.getenv("ENVIRONMENT_TYPE", "production"),
)
app.add_middleware(LoggingMiddleware)

# CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# Routers.
app.include_router(auth_router, prefix = "/api/auth", tags = ["auth"])
app.include_router(mlops_router, prefix = "/api/mlops", tags = ["mlops"])

# Legacy UI placeholder routes — Chat, Compare Models, Training Monitor pages
# still hit these paths. They currently return 503 and will be wired through
# GSSP-GS / Stellar in a follow-up pass.
app.include_router(inference_router, prefix = "/api/inference", tags = ["inference"])
app.include_router(training_router, prefix = "/api/train", tags = ["training"])
app.include_router(training_history_router, prefix = "/api/train", tags = ["training-history"])
app.include_router(models_router, prefix = "/api/models", tags = ["models"])
app.include_router(datasets_router, prefix = "/api/datasets", tags = ["datasets"])
app.include_router(export_router, prefix = "/api/export", tags = ["export"])


@app.get("/api/health")
async def health_check() -> dict[str, object]:
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "citi-mlops-plane",
        "version": MLOPS_VERSION,
    }


@app.post("/api/shutdown")
async def shutdown_server(
    request: Request,
    _subject: str = Depends(get_current_subject),
) -> dict[str, str]:
    """Graceful shutdown — used by the UI's quit dialog."""
    import asyncio
    import signal

    async def _delayed_shutdown() -> None:
        await asyncio.sleep(0.2)
        os.kill(os.getpid(), signal.SIGTERM)

    request.app.state._shutdown_task = asyncio.create_task(_delayed_shutdown())
    return {"status": "shutting_down"}
