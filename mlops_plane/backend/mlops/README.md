# Citi MLOps Plane — backend module

This package implements the Citi MLOps Plane on top of legacy
Studio backend. It is intentionally self-contained: nothing outside
`studio/backend/mlops/` (other than `main.py`, which mounts the router) needs
to be touched to add or modify MLOps features.

## Layout

```
mlops/
├── config.py                       Central, env-driven settings (DB, GSSP, Stellar, S3).
├── db/
│   ├── session.py                  Async SQLAlchemy engine + session factory.
│   ├── base.py                     Declarative base + shared mixins.
│   ├── models/                     ORM models — Experiment, ExperimentEvent, Prompt,
│   │                               DataSource, LlmInvocation, StellarDataset,
│   │                               FinetuneJob, FinetuneStatusSnapshot.
│   └── repositories/               Typed CRUD helpers per table.
├── integrations/
│   ├── gssp_client.py              GSSP-GS LLM client (dummy + real modes).
│   ├── stellar_client.py           Stellar dataset register / fine-tune / status.
│   └── s3_client.py                S3 read/write (boto3 or local on-disk shadow).
├── recipes/
│   ├── base.py                     Recipe base class + RecipeContext.
│   ├── registry.py                 Recipe registry — add new recipes here.
│   ├── runner.py                   Top-level orchestrator (background task).
│   ├── doc_to_qa.py                Document-to-Q&A recipe.
│   └── doc_to_extraction.py        Document-to-Extraction recipe.
├── schemas/                        Pydantic API I/O schemas.
└── routes/
    ├── experiments.py              CRUD + timeline + data sources + LLM invocations.
    ├── prompts.py                  Versioned prompt library CRUD.
    ├── recipes.py                  Template gallery + recipe run.
    └── finetune.py                 Stellar submit + status poll.
```

All routers are mounted by `mlops/routes/__init__.py` under `/api/mlops` and
included from the top-level `studio/backend/main.py`.

## Bring up

```bash
# 1. Start Postgres (root of repo).
docker compose up -d

# 2. Install Python deps.
pip install -r studio/backend/mlops/requirements.txt

# 3. Apply migrations.
cd studio/backend
alembic -c alembic_mlops.ini upgrade head

# 4. Start the API.
uvicorn main:app --reload
```

## Switching from placeholder to real integrations

Edit `.env`:

* `GSSP_USE_DUMMY=0` + `GSSP_BASE_URL` + `GSSP_AUTH_TOKEN` + `GSSP_SOEID`
* `STELLAR_USE_DUMMY=0` + `STELLAR_BASE_URL` + `STELLAR_AUTH_TOKEN`
* `S3_USE_DUMMY=0` + standard `AWS_*` env vars + `MLOPS_S3_*_BUCKET`

The clients pick this up the next time the process starts — nothing in the
recipes, routes or DB layer needs to change.
