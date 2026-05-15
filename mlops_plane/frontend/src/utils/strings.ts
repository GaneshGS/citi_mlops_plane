// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

export function normalizeNonEmptyName(
  value: string,
  fallback = "Unnamed",
): string {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : fallback;
}

