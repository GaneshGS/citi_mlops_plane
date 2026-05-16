// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { createRouter } from "@tanstack/react-router";
import { Route as rootRoute } from "./routes/__root";
import { Route as chatRoute } from "./routes/chat";
import { Route as indexRoute } from "./routes/index";
import { Route as loginRoute } from "./routes/login";
import { Route as onboardingRoute } from "./routes/onboarding";
import { Route as changePasswordRoute } from "./routes/change-password";
import { Route as studioRoute } from "./routes/studio";
// Citi MLOps Plane — recipes / experiments / prompts.
import { Route as recipesRoute } from "./routes/recipes";
import { Route as recipeConfigureRoute } from "./routes/recipes.$recipeId.configure";
import { Route as experimentsRoute } from "./routes/experiments";
import { Route as experimentDetailRoute } from "./routes/experiments.$experimentId";
import { Route as promptsRoute } from "./routes/prompts";

const routeTree = rootRoute.addChildren([
  indexRoute,
  onboardingRoute,
  loginRoute,
  changePasswordRoute,
  studioRoute,
  chatRoute,
  recipesRoute,
  recipeConfigureRoute,
  experimentsRoute,
  experimentDetailRoute,
  promptsRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
