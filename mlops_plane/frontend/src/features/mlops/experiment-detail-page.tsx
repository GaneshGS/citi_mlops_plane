// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { getExperiment } from "./api";
import type { ExperimentDetail, ExperimentEvent } from "./types";

const LEVEL_DOT: Record<string, string> = {
  info: "bg-blue-500",
  warn: "bg-amber-500",
  error: "bg-red-500",
};

const TERMINAL_STATES = new Set(["completed", "failed", "cancelled"]);

export function ExperimentDetailPage({
  experimentId,
}: {
  experimentId: string;
}): React.ReactElement {
  const [exp, setExp] = useState<ExperimentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: number | null = null;

    const load = () =>
      getExperiment(experimentId)
        .then((row) => {
          if (cancelled) return;
          setExp(row);
          if (TERMINAL_STATES.has(row.status) && timer != null) {
            window.clearInterval(timer);
            timer = null;
          }
        })
        .catch((e: Error) => {
          if (!cancelled) setError(e.message);
        });

    void load();
    timer = window.setInterval(load, 2000);
    return () => {
      cancelled = true;
      if (timer != null) window.clearInterval(timer);
    };
  }, [experimentId]);

  if (error) {
    return (
      <div className="mx-auto w-full max-w-4xl px-6 py-8">
        <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          Could not load experiment: {error}
        </div>
      </div>
    );
  }

  if (!exp) {
    return (
      <div className="mx-auto w-full max-w-4xl px-6 py-8 text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-8">
      <Link
        to="/experiments"
        className="mb-4 inline-block text-xs text-muted-foreground hover:text-foreground"
      >
        ← All experiments
      </Link>

      <header className="mb-6">
        <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
          {exp.name}
        </h1>
        <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <span>id: {exp.id}</span>
          <span>recipe: {exp.recipe_type}</span>
          <span>status: {exp.status}</span>
          {exp.current_stage && <span>stage: {exp.current_stage}</span>}
          <span>created: {new Date(exp.created_at).toLocaleString()}</span>
        </div>
        {exp.error_message && (
          <div className="mt-3 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
            {exp.error_message}
          </div>
        )}
      </header>

      <section className="mb-8">
        <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Configuration
        </h2>
        <pre className="overflow-x-auto rounded-md border border-border bg-card px-3 py-2 text-xs text-foreground">
          {JSON.stringify(exp.config, null, 2)}
        </pre>
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-muted-foreground">
          S3 Artifacts
        </h2>
        {exp.data_sources.length === 0 ? (
          <p className="text-sm text-muted-foreground">No artifacts recorded yet.</p>
        ) : (
          <div className="overflow-hidden rounded-md border border-border bg-card">
            <table className="w-full text-sm">
              <thead className="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Role</th>
                  <th className="px-3 py-2 text-left font-medium">S3 URI</th>
                  <th className="px-3 py-2 text-left font-medium">Size</th>
                </tr>
              </thead>
              <tbody>
                {exp.data_sources.map((d) => (
                  <tr key={d.id} className="border-t border-border/60">
                    <td className="px-3 py-2 text-foreground">{d.role}</td>
                    <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                      s3://{d.s3_bucket}/{d.s3_key}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground">
                      {d.byte_count != null ? `${d.byte_count} bytes` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mb-8">
        <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Timeline
        </h2>
        {exp.events.length === 0 ? (
          <p className="text-sm text-muted-foreground">No events yet.</p>
        ) : (
          <ol className="space-y-2">
            {exp.events.map((evt) => (
              <EventRow key={evt.id} evt={evt} />
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}

function EventRow({ evt }: { evt: ExperimentEvent }): React.ReactElement {
  return (
    <li className="rounded-md border border-border bg-card px-3 py-2">
      <div className="flex items-center gap-2 text-sm">
        <span
          className={`size-2 shrink-0 rounded-full ${
            LEVEL_DOT[evt.level] ?? "bg-muted-foreground"
          }`}
          aria-hidden
        />
        <span className="font-medium text-foreground">{evt.stage}</span>
        <span className="text-muted-foreground">· {evt.event_type}</span>
        <span className="ml-auto text-xs text-muted-foreground">
          {new Date(evt.created_at).toLocaleTimeString()}
        </span>
      </div>
      {evt.message && (
        <p className="mt-1 text-sm text-foreground/90">{evt.message}</p>
      )}
      {evt.payload && Object.keys(evt.payload).length > 0 && (
        <pre className="mt-1 overflow-x-auto rounded bg-muted/40 px-2 py-1 text-[11px] text-muted-foreground">
          {JSON.stringify(evt.payload, null, 2)}
        </pre>
      )}
    </li>
  );
}
