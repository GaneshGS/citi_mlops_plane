# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Filesystem path helpers for the Citi MLOps Plane backend."""

from __future__ import annotations

import os
from pathlib import Path


def app_data_dir() -> Path:
    """Where the backend keeps its on-disk runtime state.

    Override via ``MLOPS_DATA_DIR``. Defaults to ``~/.citi-mlops-plane``.
    """
    override = os.environ.get("MLOPS_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".citi-mlops-plane"


def auth_db_path() -> Path:
    return app_data_dir() / "auth.db"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents = True, exist_ok = True)
    return path
