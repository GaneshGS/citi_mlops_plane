// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { useEffect, useState } from "react";
import { createPrompt, deletePrompt, listPrompts, updatePrompt } from "./api";
import type { PromptOut } from "./types";

const DEFAULT_NEW: { name: string; recipe_type: string; template: string; description: string } = {
  name: "",
  recipe_type: "",
  template: "",
  description: "",
};

export function PromptLibraryPage(): React.ReactElement {
  const [rows, setRows] = useState<PromptOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [draft, setDraft] = useState(DEFAULT_NEW);
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const r = await listPrompts({ only_active: false });
      setRows(r);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await createPrompt({
        name: draft.name.trim(),
        recipe_type: draft.recipe_type.trim() || null,
        template: draft.template,
        description: draft.description || null,
      });
      setDraft(DEFAULT_NEW);
      setCreating(false);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function toggleActive(p: PromptOut) {
    try {
      await updatePrompt(p.id, { is_active: !p.is_active });
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function handleDelete(p: PromptOut) {
    if (!window.confirm(`Delete prompt "${p.name}" v${p.version}?`)) return;
    try {
      await deletePrompt(p.id);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-8">
      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
            Prompt Library
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Versioned, DB-backed prompt templates. Recipes can pin a prompt by
            id + version so re-running an old experiment stays reproducible.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setCreating((v) => !v)}
          className="rounded-md border border-border bg-card px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-accent/30"
        >
          {creating ? "Cancel" : "New prompt"}
        </button>
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </div>
      )}

      {creating && (
        <form
          onSubmit={handleCreate}
          className="mb-6 space-y-3 rounded-md border border-border bg-card p-4"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1">
              <label className="text-sm font-medium">Name</label>
              <input
                value={draft.name}
                onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                required
                className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium">Recipe type (optional)</label>
              <input
                value={draft.recipe_type}
                onChange={(e) => setDraft({ ...draft, recipe_type: e.target.value })}
                placeholder="doc_to_qa, doc_to_extraction, ..."
                className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium">Description</label>
            <input
              value={draft.description}
              onChange={(e) => setDraft({ ...draft, description: e.target.value })}
              className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium">Template</label>
            <textarea
              value={draft.template}
              onChange={(e) => setDraft({ ...draft, template: e.target.value })}
              required
              rows={8}
              className="block w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-xs"
            />
            <p className="text-xs text-muted-foreground">
              Use <code>{"{prompt_text}"}</code>, <code>{"{chunk_text}"}</code>,{" "}
              <code>{"{fields}"}</code> as placeholders depending on the recipe.
            </p>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background hover:bg-foreground/90 disabled:opacity-60"
          >
            {busy ? "Saving…" : "Save"}
          </button>
        </form>
      )}

      {!rows && !error && <div className="text-sm text-muted-foreground">Loading…</div>}

      {rows && rows.length === 0 && (
        <div className="rounded-md border border-dashed border-border px-4 py-8 text-center text-sm text-muted-foreground">
          No prompts saved yet. Recipes will use their built-in defaults.
        </div>
      )}

      {rows && rows.length > 0 && (
        <ul className="space-y-2">
          {rows.map((p) => (
            <li key={p.id} className="rounded-md border border-border bg-card p-3">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium text-foreground">{p.name}</span>
                <span className="text-xs text-muted-foreground">v{p.version}</span>
                {p.recipe_type && (
                  <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
                    {p.recipe_type}
                  </span>
                )}
                <span
                  className={`ml-auto text-xs ${
                    p.is_active ? "text-emerald-600" : "text-muted-foreground"
                  }`}
                >
                  {p.is_active ? "active" : "inactive"}
                </span>
              </div>
              {p.description && (
                <p className="mt-1 text-sm text-muted-foreground">{p.description}</p>
              )}
              <pre className="mt-2 overflow-x-auto rounded bg-muted/40 px-2 py-1 text-[11px] text-muted-foreground">
                {p.template}
              </pre>
              <div className="mt-2 flex gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => toggleActive(p)}
                  className="rounded border border-border bg-background px-2 py-0.5 hover:bg-accent/30"
                >
                  {p.is_active ? "Deactivate" : "Activate"}
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(p)}
                  className="rounded border border-red-300 bg-background px-2 py-0.5 text-red-700 hover:bg-red-50 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950/40"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
