// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { createRoute } from "@tanstack/react-router";
import { lazy } from "react";
import { requireAuth } from "../auth-guards";
import { Route as rootRoute } from "./__root";

export type OnboardingSearch = { redirectTo?: string };

const WizardLayout = lazy(() =>
  import("@/features/onboarding/components/wizard-layout").then((m) => ({
    default: m.WizardLayout,
  })),
);

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/onboarding",
  beforeLoad: () => requireAuth(),
  validateSearch: (search: Record<string, unknown>): OnboardingSearch => ({
    redirectTo: typeof search.redirectTo === "string" ? search.redirectTo : undefined,
  }),
  component: WizardLayout,
});
