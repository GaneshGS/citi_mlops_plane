# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""Document → Q&A pair training-dataset recipe.

Pipeline (each stage emits an experiment_event + persists artifacts):

1. Load input objects from ``s3://input_bucket/input_prefix``.
2. Chunk by character count (configurable).
3. For each chunk, prompt GSSP-GS for one (question, answer, evidence) row
   matching the recipe's JSON schema. Each call is recorded as an
   ``llm_invocations`` row.
4. Shuffle deterministically + split into train/test by ``train_test_split``.
5. Write ``train.jsonl`` / ``test.jsonl`` to ``s3://output_bucket/output_prefix``.
6. Mark experiment ``completed`` and emit final summary event.
"""

from __future__ import annotations

import json
import random
import time
import uuid
from typing import Any

from mlops.db.models import (
    DataSourceRole,
    EventLevel,
    ExperimentStatus,
)
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


TEMPLATE = RecipeTemplate(
    id = "doc_to_qa",
    name = "Document to Q&A",
    category = "Training Dataset Recipes",
    description = (
        "Generate question / answer / evidence training pairs from documents "
        "in S3, using GSSP-GS for the heavy lifting. Outputs JSONL ready for "
        "Stellar registration + fine-tuning."
    ),
    fields = [
        RecipeFieldSchema(
            key = "input_s3_uri",
            label = "Input S3 URI (prefix or object)",
            type = "s3_uri",
            required = True,
            placeholder = "s3://citi-mlops-inputs/policies/",
            description = "Either a single object or a prefix containing the source documents.",
        ),
        RecipeFieldSchema(
            key = "output_s3_uri",
            label = "Output S3 URI (prefix)",
            type = "s3_uri",
            required = True,
            placeholder = "s3://citi-mlops-outputs/runs/doc-to-qa/",
            description = "Train/test JSONL will be written under this prefix.",
        ),
        RecipeFieldSchema(
            key = "chunk_size",
            label = "Chunk size (characters)",
            type = "integer",
            default = 1500,
            min = 200,
            max = 8000,
            required = True,
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
            key = "pairs_per_chunk",
            label = "Q&A pairs per chunk",
            type = "integer",
            default = 1,
            min = 1,
            max = 5,
        ),
        RecipeFieldSchema(
            key = "train_test_split",
            label = "Train / test split",
            type = "number",
            default = 0.8,
            min = 0.5,
            max = 0.95,
            description = "Fraction of pairs that go into the train set.",
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
            description = "Safety cap for early experiments.",
        ),
    ],
    prompt_field_label = "Use-case description (sent to GSSP)",
    prompt_placeholder = (
        "We're fine-tuning a model to answer policy questions for branch "
        "operations. Generate concise factual Q&A pairs with verbatim "
        "evidence quotes from each chunk."
    ),
)


# Default prompt template used when the user does not pick a saved prompt.
DEFAULT_PROMPT = (
    "You are generating supervised fine-tuning data for a Citi internal "
    "model.\n\n"
    "Use-case description:\n{prompt_text}\n\n"
    "Given ONLY the chunk below, generate one question that is fully "
    "answerable from the chunk, the answer, and a verbatim evidence quote.\n\n"
    "Chunk:\n{chunk_text}\n\n"
    "Respond as a JSON object with keys: question, answer, evidence_quote."
)


class DocumentToQARecipe(Recipe):
    template = TEMPLATE

    async def run(self, ctx: RecipeContext) -> dict[str, Any]:
        return await _execute(ctx)


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------


async def _execute(ctx: RecipeContext) -> dict[str, Any]:
    input_uri = str(ctx.fields["input_s3_uri"]).strip()
    output_uri = str(ctx.fields["output_s3_uri"]).strip().rstrip("/") + "/"
    chunk_size = int(ctx.fields.get("chunk_size", 1500))
    chunk_overlap = int(ctx.fields.get("chunk_overlap", 200))
    pairs_per_chunk = int(ctx.fields.get("pairs_per_chunk", 1))
    train_test_split = float(ctx.fields.get("train_test_split", 0.8))
    model = str(ctx.fields.get("model", ctx.gssp.settings.default_model))
    max_chunks = int(ctx.fields.get("max_chunks", 50))

    in_bucket, in_key = parse_s3_uri(input_uri)
    out_bucket, out_prefix = parse_s3_uri(output_uri)

    session_factory = ctx.session_factory

    # ---- Stage 1: load ----------------------------------------------------
    async with session_factory() as session:
        events = ExperimentEventRepository(session)
        sources = DataSourceRepository(session)
        experiments = ExperimentRepository(session)
        await experiments.update_status(
            ctx.experiment_id,
            status = ExperimentStatus.loading_data,
            current_stage = RecipeStage.loading_data.value,
        )
        await events.add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.loading_data.value,
            event_type = "stage.started",
            message = f"Loading input from {input_uri}",
            payload = {"input_s3_uri": input_uri},
        )
        await session.commit()

    inputs: list[tuple[str, str, bytes]] = _load_inputs(ctx, in_bucket, in_key)

    async with session_factory() as session:
        events = ExperimentEventRepository(session)
        sources = DataSourceRepository(session)
        for bucket, key, body in inputs:
            await sources.add(
                experiment_id = ctx.experiment_id,
                role = DataSourceRole.input,
                s3_bucket = bucket,
                s3_key = key,
                byte_count = len(body),
                content_type = "application/octet-stream",
            )
        await events.add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.loading_data.value,
            event_type = "stage.completed",
            message = f"Loaded {len(inputs)} object(s)",
            payload = {"object_count": len(inputs)},
        )
        await session.commit()

    # ---- Stage 2: chunk ---------------------------------------------------
    async with session_factory() as session:
        events = ExperimentEventRepository(session)
        await ExperimentRepository(session).update_status(
            ctx.experiment_id,
            status = ExperimentStatus.preparing_dataset,
            current_stage = RecipeStage.chunking.value,
        )
        await events.add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.chunking.value,
            event_type = "stage.started",
            payload = {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
        )
        await session.commit()

    chunks: list[dict[str, Any]] = []
    for bucket, key, body in inputs:
        text = _decode_to_text(body)
        for idx, chunk in enumerate(_chunk_text(text, chunk_size, chunk_overlap)):
            chunks.append(
                {
                    "source_bucket": bucket,
                    "source_key": key,
                    "chunk_index": len(chunks),
                    "chunk_index_in_doc": idx,
                    "text": chunk,
                }
            )
            if max_chunks and len(chunks) >= max_chunks:
                break
        if max_chunks and len(chunks) >= max_chunks:
            break

    async with session_factory() as session:
        events = ExperimentEventRepository(session)
        await events.add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.chunking.value,
            event_type = "stage.completed",
            message = f"Produced {len(chunks)} chunks",
            payload = {"chunk_count": len(chunks)},
        )
        await session.commit()

    if not chunks:
        await _fail(ctx, "No chunks produced — check the input URI.")
        return {"status": "failed", "reason": "no_chunks"}

    # ---- Stage 3: generate Q&A pairs --------------------------------------
    async with session_factory() as session:
        events = ExperimentEventRepository(session)
        await events.add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.generating.value,
            event_type = "stage.started",
            payload = {"chunks": len(chunks), "pairs_per_chunk": pairs_per_chunk},
        )
        await session.commit()

    rows: list[dict[str, Any]] = []
    template = ctx.prompt_template or DEFAULT_PROMPT

    for chunk in chunks:
        for _ in range(pairs_per_chunk):
            rendered = template.format(
                prompt_text = ctx.prompt_text or "(no use-case description provided)",
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
            except Exception as exc:  # noqa: BLE001 — recorded explicitly
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
                inv_repo = LlmInvocationRepository(session)
                await inv_repo.add(
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

            if status_str == "ok" and isinstance(parsed, dict) and parsed.get("question"):
                rows.append(
                    {
                        "question": parsed.get("question"),
                        "answer": parsed.get("answer"),
                        "evidence_quote": parsed.get("evidence_quote"),
                        "source_s3_uri": f"s3://{chunk['source_bucket']}/{chunk['source_key']}",
                        "chunk_index": chunk["chunk_index"],
                    }
                )

    async with session_factory() as session:
        events = ExperimentEventRepository(session)
        await events.add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.generating.value,
            event_type = "stage.completed",
            message = f"Generated {len(rows)} Q&A pairs",
            payload = {"row_count": len(rows)},
        )
        await session.commit()

    if not rows:
        await _fail(ctx, "GSSP returned no usable Q&A pairs.")
        return {"status": "failed", "reason": "no_rows"}

    # ---- Stage 4: split + write ------------------------------------------
    rng = random.Random(str(ctx.experiment_id))
    rng.shuffle(rows)
    split_idx = max(1, int(len(rows) * train_test_split))
    train_rows = rows[:split_idx]
    test_rows = rows[split_idx:] or rows[-1:]  # always ship at least one test row

    train_key = f"{out_prefix.rstrip('/')}/train.jsonl"
    test_key = f"{out_prefix.rstrip('/')}/test.jsonl"

    train_obj = ctx.s3.put_jsonl(out_bucket, train_key, train_rows)
    test_obj = ctx.s3.put_jsonl(out_bucket, test_key, test_rows)

    async with session_factory() as session:
        sources = DataSourceRepository(session)
        events = ExperimentEventRepository(session)
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
        await events.add(
            experiment_id = ctx.experiment_id,
            stage = RecipeStage.writing_output.value,
            event_type = "stage.completed",
            message = f"Wrote {len(train_rows)} train + {len(test_rows)} test rows",
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


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _load_inputs(ctx: RecipeContext, bucket: str, key_or_prefix: str) -> list[tuple[str, str, bytes]]:
    """Load every object under the prefix (or the single object)."""
    out: list[tuple[str, str, bytes]] = []
    try:
        obj = ctx.s3.get_object(bucket, key_or_prefix)
        out.append((obj.bucket, obj.key, obj.body))
        return out
    except FileNotFoundError:
        pass
    except Exception:  # noqa: BLE001
        # boto raises ClientError; fall through to listing
        pass

    for entry in ctx.s3.list_objects(bucket, key_or_prefix):
        try:
            obj = ctx.s3.get_object(bucket, entry["Key"])
            out.append((obj.bucket, obj.key, obj.body))
        except Exception:  # noqa: BLE001 — skip unreadable objects
            continue
    return out


def _decode_to_text(body: bytes) -> str:
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body.decode("utf-8", errors = "replace")


def _chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0:
        return [text]
    overlap = max(0, min(overlap, size - 1))
    step = size - overlap
    chunks: list[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + size])
        if i + size >= len(text):
            break
        i += step
    return chunks


async def _fail(ctx: RecipeContext, reason: str) -> None:
    async with ctx.session_factory() as session:
        await ExperimentRepository(session).update_status(
            ctx.experiment_id,
            status = ExperimentStatus.failed,
            error_message = reason,
        )
        await ExperimentEventRepository(session).add(
            experiment_id = ctx.experiment_id,
            stage = "failure",
            event_type = "experiment.failed",
            level = EventLevel.error,
            message = reason,
        )
        await session.commit()
