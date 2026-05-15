// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { createRoute } from "@tanstack/react-router";
import { lazy } from "react";
import { requireAuth } from "../auth-guards";
import { Route as rootRoute } from "./__root";

const ExperimentListPage = lazy(() =>
  import("@/features/mlops").then((m) => ({ default: m.ExperimentListPage })),
);

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/experiments",
  beforeLoad: () => requireAuth(),
  component: ExperimentListPage,
});
