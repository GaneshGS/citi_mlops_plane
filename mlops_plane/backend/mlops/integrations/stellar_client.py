# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Stellar client — Citi's dataset registry + fine-tuning service.

Three operations the MLOps plane needs:

1. ``register_dataset(s3_uri, role, ...)`` — uploads a manifest/dataset file
   reference, returns a Stellar dataset ID.
2. ``submit_finetune(train_id, test_id, base_model, hyperparams, ...)`` —
   queues a fine-tuning job and returns a Stellar job ID.
3. ``get_status(job_id)`` — polls a job's status + metrics.

All three have a dummy mode for local development. URL, auth, and paths
come from environment variables — drop in real values when ready.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from mlops.config import StellarSettings, get_settings


@dataclass
class StellarDatasetRegistration:
    stellar_dataset_id: str
    role: str
    source_s3_uri: str
    byte_count: Optional[int] = None
    row_count: Optional[int] = None
    raw: dict[str, Any] = field(default_factory = dict)


@dataclass
class StellarFinetuneSubmission:
    stellar_job_id: str
    status: str
    submitted_at_iso: str
    raw: dict[str, Any] = field(default_factory = dict)


@dataclass
class StellarStatus:
    stellar_job_id: str
    status: str
    metrics: dict[str, Any] = field(default_factory = dict)
    result_model_uri: Optional[str] = None
    raw: dict[str, Any] = field(default_factory = dict)


class StellarClient:
    def __init__(self, settings: Optional[StellarSettings] = None) -> None:
        self._settings = settings or get_settings().stellar

    @property
    def settings(self) -> StellarSettings:
        return self._settings

    # ---------- dataset registration ----------

    async def register_dataset(
        self,
        *,
        s3_uri: str,
        role: str,
        experiment_id: str,
        byte_count: Optional[int] = None,
        row_count: Optional[int] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> StellarDatasetRegistration:
        body = {
            "s3_uri": s3_uri,
            "role": role,
            "experiment_id": experiment_id,
            "byte_count": byte_count,
            "row_count": row_count,
            "metadata": extra or {},
        }
        if self._settings.use_dummy or not self._settings.base_url:
            stellar_id = "ds_" + hashlib.sha1(
                f"{experiment_id}:{role}:{s3_uri}".encode()
            ).hexdigest()[:16]
            return StellarDatasetRegistration(
                stellar_dataset_id = stellar_id,
                role = role,
                source_s3_uri = s3_uri,
                byte_count = byte_count,
                row_count = row_count,
                raw = {"mode": "dummy", "echo": body},
            )

        url = self._settings.base_url.rstrip("/") + self._settings.register_dataset_path
        async with httpx.AsyncClient(
            timeout = self._settings.request_timeout_seconds
        ) as client:
            r = await client.post(url, json = body, headers = self._headers())
        r.raise_for_status()
        payload = r.json()
        return StellarDatasetRegistration(
            stellar_dataset_id = str(payload.get("dataset_id") or payload.get("id")),
            role = role,
            source_s3_uri = s3_uri,
            byte_count = payload.get("byte_count", byte_count),
            row_count = payload.get("row_count", row_count),
            raw = payload,
        )

    # ---------- fine-tune submit ----------

    async def submit_finetune(
        self,
        *,
        experiment_id: str,
        train_dataset_id: str,
        test_dataset_id: Optional[str],
        base_model: str,
        hyperparams: dict[str, Any],
    ) -> StellarFinetuneSubmission:
        body = {
            "experiment_id": experiment_id,
            "train_dataset_id": train_dataset_id,
            "test_dataset_id": test_dataset_id,
            "base_model": base_model,
            "hyperparameters": hyperparams,
        }

        if self._settings.use_dummy or not self._settings.base_url:
            job_id = "ft_" + hashlib.sha1(
                f"{experiment_id}:{train_dataset_id}:{base_model}".encode()
            ).hexdigest()[:16]
            return StellarFinetuneSubmission(
                stellar_job_id = job_id,
                status = "queued",
                submitted_at_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                raw = {"mode": "dummy", "echo": body},
            )

        url = self._settings.base_url.rstrip("/") + self._settings.submit_finetune_path
        async with httpx.AsyncClient(
            timeout = self._settings.request_timeout_seconds
        ) as client:
            r = await client.post(url, json = body, headers = self._headers())
        r.raise_for_status()
        payload = r.json()
        return StellarFinetuneSubmission(
            stellar_job_id = str(payload.get("job_id") or payload.get("id")),
            status = payload.get("status", "queued"),
            submitted_at_iso = payload.get(
                "submitted_at",
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ),
            raw = payload,
        )

    # ---------- status ----------

    async def get_status(self, stellar_job_id: str) -> StellarStatus:
        if self._settings.use_dummy or not self._settings.base_url:
            return StellarStatus(
                stellar_job_id = stellar_job_id,
                status = "running",
                metrics = {"step": 100, "loss": 0.42, "eta_seconds": 600},
                result_model_uri = None,
                raw = {"mode": "dummy"},
            )

        path = self._settings.get_status_path.replace("{job_id}", stellar_job_id)
        url = self._settings.base_url.rstrip("/") + path
        async with httpx.AsyncClient(
            timeout = self._settings.request_timeout_seconds
        ) as client:
            r = await client.get(url, headers = self._headers())
        r.raise_for_status()
        payload = r.json()
        return StellarStatus(
            stellar_job_id = stellar_job_id,
            status = payload.get("status", "unknown"),
            metrics = payload.get("metrics", {}) or {},
            result_model_uri = payload.get("result_model_uri"),
            raw = payload,
        )

    # ---------- headers ----------

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Correlation-Id": str(uuid.uuid4()),
        }
        if self._settings.auth_token:
            headers["Authorization"] = f"Bearer {self._settings.auth_token}"
        return headers


_singleton: Optional[StellarClient] = None


def get_stellar_client() -> StellarClient:
    global _singleton
    if _singleton is None:
        _singleton = StellarClient()
    return _singleton
