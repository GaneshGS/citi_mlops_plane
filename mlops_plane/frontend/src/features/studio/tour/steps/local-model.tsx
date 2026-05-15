// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { ReadMore, type TourStep } from "@/features/tour";

export const studioLocalModelStep: TourStep = {
  id: "local-model",
  target: "studio-local-model",
  title: "Model catalog",
  body: (
    <>
      Pick a base model from the internal catalog (or type a model id your
      environment exposes). Select a size that fits your task and VRAM; you can
      start smaller to iterate quickly.{" "}
      <ReadMore href="https://citi.com/docs/basics/fine-tuning-llms-guide" />
    </>
  ),
};
