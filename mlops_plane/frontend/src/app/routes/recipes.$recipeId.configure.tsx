// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { createRoute } from "@tanstack/react-router";
import type { ReactElement } from "react";
import { lazy } from "react";
import { requireAuth } from "../auth-guards";
import { Route as rootRoute } from "./__root";

const RecipeConfigurePage = lazy(() =>
  import("@/features/mlops").then((m) => ({ default: m.RecipeConfigurePage })),
);

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/recipes/$recipeId/configure",
  beforeLoad: () => requireAuth(),
  component: ConfigureRecipeRoute,
});

function ConfigureRecipeRoute(): ReactElement {
  const { recipeId } = Route.useParams();
  return <RecipeConfigurePage recipeId={recipeId} />;
}
