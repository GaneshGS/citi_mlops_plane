# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Central, env-driven settings for the Citi MLOps plane.

Every external dependency (Postgres, GSSP-GS, Stellar, S3) is configured
exclusively from environment variables here. No URL, token or bucket name
is hard-coded anywhere else in the codebase — plug real values into the env
and the plane points at production.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen = True)
class DatabaseSettings:
    """PostgreSQL connection."""
    dsn: str
    echo: bool

    @property
    def is_configured(self) -> bool:
        return bool(self.dsn)


@dataclass(frozen = True)
class GsspSettings:
    """GSSP-GS LLM endpoint configuration."""
    base_url: str
    pass_through_path: str
    auth_token: str
    application_id: str
    soeid: str
    default_model: str
    request_timeout_seconds: float
    use_dummy: bool

    @property
    def url(self) -> str:
        if not self.base_url:
            return ""
        return self.base_url.rstrip("/") + self.pass_through_path


@dataclass(frozen = True)
class StellarSettings:
    """Stellar dataset registration + fine-tune endpoint configuration."""
    base_url: str
    register_dataset_path: str
    submit_finetune_path: str
    get_status_path: str
    auth_token: str
    request_timeout_seconds: float
    use_dummy: bool


@dataclass(frozen = True)
class S3Settings:
    """S3 access configuration (placeholder until boto3 wiring lands)."""
    endpoint_url: str   # blank → real AWS; set for MinIO / dev mock
    region: str
    access_key_id: str
    secret_access_key: str
    default_input_bucket: str
    default_output_bucket: str
    use_dummy: bool


@dataclass(frozen = True)
class MlopsSettings:
    db: DatabaseSettings
    gssp: GsspSettings
    stellar: StellarSettings
    s3: S3Settings


@lru_cache(maxsize = 1)
def get_settings() -> MlopsSettings:
    """Read environment once, cache, and return immutable settings."""

    db = DatabaseSettings(
        dsn = _env(
            "MLOPS_POSTGRES_DSN",
            # Local default — matches docker-compose.yml shipped with the repo.
            "postgresql+asyncpg://mlops:mlops@localhost:5432/mlops",
        ),
        echo = _env_bool("MLOPS_DB_ECHO", default = False),
    )

    gssp = GsspSettings(
        base_url = _env("GSSP_BASE_URL", ""),
        pass_through_path = _env(
            "GSSP_PASS_THROUGH_PATH",
            "/api/gssp-generation-service/v1/generate-pass-through",
        ),
        auth_token = _env("GSSP_AUTH_TOKEN", ""),
        application_id = _env("GSSP_APPLICATION_ID", "citi-mlops-plane"),
        soeid = _env("GSSP_SOEID", ""),
        default_model = _env("GSSP_DEFAULT_MODEL", "gpt-4o-mini"),
        request_timeout_seconds = float(_env("GSSP_TIMEOUT_SECONDS", "120")),
        # Default to dummy mode so local dev works out of the box.
        use_dummy = _env_bool("GSSP_USE_DUMMY", default = True),
    )

    stellar = StellarSettings(
        base_url = _env("STELLAR_BASE_URL", ""),
        register_dataset_path = _env(
            "STELLAR_REGISTER_DATASET_PATH", "/api/v1/datasets/register"
        ),
        submit_finetune_path = _env(
            "STELLAR_SUBMIT_FINETUNE_PATH", "/api/v1/finetune/submit"
        ),
        get_status_path = _env(
            "STELLAR_GET_STATUS_PATH", "/api/v1/finetune/{job_id}/status"
        ),
        auth_token = _env("STELLAR_AUTH_TOKEN", ""),
        request_timeout_seconds = float(_env("STELLAR_TIMEOUT_SECONDS", "60")),
        use_dummy = _env_bool("STELLAR_USE_DUMMY", default = True),
    )

    s3 = S3Settings(
        endpoint_url = _env("S3_ENDPOINT_URL", ""),
        region = _env("AWS_REGION", "us-east-1"),
        access_key_id = _env("AWS_ACCESS_KEY_ID", ""),
        secret_access_key = _env("AWS_SECRET_ACCESS_KEY", ""),
        default_input_bucket = _env("MLOPS_S3_INPUT_BUCKET", "citi-mlops-inputs"),
        default_output_bucket = _env("MLOPS_S3_OUTPUT_BUCKET", "citi-mlops-outputs"),
        use_dummy = _env_bool("S3_USE_DUMMY", default = True),
    )

    return MlopsSettings(db = db, gssp = gssp, stellar = stellar, s3 = s3)
