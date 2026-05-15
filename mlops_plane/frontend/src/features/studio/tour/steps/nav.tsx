// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { ReadMore, type TourStep } from "@/features/tour";

export const studioNavStep: TourStep = {
  id: "nav",
  target: "navbar",
  title: "Quick orientation",
  body: (
    <>
      Fine-tuning Plane: pick base model, dataset, hyperparams, then start training. After
      you start, you’ll see a Training view with live loss/metrics. Chat is for
      testing base vs LoRA adapters.{" "}
      <ReadMore href="https://citi.com/docs/get-started/fine-tuning-for-beginners" />
    </>
  ),
};
