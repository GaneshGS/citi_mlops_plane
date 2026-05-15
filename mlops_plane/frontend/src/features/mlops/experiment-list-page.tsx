// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { listExperiments } from "./api";
import type { ExperimentStatus, ExperimentSummary } from "./types";

const STATUS_COLOR: Record<ExperimentStatus, string> = {
  pending: "bg-muted text-foreground",
  loading_data: "bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-200",
  preparing_dataset: "bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-200",
  registering_dataset: "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200",
  submitted_finetune: "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200",
  training: "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-200",
  completed: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200",
  failed: "bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-200",
  cancelled: "bg-muted text-muted-foreground",
};

export function ExperimentListPage(): React.ReactElement {
  const [rows, setRows] = useState<ExperimentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      listExperiments({ limit: 100 })
        .then((r) => {
          if (!cancelled) setRows(r);
        })
        .catch((e: Error) => {
          if (!cancelled) setError(e.message);
        });
    void load();
    const timer = window.setInterval(load, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-8">
      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
            Experiments
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Every recipe run creates an experiment. Click one to inspect its
            stage timeline, S3 artifacts, and GSSP invocations.
          </p>
        </div>
        <Link
          to="/recipes"
          className="rounded-md border border-border bg-card px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-accent/30"
        >
          New recipe run →
        </Link>
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          Could not load experiments: {error}
        </div>
      )}

      {!rows && !error && (
        <div className="text-sm text-muted-foreground">Loading…</div>
      )}

      {rows && rows.length === 0 && (
        <div className="rounded-md border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground">
          No experiments yet. Start one from the{" "}
          <Link to="/recipes" className="underline">
            Recipes
          </Link>{" "}
          page.
        </div>
      )}

      {rows && rows.length > 0 && (
        <div className="overflow-hidden rounded-md border border-border bg-card">
          <table className="w-full text-sm">
            <thead className="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Name</th>
                <th className="px-4 py-2 text-left font-medium">Recipe</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">Stage</th>
                <th className="px-4 py-2 text-left font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t border-border/60 hover:bg-accent/20">
                  <td className="px-4 py-2">
                    <Link
                      to="/experiments/$experimentId"
                      params={{ experimentId: r.id }}
                      className="font-medium text-foreground hover:underline"
                    >
                      {r.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">{r.recipe_type}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        STATUS_COLOR[r.status] ?? "bg-muted text-foreground"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {r.current_stage ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
