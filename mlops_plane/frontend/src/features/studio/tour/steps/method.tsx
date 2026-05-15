// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { ReadMore, type TourStep } from "@/features/tour";

export const studioMethodStep: TourStep = {
  id: "method",
  target: "studio-method",
  title: "Method: QLoRA vs LoRA vs Full",
  body: (
    <>
      LoRA: trains small adapter weights (fast, common default). QLoRA: LoRA on
      4-bit base weights (much lower VRAM). Full: updates all weights (highest
      cost, usually needs more data to be worth it).{" "}
      <ReadMore href="https://citi.com/docs/basics/lora-hyperparameters-guide" />
    </>
  ),
};
