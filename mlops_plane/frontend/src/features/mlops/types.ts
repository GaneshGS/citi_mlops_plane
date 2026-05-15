// SPDX-License-Identifier: Proprietary
// Copyright 2026-present Citi MLOps Plane.

/** TypeScript counterparts to the Pydantic schemas in studio/backend/mlops. */

export type RecipeFieldType =
  | "string"
  | "integer"
  | "number"
  | "boolean"
  | "select"
  | "textarea"
  | "s3_uri";

export interface RecipeFieldSchema {
  key: string;
  label: string;
  type: RecipeFieldType;
  description?: string | null;
  required?: boolean;
  default?: unknown;
  placeholder?: string | null;
  options?: Array<{ value: unknown; label: string }> | null;
  min?: number | null;
  max?: number | null;
}

export interface RecipeTemplate {
  id: string;
  name: string;
  category: string;
  description: string;
  fields: RecipeFieldSchema[];
  prompt_field_label: string;
  prompt_placeholder: string;
}

export interface RecipeRunRequest {
  name: string;
  fields: Record<string, unknown>;
  prompt_text: string;
  prompt_id?: string | null;
  owner_soeid?: string | null;
}

export interface RecipeRunResponse {
  experiment_id: string;
  status: string;
  detail_url: string;
}

export type ExperimentStatus =
  | "pending"
  | "loading_data"
  | "preparing_dataset"
  | "registering_dataset"
  | "submitted_finetune"
  | "training"
  | "completed"
  | "failed"
  | "cancelled";

export interface ExperimentSummary {
  id: string;
  name: string;
  recipe_type: string;
  owner_soeid: string | null;
  status: ExperimentStatus;
  current_stage: string | null;
  config: Record<string, unknown>;
  prompt_id: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export type EventLevel = "info" | "warn" | "error";

export interface ExperimentEvent {
  id: string;
  experiment_id: string;
  stage: string;
  event_type: string;
  level: EventLevel;
  message: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface ExperimentDataSource {
  id: string;
  role: string;
  s3_bucket: string;
  s3_key: string;
  byte_count: number | null;
  content_type: string | null;
  registered_at: string;
}

export interface ExperimentDetail extends ExperimentSummary {
  events: ExperimentEvent[];
  data_sources: ExperimentDataSource[];
}

export interface PromptOut {
  id: string;
  name: string;
  version: number;
  recipe_type: string | null;
  template: string;
  variables: string[];
  description: string | null;
  is_active: boolean;
  created_by: string | null;
  extra: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface PromptCreate {
  name: string;
  template: string;
  version?: number;
  recipe_type?: string | null;
  variables?: string[];
  description?: string | null;
  created_by?: string | null;
  extra?: Record<string, unknown>;
}

export interface PromptUpdate {
  template?: string;
  description?: string | null;
  is_active?: boolean;
  variables?: string[];
}
