// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import type { TourStep } from "@/features/tour";
import { studioDatasetStep } from "./dataset";
import { studioLocalModelStep } from "./local-model";
import { studioMethodStep } from "./method";
import { studioNavStep } from "./nav";
import { studioParamsStep } from "./params";
import { studioSaveStep } from "./save";
import { studioStartStep } from "./start";

export const studioTourSteps: TourStep[] = [
  studioNavStep,
  studioLocalModelStep,
  studioMethodStep,
  studioDatasetStep,
  studioParamsStep,
  studioStartStep,
  studioSaveStep,
];

