# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane. All rights reserved.

"""Pydantic schemas for user / token responses."""

from __future__ import annotations

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False
