// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { createRoute } from "@tanstack/react-router";
import type { ReactElement } from "react";
import { lazy } from "react";
import { requireAuth } from "../auth-guards";
import { Route as rootRoute } from "./__root";

const ExperimentDetailPage = lazy(() =>
  import("@/features/mlops").then((m) => ({ default: m.ExperimentDetailPage })),
);

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/experiments/$experimentId",
  beforeLoad: () => requireAuth(),
  component: ExperimentDetailRoute,
});

function ExperimentDetailRoute(): ReactElement {
  const { experimentId } = Route.useParams();
  return <ExperimentDetailPage experimentId={experimentId} />;
}
