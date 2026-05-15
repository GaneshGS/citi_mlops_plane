// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane. All rights reserved.

import { useEffect } from "react";
import { useTrainingRuntimeStore } from "@/features/training";

let currentHandler: ((e: BeforeUnloadEvent) => void) | null = null;

/**
 * Mounts a beforeunload guard that warns the user if training is running.
 * Call once at the app root.
 */
export function useTrainingUnloadGuard() {
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (!useTrainingRuntimeStore.getState().isTrainingRunning) return;
      e.preventDefault();
      e.returnValue = "";
    };
    currentHandler = handler;
    window.addEventListener("beforeunload", handler);
    return () => {
      if (currentHandler === handler) currentHandler = null;
      window.removeEventListener("beforeunload", handler);
    };
  }, []);
}

/**
 * Removes the active beforeunload guard (if any).
 * Call this before intentionally ending the session (e.g. shutting down
 * the Studio server) so the "Server stopped" page can render without
 * the browser prompting the user to confirm leaving.
 */
export function removeTrainingUnloadGuard() {
  if (currentHandler) {
    window.removeEventListener("beforeunload", currentHandler);
    currentHandler = null;
  }
}
