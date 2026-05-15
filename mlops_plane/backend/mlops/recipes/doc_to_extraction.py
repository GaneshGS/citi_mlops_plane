# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Document → Structured Extraction recipe.

Same pipeline shape as ``doc_to_qa`` but the per-chunk LLM call asks for a
flat JSON object whose keys come from the user-supplied ``fields_csv``
(e.g. ``customer_id,policy_number,effective_date``).
"""

from __future__ import annotations

import json
import random
import time
from typing import Any

from mlops.db.models import DataSourceRole, EventLevel, ExperimentStatus
from mlops.db.repositories import (
    DataSourceRepository,
    ExperimentEventRepository,
    ExperimentRepository,
    LlmInvocationRepository,
)
from mlops.integrations.gssp_client import GsspChatRequest, GsspMessage
from mlops.integrations.s3_client import parse_s3_uri
from mlops.schemas import RecipeFieldSchema, RecipeTemplate

from .base import Recipe, RecipeContext, RecipeStage
from .doc_to_qa import _chunk_text, _decode_to_text, _fail, _load_inputs


TEMPLATE = RecipeTemplate(
    id = "doc_to_extraction",
    name = "Document to Extraction",
    category = "Training Dataset Recipes",
    description = (
        "Extract structured fields from documents in S3 to build a labeled "
        "training set for a fine-tuned extractor model. Output is JSONL "
        "with one row per chunk."
    ),
    fields = [
        RecipeFieldSchema(
            key = "input_s3_uri",
            label = "Input S3 URI (prefix or object)",
            type = "s3_uri",
            required = True,
            placeholder = "s3://citi-mlops-inputs/forms/",
        ),
        RecipeFieldSchema(
            key = "output_s3_uri",
            label = "Output S3 URI (prefix)",
            type = "s3_uri",
            required = True,
            placeholder = "s3://citi-mlops-outputs/runs/doc-to-extraction/",
        ),
        RecipeFieldSchema(
            key = "fields_csv",
            label = "Fields to extract (CSV)",
            type = "string",
            required = True,
            placeholder = "customer_id, policy_number, effective_date, premium_amount",
            description = "Comma-separated list of JSON keys the model should produce.",
        ),
        RecipeFieldSchema(
            key = "chunk_size",
            label = "Chunk size (characters)",
            type = "integer",
            default = 2000,
            min = 200,
            max = 8000,
        ),
        RecipeFieldSchema(
            key = "chunk_overlap",
            label = "Chunk overlap (characters)",
            type = "integer",
            default = 200,
            min = 0,
            max = 2000,
        ),
        RecipeFieldSchema(
            key = "train_test_split",
            label = "Train / test split",
            type = "number",
            default = 0.8,
            min = 0.5,
            max = 0.95,
        ),
        RecipeFieldSchema(
            key = "model",
            label = "GSSP model",
            type = "string",
            default = "gpt-4o-mini",
        ),
        RecipeFieldSchema(
            key = "max_chunks",
            label = "Max chunks (0 = no limit)",
            type = "integer",
            default = 50,
            min = 0,
            max = 5000,
        ),
    ],
    prompt_field_label = "Extraction instructions for GSSP",
    prompt_placeholder = (
        "Extract the listed fields from each document chunk. Use null when "
        "a field is not present. Dates as ISO-8601."
    ),
)


DEFAULT_PROMPT = (
    "You are extracting structured data for a Citi training set.\n\n"
    "Extraction instructions:\n{prompt_text}\n\n"
    "Extract the following fields from the chunk below. Use null when a "
    "field is not present. Return a single JSON object whose keys are "
    "exactly: {fields}.\n\n"
    "Chunk:\n{chunk_text}"
)


class DocumentToExtractionRecipe(Recipe):
    template = TEMPLATE

    async def run(self, ctx: RecipeContext) -> dict[str, Any]:
        return await _execute(ctx)


async def _execute(ctx: RecipeContext) -> dict[str, Any]:
    fields_csv = str(ctx.fields.get("fields_csv", "")).strip()
    field_names = [f.strip() for f in fields_csv.split(",") if f.strip()]
    if not field_names:
        await _fail(ctx, "fields_csv must list at least one field name.")
        return {"status": "failed", "reason": "no_fields"}

    input_uri = str(ctx.fields["input_s3_uri"]).strip()
    output_uri = str(ctx.fields["output_s3_uri"]).strip().rstrip("/") + "/"
    chunk_size = int(ctx.fields.get("chunk_size", 2000))
    chunk_overlap = int(ctx.fields.get("chunk_overlap", 200))
    train_test_split = float(ctx.fields.get("train_test_split", 0.8))
    model = str(ctx.fields.get("model", ctx.gssp.settings.default_model))
    max_chunks = int(ctx.fields.get("max_chunks", 50))

    in_bucket, in_key = parse_s3_uri(input_uri)
    out_bucket, out_prefix = parse_s3_uri(output_uri)

    session_factory = ctx.session_factory

    async with session_factory() as session:
        await ExperimentRepository(session).update_status(
            ctx.experiment_id,
            status = ExperimentStatus.loading_data,
            current_stage = RecipeStage.loading_data.value,
        )
        await ExperimentEventRepository(session).add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.loading_data.value,
            event_type = "stage.started",
            payload = {"input_s3_uri": input_uri, "fields": field_names},
        )
        await session.commit()

    inputs = _load_inputs(ctx, in_bucket, in_key)
    async with session_factory() as session:
        sources = DataSourceRepository(session)
        for bucket, key, body in inputs:
            await sources.add(
                experiment_id = ctx.experiment_id,
                role = DataSourceRole.input,
                s3_bucket = bucket,
                s3_key = key,
                byte_count = len(body),
            )
        await ExperimentEventRepository(session).add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.loading_data.value,
            event_type = "stage.completed",
            payload = {"object_count": len(inputs)},
        )
        await session.commit()

    chunks: list[dict[str, Any]] = []
    for bucket, key, body in inputs:
        text = _decode_to_text(body)
        for idx, ch in enumerate(_chunk_text(text, chunk_size, chunk_overlap)):
            chunks.append(
                {
                    "source_bucket": bucket,
                    "source_key": key,
                    "chunk_index": len(chunks),
                    "chunk_index_in_doc": idx,
                    "text": ch,
                }
            )
            if max_chunks and len(chunks) >= max_chunks:
                break
        if max_chunks and len(chunks) >= max_chunks:
            break

    if not chunks:
        await _fail(ctx, "No chunks produced — check the input URI.")
        return {"status": "failed", "reason": "no_chunks"}

    rows: list[dict[str, Any]] = []
    template = ctx.prompt_template or DEFAULT_PROMPT
    fields_repr = ", ".join(field_names)

    for chunk in chunks:
        rendered = template.format(
            prompt_text = ctx.prompt_text or "(no extraction instructions provided)",
            fields = fields_repr,
            chunk_text = chunk["text"],
        )
        request = GsspChatRequest(
            messages = [GsspMessage(role = "user", content = rendered)],
            model = model,
            response_format = {"type": "json_object"},
        )
        t0 = time.monotonic()
        try:
            response = await ctx.gssp.chat(request)
            status_str = "ok"
            error_message = None
        except Exception as exc:  # noqa: BLE001
            response = None
            status_str = "error"
            error_message = str(exc)
        latency_ms = int((time.monotonic() - t0) * 1000)

        parsed: dict[str, Any] = {}
        if response is not None:
            try:
                parsed = json.loads(response.text)
            except json.JSONDecodeError:
                parsed = {"raw_text": response.text}

        async with session_factory() as session:
            await LlmInvocationRepository(session).add(
                experiment_id = ctx.experiment_id,
                rendered_prompt = rendered,
                model = model,
                params = {"response_format": "json_object"},
                stage = RecipeStage.generating.value,
                chunk_index = chunk["chunk_index"],
                prompt_id = ctx.prompt_id,
                prompt_version = ctx.prompt_version,
                response_text = response.text if response else None,
                response_json = parsed if parsed else None,
                tokens_in = response.tokens_in if response else None,
                tokens_out = response.tokens_out if response else None,
                latency_ms = latency_ms,
                gssp_correlation_id = response.correlation_id if response else None,
                status = status_str,
                error_message = error_message,
            )
            await session.commit()

        if status_str == "ok" and isinstance(parsed, dict):
            row = {f: parsed.get(f) for f in field_names}
            row["source_s3_uri"] = f"s3://{chunk['source_bucket']}/{chunk['source_key']}"
            row["chunk_index"] = chunk["chunk_index"]
            rows.append(row)

    if not rows:
        await _fail(ctx, "GSSP returned no extracted rows.")
        return {"status": "failed", "reason": "no_rows"}

    rng = random.Random(str(ctx.experiment_id))
    rng.shuffle(rows)
    split_idx = max(1, int(len(rows) * train_test_split))
    train_rows = rows[:split_idx]
    test_rows = rows[split_idx:] or rows[-1:]

    train_key = f"{out_prefix.rstrip('/')}/train.jsonl"
    test_key = f"{out_prefix.rstrip('/')}/test.jsonl"
    train_obj = ctx.s3.put_jsonl(out_bucket, train_key, train_rows)
    test_obj = ctx.s3.put_jsonl(out_bucket, test_key, test_rows)

    async with session_factory() as session:
        sources = DataSourceRepository(session)
        await sources.add(
            experiment_id = ctx.experiment_id,
            role = DataSourceRole.train,
            s3_bucket = train_obj.bucket,
            s3_key = train_obj.key,
            byte_count = train_obj.size,
            content_type = train_obj.content_type,
            etag = train_obj.etag,
        )
        await sources.add(
            experiment_id = ctx.experiment_id,
            role = DataSourceRole.test,
            s3_bucket = test_obj.bucket,
            s3_key = test_obj.key,
            byte_count = test_obj.size,
            content_type = test_obj.content_type,
            etag = test_obj.etag,
        )
        await ExperimentEventRepository(session).add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.writing_output.value,
            event_type = "stage.completed",
            level = EventLevel.info,
            payload = {
                "train_s3_uri": train_obj.uri,
                "test_s3_uri": test_obj.uri,
                "train_rows": len(train_rows),
                "test_rows": len(test_rows),
            },
        )
        await ExperimentRepository(session).update_status(
            ctx.experiment_id,
            status = ExperimentStatus.completed,
            current_stage = RecipeStage.writing_output.value,
        )
        await session.commit()

    return {
        "status": "completed",
        "train_s3_uri": train_obj.uri,
        "test_s3_uri": test_obj.uri,
        "train_rows": len(train_rows),
        "test_rows": len(test_rows),
        "chunk_count": len(chunks),
    }
