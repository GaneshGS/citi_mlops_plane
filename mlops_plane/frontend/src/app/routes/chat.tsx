// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { ChatPage } from "@/features/chat/chat-page";
import { createRoute } from "@tanstack/react-router";
import { requireAuth } from "../auth-guards";
import { Route as rootRoute } from "./__root";

export type ChatSearch = {
  thread?: string;
  compare?: string;
  new?: string;
};

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/chat",
  beforeLoad: () => requireAuth(),
  validateSearch: (search: Record<string, unknown>): ChatSearch => ({
    thread: typeof search.thread === "string" ? search.thread : undefined,
    compare: typeof search.compare === "string" ? search.compare : undefined,
    new: typeof search.new === "string" ? search.new : undefined,
  }),
  component: ChatPage,
});
