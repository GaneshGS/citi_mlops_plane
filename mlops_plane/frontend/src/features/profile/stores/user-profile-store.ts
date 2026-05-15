// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface UserProfileState {
  displayName: string;
  avatarDataUrl: string | null;
  setDisplayName: (displayName: string) => void;
  setAvatarDataUrl: (avatarDataUrl: string | null) => void;
}

export const useUserProfileStore = create<UserProfileState>()(
  persist(
    (set) => ({
      displayName: "",
      avatarDataUrl: null,
      setDisplayName: (displayName) => set({ displayName }),
      setAvatarDataUrl: (avatarDataUrl) => set({ avatarDataUrl }),
    }),
    { name: "mlops_user_profile" },
  ),
);
