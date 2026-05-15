// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { RouterProvider } from "@tanstack/react-router";
import { router } from "./router";

export function App() {
  return <RouterProvider router={router} />;
}
