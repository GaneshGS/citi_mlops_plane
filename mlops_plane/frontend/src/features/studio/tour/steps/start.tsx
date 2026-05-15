// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import type { TourStep } from "@/features/tour";

export const studioStartStep: TourStep = {
  id: "start",
  target: "studio-start",
  title: "Start training",
  body: (
    <>
      Kick off training. If it errors immediately, check model id, file paths,
      and dataset access first. Start with a small run to sanity-check loss +
      sample outputs before burning hours.
    </>
  ),
};
