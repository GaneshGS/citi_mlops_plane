"""Initial schema for Citi MLOps plane.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-15

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


EXPERIMENT_STATUS = sa.Enum(
    "pending",
    "loading_data",
    "preparing_dataset",
    "registering_dataset",
    "submitted_finetune",
    "training",
    "completed",
    "failed",
    "cancelled",
    name = "experiment_status",
)
EVENT_LEVEL = sa.Enum("info", "warn", "error", name = "event_level")
DATA_SOURCE_ROLE = sa.Enum(
    "input", "chunked", "train", "test", "output", "artifact",
    name = "data_source_role",
)
STELLAR_DATASET_ROLE = sa.Enum(
    "train", "test", "validation", name = "stellar_dataset_role"
)
FINETUNE_STATUS = sa.Enum(
    "pending", "queued", "running", "succeeded", "failed", "cancelled",
    name = "finetune_status",
)


def upgrade() -> None:
    bind = op.get_bind()
    EXPERIMENT_STATUS.create(bind, checkfirst = True)
    EVENT_LEVEL.create(bind, checkfirst = True)
    DATA_SOURCE_ROLE.create(bind, checkfirst = True)
    STELLAR_DATASET_ROLE.create(bind, checkfirst = True)
    FINETUNE_STATUS.create(bind, checkfirst = True)

    op.create_table(
        "prompts",
        sa.Column("id", postgresql.UUID(as_uuid = True), primary_key = True),
        sa.Column("name", sa.String(length = 128), nullable = False),
        sa.Column("version", sa.Integer(), nullable = False, server_default = "1"),
        sa.Column("recipe_type", sa.String(length = 64), nullable = True),
        sa.Column("template", sa.Text(), nullable = False),
        sa.Column("variables", postgresql.JSONB(astext_type = sa.Text()), nullable = False, server_default = "[]"),
        sa.Column("description", sa.Text(), nullable = True),
        sa.Column("is_active", sa.Boolean(), nullable = False, server_default = sa.true()),
        sa.Column("created_by", sa.String(length = 64), nullable = True),
        sa.Column("extra", postgresql.JSONB(astext_type = sa.Text()), nullable = False, server_default = "{}"),
        sa.Column("created_at", sa.DateTime(timezone = True), nullable = False),
        sa.Column("updated_at", sa.DateTime(timezone = True), nullable = False),
        sa.UniqueConstraint("name", "version", name = "uq_prompts_name_version"),
    )
    op.create_index("ix_prompts_name", "prompts", ["name"])
    op.create_index("ix_prompts_recipe_type", "prompts", ["recipe_type"])

    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid = True), primary_key = True),
        sa.Column("name", sa.String(length = 255), nullable = False),
        sa.Column("recipe_type", sa.String(length = 64), nullable = False),
        sa.Column("owner_soeid", sa.String(length = 64), nullable = True),
        sa.Column("status", EXPERIMENT_STATUS, nullable = False, server_default = "pending"),
        sa.Column("current_stage", sa.String(length = 64), nullable = True),
        sa.Column("config", postgresql.JSONB(astext_type = sa.Text()), nullable = False, server_default = "{}"),
        sa.Column(
            "prompt_id",
            postgresql.UUID(as_uuid = True),
            sa.ForeignKey("prompts.id", ondelete = "SET NULL"),
            nullable = True,
        ),
        sa.Column("error_message", sa.Text(), nullable = True),
        sa.Column("is_deleted", sa.Boolean(), nullable = False, server_default = sa.false()),
        sa.Column("created_at", sa.DateTime(timezone = True), nullable = False),
        sa.Column("updated_at", sa.DateTime(timezone = True), nullable = False),
    )
    op.create_index("ix_experiments_recipe_type", "experiments", ["recipe_type"])
    op.create_index("ix_experiments_status", "experiments", ["status"])

    op.create_table(
        "experiment_events",
        sa.Column("id", postgresql.UUID(as_uuid = True), primary_key = True),
        sa.Column(
            "experiment_id",
            postgresql.UUID(as_uuid = True),
            sa.ForeignKey("experiments.id", ondelete = "CASCADE"),
            nullable = False,
        ),
        sa.Column("stage", sa.String(length = 64), nullable = False),
        sa.Column("event_type", sa.String(length = 64), nullable = False),
        sa.Column("level", EVENT_LEVEL, nullable = False, server_default = "info"),
        sa.Column("message", sa.Text(), nullable = True),
        sa.Column("payload", postgresql.JSONB(astext_type = sa.Text()), nullable = False, server_default = "{}"),
        sa.Column("created_at", sa.DateTime(timezone = True), nullable = False),
    )
    op.create_index("ix_experiment_events_experiment_id", "experiment_events", ["experiment_id"])
    op.create_index("ix_experiment_events_stage", "experiment_events", ["stage"])
    op.create_index("ix_experiment_events_created_at", "experiment_events", ["created_at"])

    op.create_table(
        "data_sources",
        sa.Column("id", postgresql.UUID(as_uuid = True), primary_key = True),
        sa.Column(
            "experiment_id",
            postgresql.UUID(as_uuid = True),
            sa.ForeignKey("experiments.id", ondelete = "CASCADE"),
            nullable = False,
        ),
        sa.Column("role", DATA_SOURCE_ROLE, nullable = False),
        sa.Column("s3_bucket", sa.String(length = 255), nullable = False),
        sa.Column("s3_key", sa.Text(), nullable = False),
        sa.Column("byte_count", sa.BigInteger(), nullable = True),
        sa.Column("etag", sa.String(length = 128), nullable = True),
        sa.Column("content_type", sa.String(length = 128), nullable = True),
        sa.Column("registered_at", sa.DateTime(timezone = True), nullable = False),
    )
    op.create_index("ix_data_sources_experiment_id", "data_sources", ["experiment_id"])
    op.create_index("ix_data_sources_role", "data_sources", ["role"])

    op.create_table(
        "llm_invocations",
        sa.Column("id", postgresql.UUID(as_uuid = True), primary_key = True),
        sa.Column(
            "experiment_id",
            postgresql.UUID(as_uuid = True),
            sa.ForeignKey("experiments.id", ondelete = "CASCADE"),
            nullable = False,
        ),
        sa.Column(
            "prompt_id",
            postgresql.UUID(as_uuid = True),
            sa.ForeignKey("prompts.id", ondelete = "SET NULL"),
            nullable = True,
        ),
        sa.Column("prompt_version", sa.Integer(), nullable = True),
        sa.Column("stage", sa.String(length = 64), nullable = True),
        sa.Column("chunk_index", sa.Integer(), nullable = True),
        sa.Column("rendered_prompt", sa.Text(), nullable = False),
        sa.Column("model", sa.String(length = 128), nullable = False),
        sa.Column("params", postgresql.JSONB(astext_type = sa.Text()), nullable = False, server_default = "{}"),
        sa.Column("response_text", sa.Text(), nullable = True),
        sa.Column("response_json", postgresql.JSONB(astext_type = sa.Text()), nullable = True),
        sa.Column("tokens_in", sa.Integer(), nullable = True),
        sa.Column("tokens_out", sa.Integer(), nullable = True),
        sa.Column("latency_ms", sa.Integer(), nullable = True),
        sa.Column("gssp_correlation_id", sa.String(length = 128), nullable = True),
        sa.Column("status", sa.String(length = 32), nullable = False, server_default = "ok"),
        sa.Column("error_message", sa.Text(), nullable = True),
        sa.Column("created_at", sa.DateTime(timezone = True), nullable = False),
    )
    op.create_index("ix_llm_invocations_experiment_id", "llm_invocations", ["experiment_id"])
    op.create_index("ix_llm_invocations_stage", "llm_invocations", ["stage"])
    op.create_index("ix_llm_invocations_created_at", "llm_invocations", ["created_at"])

    op.create_table(
        "stellar_datasets",
        sa.Column("id", postgresql.UUID(as_uuid = True), primary_key = True),
        sa.Column(
            "experiment_id",
            postgresql.UUID(as_uuid = True),
            sa.ForeignKey("experiments.id", ondelete = "CASCADE"),
            nullable = False,
        ),
        sa.Column("role", STELLAR_DATASET_ROLE, nullable = False),
        sa.Column("stellar_dataset_id", sa.String(length = 255), nullable = False),
        sa.Column("source_s3_uri", sa.Text(), nullable = True),
        sa.Column("byte_count", sa.BigInteger(), nullable = True),
        sa.Column("row_count", sa.BigInteger(), nullable = True),
        sa.Column("extra", postgresql.JSONB(astext_type = sa.Text()), nullable = False, server_default = "{}"),
        sa.Column("registered_at", sa.DateTime(timezone = True), nullable = False),
    )
    op.create_index("ix_stellar_datasets_experiment_id", "stellar_datasets", ["experiment_id"])
    op.create_index("ix_stellar_datasets_stellar_dataset_id", "stellar_datasets", ["stellar_dataset_id"])

    op.create_table(
        "finetune_jobs",
        sa.Column("id", postgresql.UUID(as_uuid = True), primary_key = True),
        sa.Column(
            "experiment_id",
            postgresql.UUID(as_uuid = True),
            sa.ForeignKey("experiments.id", ondelete = "CASCADE"),
            nullable = False,
        ),
        sa.Column("stellar_job_id", sa.String(length = 255), nullable = True),
        sa.Column("train_stellar_dataset_id", sa.String(length = 255), nullable = True),
        sa.Column("test_stellar_dataset_id", sa.String(length = 255), nullable = True),
        sa.Column("base_model", sa.String(length = 255), nullable = True),
        sa.Column("hyperparams", postgresql.JSONB(astext_type = sa.Text()), nullable = False, server_default = "{}"),
        sa.Column("status", FINETUNE_STATUS, nullable = False, server_default = "pending"),
        sa.Column("submitted_at", sa.DateTime(timezone = True), nullable = True),
        sa.Column("finished_at", sa.DateTime(timezone = True), nullable = True),
        sa.Column("result_model_uri", sa.Text(), nullable = True),
        sa.Column("error_message", sa.Text(), nullable = True),
        sa.Column("created_at", sa.DateTime(timezone = True), nullable = False),
        sa.Column("updated_at", sa.DateTime(timezone = True), nullable = False),
    )
    op.create_index("ix_finetune_jobs_experiment_id", "finetune_jobs", ["experiment_id"])
    op.create_index("ix_finetune_jobs_stellar_job_id", "finetune_jobs", ["stellar_job_id"])
    op.create_index("ix_finetune_jobs_status", "finetune_jobs", ["status"])

    op.create_table(
        "finetune_status_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid = True), primary_key = True),
        sa.Column(
            "finetune_job_id",
            postgresql.UUID(as_uuid = True),
            sa.ForeignKey("finetune_jobs.id", ondelete = "CASCADE"),
            nullable = False,
        ),
        sa.Column("status", sa.String(length = 64), nullable = False),
        sa.Column("metrics", postgresql.JSONB(astext_type = sa.Text()), nullable = False, server_default = "{}"),
        sa.Column("raw_payload", postgresql.JSONB(astext_type = sa.Text()), nullable = True),
        sa.Column("captured_at", sa.DateTime(timezone = True), nullable = False),
    )
    op.create_index("ix_finetune_status_snapshots_finetune_job_id", "finetune_status_snapshots", ["finetune_job_id"])
    op.create_index("ix_finetune_status_snapshots_captured_at", "finetune_status_snapshots", ["captured_at"])


def downgrade() -> None:
    op.drop_table("finetune_status_snapshots")
    op.drop_table("finetune_jobs")
    op.drop_table("stellar_datasets")
    op.drop_table("llm_invocations")
    op.drop_table("data_sources")
    op.drop_table("experiment_events")
    op.drop_table("experiments")
    op.drop_table("prompts")

    bind = op.get_bind()
    FINETUNE_STATUS.drop(bind, checkfirst = True)
    STELLAR_DATASET_ROLE.drop(bind, checkfirst = True)
    DATA_SOURCE_ROLE.drop(bind, checkfirst = True)
    EVENT_LEVEL.drop(bind, checkfirst = True)
    EXPERIMENT_STATUS.drop(bind, checkfirst = True)
