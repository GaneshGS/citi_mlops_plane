// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { getAuthToken } from "@/features/auth";
import { decodeJwtSubject } from "../utils/jwt-subject";
import { useUserProfileStore } from "../stores/user-profile-store";

export function useEffectiveProfile() {
  const displayName = useUserProfileStore((s) => s.displayName);
  const avatarDataUrl = useUserProfileStore((s) => s.avatarDataUrl);

  const sessionSub = decodeJwtSubject(getAuthToken());
  const dn = displayName.trim();
  return {
    sessionSub,
    displayTitle: dn || "Citi MLOps",
    avatarDataUrl,
  };
}
