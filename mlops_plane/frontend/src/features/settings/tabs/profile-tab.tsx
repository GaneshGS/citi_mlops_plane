// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { ProfilePersonalizationPanel } from "@/features/profile";

export function ProfileTab() {
  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-lg font-semibold font-heading">Profile</h1>
        <p className="text-xs text-muted-foreground">
          Update how your profile appears in Plane.
        </p>
      </header>

      <ProfilePersonalizationPanel />
    </div>
  );
}
