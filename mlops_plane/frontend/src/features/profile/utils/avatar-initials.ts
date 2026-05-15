// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

export function initialsFromName(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) return "?";
  return trimmed[0]!.toUpperCase();
}

/** Default blue background for avatar fallback (readable white text). */
export function avatarBgStyle(): { backgroundColor: string } {
  return { backgroundColor: "hsl(217 58% 48%)" };
}
