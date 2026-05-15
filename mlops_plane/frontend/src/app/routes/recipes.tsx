// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { createRoute } from "@tanstack/react-router";
import { lazy } from "react";
import { requireAuth } from "../auth-guards";
import { Route as rootRoute } from "./__root";

const RecipeListPage = lazy(() =>
  import("@/features/mlops").then((m) => ({ default: m.RecipeListPage })),
);

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/recipes",
  beforeLoad: () => requireAuth(),
  component: RecipeListPage,
});
