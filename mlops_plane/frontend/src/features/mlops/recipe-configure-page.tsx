// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { getRecipeTemplate, runRecipe } from "./api";
import type { RecipeFieldSchema, RecipeTemplate } from "./types";

interface RecipeConfigurePageProps {
  recipeId: string;
}

export function RecipeConfigurePage({
  recipeId,
}: RecipeConfigurePageProps): React.ReactElement {
  const navigate = useNavigate();
  const [template, setTemplate] = useState<RecipeTemplate | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState<string>("");
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [promptText, setPromptText] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getRecipeTemplate(recipeId)
      .then((t) => {
        if (cancelled) return;
        setTemplate(t);
        // Seed defaults so optional fields aren't empty.
        const seeded: Record<string, unknown> = {};
        for (const f of t.fields) {
          if (f.default !== undefined && f.default !== null) {
            seeded[f.key] = f.default;
          }
        }
        setValues(seeded);
        if (!name) {
          const stamp = new Date().toISOString().slice(0, 16).replace("T", " ");
          setName(`${t.name} — ${stamp}`);
        }
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recipeId]);

  const fieldOrder = useMemo(() => template?.fields ?? [], [template]);

  function setField(key: string, value: unknown) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!template) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await runRecipe(recipeId, {
        name,
        fields: values,
        prompt_text: promptText,
      });
      navigate({
        to: "/experiments/$experimentId",
        params: { experimentId: res.experiment_id },
      });
    } catch (e) {
      setSubmitError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (error) {
    return (
      <div className="mx-auto w-full max-w-3xl px-6 py-8">
        <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          Could not load recipe: {error}
        </div>
        <Link
          to="/recipes"
          className="mt-4 inline-block text-sm text-muted-foreground underline"
        >
          ← Back to recipes
        </Link>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="mx-auto w-full max-w-3xl px-6 py-8 text-sm text-muted-foreground">
        Loading…
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-8">
      <Link
        to="/recipes"
        className="mb-4 inline-block text-xs text-muted-foreground hover:text-foreground"
      >
        ← All recipes
      </Link>

      <header className="mb-6">
        <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
          {template.name}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {template.description}
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">Experiment name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        {fieldOrder.map((f) => (
          <RecipeFieldInput
            key={f.key}
            field={f}
            value={values[f.key]}
            onChange={(v) => setField(f.key, v)}
          />
        ))}

        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">
            {template.prompt_field_label}
          </label>
          <textarea
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder={template.prompt_placeholder}
            rows={5}
            className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <p className="text-xs text-muted-foreground">
            This text is sent to GSSP-GS alongside each chunk. It's how you steer
            the model — be specific about the audience, tone, and edge cases.
          </p>
        </div>

        {submitError && (
          <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
            {submitError}
          </div>
        )}

        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center justify-center rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background shadow-sm transition-colors hover:bg-foreground/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Submitting…" : "Run recipe"}
          </button>
          <Link
            to="/recipes"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}

function RecipeFieldInput({
  field,
  value,
  onChange,
}: {
  field: RecipeFieldSchema;
  value: unknown;
  onChange: (v: unknown) => void;
}): React.ReactElement {
  const common = {
    placeholder: field.placeholder ?? undefined,
    required: field.required ?? false,
    className:
      "block w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring",
  } as const;

  function describe() {
    if (!field.description) return null;
    return <p className="text-xs text-muted-foreground">{field.description}</p>;
  }

  switch (field.type) {
    case "integer":
    case "number":
      return (
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">{field.label}</label>
          <input
            {...common}
            type="number"
            step={field.type === "integer" ? 1 : "any"}
            min={field.min ?? undefined}
            max={field.max ?? undefined}
            value={value as number | string | undefined ?? ""}
            onChange={(e) => {
              const v = e.target.value;
              if (v === "") return onChange(undefined);
              onChange(field.type === "integer" ? Number.parseInt(v, 10) : Number.parseFloat(v));
            }}
          />
          {describe()}
        </div>
      );
    case "boolean":
      return (
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={Boolean(value)}
            onChange={(e) => onChange(e.target.checked)}
            className="h-4 w-4 rounded border-input"
          />
          <label className="text-sm text-foreground">{field.label}</label>
        </div>
      );
    case "textarea":
      return (
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">{field.label}</label>
          <textarea
            {...common}
            rows={4}
            value={(value as string | undefined) ?? ""}
            onChange={(e) => onChange(e.target.value)}
          />
          {describe()}
        </div>
      );
    case "select":
      return (
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">{field.label}</label>
          <select
            {...common}
            value={(value as string | undefined) ?? ""}
            onChange={(e) => onChange(e.target.value)}
          >
            <option value="">Select…</option>
            {(field.options ?? []).map((opt) => (
              <option key={String(opt.value)} value={String(opt.value)}>
                {opt.label}
              </option>
            ))}
          </select>
          {describe()}
        </div>
      );
    case "s3_uri":
    case "string":
    default:
      return (
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">{field.label}</label>
          <input
            {...common}
            type="text"
            value={(value as string | undefined) ?? ""}
            onChange={(e) => onChange(e.target.value)}
          />
          {describe()}
        </div>
      );
  }
}
