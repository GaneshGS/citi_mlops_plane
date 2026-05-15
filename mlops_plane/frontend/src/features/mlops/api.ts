// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

import { apiUrl } from "@/lib/api-base";
import { getAuthToken } from "@/features/auth";
import type {
  ExperimentDetail,
  ExperimentEvent,
  ExperimentSummary,
  PromptCreate,
  PromptOut,
  PromptUpdate,
  RecipeRunRequest,
  RecipeRunResponse,
  RecipeTemplate,
} from "./types";

function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(apiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ---------- recipes ----------

export function listRecipeTemplates(): Promise<RecipeTemplate[]> {
  return request("/api/mlops/recipes");
}

export function getRecipeTemplate(recipeId: string): Promise<RecipeTemplate> {
  return request(`/api/mlops/recipes/${recipeId}`);
}

export function runRecipe(
  recipeId: string,
  body: RecipeRunRequest,
): Promise<RecipeRunResponse> {
  return request(`/api/mlops/recipes/${recipeId}/run`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ---------- experiments ----------

export function listExperiments(params: {
  recipe_type?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<ExperimentSummary[]> {
  const search = new URLSearchParams();
  if (params.recipe_type) search.set("recipe_type", params.recipe_type);
  if (params.limit != null) search.set("limit", String(params.limit));
  if (params.offset != null) search.set("offset", String(params.offset));
  const qs = search.toString();
  return request(`/api/mlops/experiments${qs ? `?${qs}` : ""}`);
}

export function getExperiment(experimentId: string): Promise<ExperimentDetail> {
  return request(`/api/mlops/experiments/${experimentId}`);
}

export function listExperimentEvents(
  experimentId: string,
): Promise<ExperimentEvent[]> {
  return request(`/api/mlops/experiments/${experimentId}/events`);
}

export function deleteExperiment(experimentId: string): Promise<void> {
  return request(`/api/mlops/experiments/${experimentId}`, { method: "DELETE" });
}

// ---------- prompts ----------

export function listPrompts(params: {
  recipe_type?: string;
  only_active?: boolean;
} = {}): Promise<PromptOut[]> {
  const search = new URLSearchParams();
  if (params.recipe_type) search.set("recipe_type", params.recipe_type);
  if (params.only_active != null) search.set("only_active", String(params.only_active));
  const qs = search.toString();
  return request(`/api/mlops/prompts${qs ? `?${qs}` : ""}`);
}

export function createPrompt(body: PromptCreate): Promise<PromptOut> {
  return request("/api/mlops/prompts", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function updatePrompt(promptId: string, body: PromptUpdate): Promise<PromptOut> {
  return request(`/api/mlops/prompts/${promptId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function deletePrompt(promptId: string): Promise<void> {
  return request(`/api/mlops/prompts/${promptId}`, { method: "DELETE" });
}
