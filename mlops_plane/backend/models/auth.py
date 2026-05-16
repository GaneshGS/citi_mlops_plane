# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane. All rights reserved.

"""Pydantic schemas for the authentication routes."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------- requests ----------


class AuthLoginRequest(BaseModel):
    username: str = Field(..., min_length = 1, max_length = 128)
    password: str = Field(..., min_length = 1)


class DesktopLoginRequest(BaseModel):
    secret: str = Field(..., min_length = 1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length = 1)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length = 1)
    new_password: str = Field(..., min_length = 8, max_length = 128)


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length = 1, max_length = 128)
    expires_in_days: Optional[int] = Field(default = None, ge = 1, le = 3650)


# ---------- responses ----------


class AuthStatusResponse(BaseModel):
    initialized: bool
    default_username: str
    requires_password_change: bool


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_at: str
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_active: bool


class ApiKeyListResponse(BaseModel):
    api_keys: list[ApiKeyResponse]


class CreateApiKeyResponse(BaseModel):
    key: str
    api_key: ApiKeyResponse
