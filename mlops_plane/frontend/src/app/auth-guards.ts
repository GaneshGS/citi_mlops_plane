// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

/**
 * Auth guards — currently a no-op for local development.
 *
 * Login / change-password / SSO flows are bypassed so the UI is accessible
 * without backend auth. When wiring real Citi SSO later, restore the
 * implementations from git history (commit 67f9aa5 has the originals).
 */

export async function requireAuth(): Promise<void> {
  // No-op: allow every route through.
}

export async function requireGuest(): Promise<void> {
  // No-op: allow the login / signup pages to render but don't redirect.
}

export async function requirePasswordChangeFlow(): Promise<void> {
  // No-op.
}
