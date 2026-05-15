# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""GSSP-GS client — Citi's OpenAI-compatible LLM gateway.

Two modes:

* ``use_dummy = True`` (default for local dev) returns a deterministic stub so
  recipes can run end-to-end without network access.
* ``use_dummy = False`` POSTs to the real GSSP pass-through endpoint. URL,
  auth and headers come from environment variables — see ``mlops.config``.

Swap real values into the env and nothing else changes.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from mlops.config import GsspSettings, get_settings


@dataclass
class GsspResponse:
    """Normalized response from a GSSP completion call."""
    text: str
    raw: dict[str, Any]
    model: str
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    latency_ms: Optional[int] = None
    correlation_id: Optional[str] = None
    finish_reason: Optional[str] = None


@dataclass
class GsspMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class GsspChatRequest:
    """Caller-facing chat-completion request."""
    messages: list[GsspMessage]
    model: Optional[str] = None
    temperature: float = 0.2
    max_tokens: Optional[int] = 1024
    response_format: Optional[dict[str, Any]] = None
    extra: dict[str, Any] = field(default_factory = dict)


class GsspClient:
    """Thin async client over the GSSP pass-through endpoint."""

    def __init__(self, settings: Optional[GsspSettings] = None) -> None:
        self._settings = settings or get_settings().gssp

    @property
    def settings(self) -> GsspSettings:
        return self._settings

    # ---------- public API ----------

    async def chat(self, request: GsspChatRequest) -> GsspResponse:
        """Run a chat completion."""
        if self._settings.use_dummy or not self._settings.base_url:
            return self._dummy_chat(request)
        return await self._real_chat(request)

    async def healthz(self) -> dict[str, Any]:
        if self._settings.use_dummy or not self._settings.base_url:
            return {"status": "ok", "mode": "dummy"}
        async with httpx.AsyncClient(timeout = 5.0) as client:
            r = await client.get(
                self._settings.base_url.rstrip("/")
                + "/api/gssp-generation-service/healthz",
            )
            return {"status": r.status_code, "body": r.text}

    # ---------- transport ----------

    async def _real_chat(self, request: GsspChatRequest) -> GsspResponse:
        body = self._build_request_body(request)
        headers = self._build_headers()
        url = self._settings.url
        correlation_id = headers.get("X-Correlation-Id")

        t0 = time.monotonic()
        async with httpx.AsyncClient(
            timeout = self._settings.request_timeout_seconds
        ) as client:
            r = await client.post(url, json = body, headers = headers)
        latency_ms = int((time.monotonic() - t0) * 1000)
        r.raise_for_status()
        payload: dict[str, Any] = r.json()

        return _parse_openai_style(
            payload,
            request_model = body.get("model", ""),
            latency_ms = latency_ms,
            correlation_id = correlation_id,
        )

    # ---------- request shaping ----------

    def _build_request_body(self, request: GsspChatRequest) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": request.model or self._settings.default_model,
            "messages": [m.to_dict() for m in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.response_format is not None:
            body["response_format"] = request.response_format
        if request.extra:
            body.update(request.extra)
        return body

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Correlation-Id": str(uuid.uuid4()),
            "X-Application-Id": self._settings.application_id,
        }
        if self._settings.auth_token:
            headers["Authorization"] = f"Bearer {self._settings.auth_token}"
        if self._settings.soeid:
            headers["X-SOEID"] = self._settings.soeid
        return headers

    # ---------- dummy ----------

    def _dummy_chat(self, request: GsspChatRequest) -> GsspResponse:
        """Deterministic stub used for local dev / tests.

        For structured outputs (``response_format`` set), we emit a minimal
        JSON object matching the most common Citi recipe schemas so the
        downstream orchestrator's parser keeps working.
        """
        # Pick the last user message as the seed.
        seed = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            "",
        )

        if request.response_format and request.response_format.get("type") == "json_object":
            payload: dict[str, Any] = {
                "question": "What is the main topic of this chunk?",
                "answer": (seed[:120] + "...") if len(seed) > 120 else seed,
                "evidence_quote": seed[:80],
            }
            text = json.dumps(payload, ensure_ascii = False)
        else:
            text = f"[gssp-dummy] {seed[:200]}"

        return GsspResponse(
            text = text,
            raw = {"id": f"dummy-{uuid.uuid4()}", "object": "chat.completion"},
            model = request.model or self._settings.default_model,
            tokens_in = max(1, len(seed.split())),
            tokens_out = max(1, len(text.split())),
            latency_ms = 1,
            correlation_id = str(uuid.uuid4()),
            finish_reason = "stop",
        )


def _parse_openai_style(
    payload: dict[str, Any],
    request_model: str,
    latency_ms: int,
    correlation_id: Optional[str],
) -> GsspResponse:
    """Best-effort parse of an OpenAI-style chat completion payload."""
    choice = (payload.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    text = msg.get("content") or ""
    usage = payload.get("usage") or {}
    return GsspResponse(
        text = text,
        raw = payload,
        model = payload.get("model") or request_model,
        tokens_in = usage.get("prompt_tokens"),
        tokens_out = usage.get("completion_tokens"),
        latency_ms = latency_ms,
        correlation_id = correlation_id,
        finish_reason = choice.get("finish_reason"),
    )


_singleton: Optional[GsspClient] = None


def get_gssp_client() -> GsspClient:
    """Process-wide singleton (settings frozen at first call)."""
    global _singleton
    if _singleton is None:
        _singleton = GsspClient()
    return _singleton
