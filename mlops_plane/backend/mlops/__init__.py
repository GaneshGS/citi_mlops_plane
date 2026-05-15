# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane. All rights reserved.

"""Citi MLOps Plane — backend module.

This package owns the MLOps surface for the Citi MLOps Plane:

* PostgreSQL persistence for experiments, events, prompts, data sources,
  LLM invocations, Stellar datasets and fine-tune jobs.
* Integration clients (placeholders) for GSSP-GS (LLM calls), Stellar
  (dataset registration + fine-tuning) and S3 (data load/store).
* Recipe registry + orchestrator (Document-to-Q&A, Document-to-Extraction).
* CRUD route modules mounted under ``/api/mlops``.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
