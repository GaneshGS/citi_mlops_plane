// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { listRecipeTemplates } from "./api";
import type { RecipeTemplate } from "./types";

export function RecipeListPage(): React.ReactElement {
  const [templates, setTemplates] = useState<RecipeTemplate[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listRecipeTemplates()
      .then((rows) => {
        if (!cancelled) setTemplates(rows);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const byCategory = (templates ?? []).reduce<Record<string, RecipeTemplate[]>>(
    (acc, t) => {
      (acc[t.category] ||= []).push(t);
      return acc;
    },
    {},
  );

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
          Recipes
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Pick a template, fill in the configuration, and the MLOps plane will
          orchestrate the rest — load from S3, call GSSP-GS, write your training
          and test datasets back to S3, and record every step against an
          experiment.
        </p>
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          Could not load recipes: {error}
        </div>
      )}

      {!templates && !error && (
        <div className="text-sm text-muted-foreground">Loading…</div>
      )}

      {templates && templates.length === 0 && (
        <div className="rounded-md border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground">
          No recipes registered yet.
        </div>
      )}

      {Object.entries(byCategory).map(([category, group]) => (
        <section key={category} className="mb-8">
          <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-muted-foreground">
            {category}
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {group.map((t) => (
              <Link
                key={t.id}
                to="/recipes/$recipeId/configure"
                params={{ recipeId: t.id }}
                className="group rounded-lg border border-border bg-card p-4 transition-colors hover:border-foreground/30 hover:bg-accent/30"
              >
                <div className="font-heading text-base font-semibold text-foreground">
                  {t.name}
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {t.description}
                </p>
                <div className="mt-3 text-xs font-medium text-muted-foreground/80">
                  {t.fields.length} configuration field
                  {t.fields.length === 1 ? "" : "s"} · 1 prompt
                </div>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
