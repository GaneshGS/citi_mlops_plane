# Citi MLOps Plane

> Internal, enterprise MLOps platform for building fine-tuning datasets,
> orchestrating fine-tunes through Stellar, and recording every step against
> a PostgreSQL experiment store.

The Citi MLOps Plane is a FastAPI service plus a React/TypeScript web UI.
It does **not** run models locally. Every model inference call routes through
**GSSP-GS**, every fine-tune submission routes through **Stellar**, and every
piece of data flows through **S3**. The plane itself owns:

- A versioned recipe registry (Document-to-Q&A, Document-to-Extraction, …).
- An experiments database — every recipe run mints an `experiment_id` that
  threads through stage events, S3 data sources, LLM invocations, Stellar
  dataset registrations, fine-tune jobs and status snapshots.
- A versioned prompt library so dataset-build runs stay reproducible.
- CRUD APIs on every persisted entity.

## Layout

```
mlops_plane/
├── backend/                FastAPI service
│   ├── main.py             App entry + router registration
│   ├── auth/               JWT auth + admin bootstrap
│   ├── loggers/            Structured logging
│   ├── routes/             Legacy UI route stubs (return 503 until wired)
│   ├── alembic_mlops/      Alembic migrations for the MLOps plane DB
│   ├── alembic_mlops.ini
│   └── mlops/              The MLOps feature module
│       ├── config.py       Env-driven settings (DB, GSSP, Stellar, S3)
│       ├── db/             SQLAlchemy models + repositories
│       ├── integrations/   GSSP / Stellar / S3 clients
│       ├── recipes/        Recipe registry + orchestrator
│       ├── routes/         REST API under /api/mlops
│       └── schemas/        Pydantic I/O models
└── frontend/               React 19 + Next + TanStack Router + Tailwind
    ├── index.html
    ├── package.json
    └── src/
        ├── app/            Router, root layout, route registrations
        ├── components/     Sidebar, dialogs, primitives
        └── features/
            ├── mlops/      Recipes / Experiments / Prompt Library pages
            ├── chat/       Chat with Model (to be wired to GSSP)
            ├── training/   Training Monitor (to be wired to Stellar)
            ├── finetune/   Compare Models / Finetune (to be wired)
            ├── auth/
            ├── onboarding/
            └── profile/
```

## Local development

```bash
# 1. Postgres
docker compose up -d

# 2. Backend
pip install -r mlops_plane/backend/mlops/requirements.txt
cd mlops_plane/backend
alembic -c alembic_mlops.ini upgrade head
uvicorn main:app --reload

# 3. Frontend (in another shell)
cd mlops_plane/frontend
npm install
npm run dev
```

Open the printed URL and sign in with the bootstrap admin credentials emitted
on first start.

## Environment

All external endpoints, secrets and bucket names are read from environment
variables. See `.env.example` at the repository root for the full list. To
switch from local dummy clients to real Citi infrastructure, set each
`*_USE_DUMMY=0` and provide the real `*_BASE_URL` / `*_AUTH_TOKEN`:

| Service     | Toggle              | URL var             | Token var            |
| ----------- | ------------------- | ------------------- | -------------------- |
| GSSP-GS     | `GSSP_USE_DUMMY`    | `GSSP_BASE_URL`     | `GSSP_AUTH_TOKEN`    |
| Stellar     | `STELLAR_USE_DUMMY` | `STELLAR_BASE_URL`  | `STELLAR_AUTH_TOKEN` |
| S3          | `S3_USE_DUMMY`      | `S3_ENDPOINT_URL`   | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` |

## License

Proprietary. © 2026-present Citi. All rights reserved.
