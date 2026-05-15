# SPDX-License-Identifier: Proprietary
# Copyright 2026-present Citi MLOps Plane.

"""S3 client — minimal load/store interface for the MLOps plane.

The real implementation uses ``boto3``. A dummy mode (default) keeps a
local on-disk store under ``$MLOPS_LOCAL_S3_ROOT`` (default ``/tmp/mlops-s3``)
so recipes can run end-to-end without AWS credentials.

Drop ``S3_USE_DUMMY=0`` plus the standard AWS env vars to go live.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from mlops.config import S3Settings, get_settings


@dataclass
class S3Object:
    bucket: str
    key: str
    body: bytes
    content_type: Optional[str] = None
    etag: Optional[str] = None

    @property
    def size(self) -> int:
        return len(self.body)

    @property
    def uri(self) -> str:
        return f"s3://{self.bucket}/{self.key}"


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Split ``s3://bucket/path/to/key`` into ``(bucket, key)``."""
    if not uri.startswith("s3://"):
        raise ValueError(f"Not an s3:// URI: {uri!r}")
    without_scheme = uri[len("s3://"):]
    if "/" not in without_scheme:
        raise ValueError(f"S3 URI missing key: {uri!r}")
    bucket, _, key = without_scheme.partition("/")
    if not bucket or not key:
        raise ValueError(f"Bad S3 URI: {uri!r}")
    return bucket, key


class S3Client:
    """Read/write S3 objects (or local on-disk shadow when dummy)."""

    def __init__(self, settings: Optional[S3Settings] = None) -> None:
        self._settings = settings or get_settings().s3
        self._local_root = Path(
            os.environ.get("MLOPS_LOCAL_S3_ROOT", "/tmp/mlops-s3")
        )
        self._boto_session = None  # lazy

    @property
    def settings(self) -> S3Settings:
        return self._settings

    # ---------- read ----------

    def get_object(self, bucket: str, key: str) -> S3Object:
        if self._settings.use_dummy:
            path = self._local_root / bucket / key
            if not path.exists():
                raise FileNotFoundError(f"s3://{bucket}/{key} (dummy)")
            data = path.read_bytes()
            return S3Object(
                bucket = bucket,
                key = key,
                body = data,
                content_type = _guess_content_type(key),
                etag = _md5(data),
            )
        client = self._get_boto_s3()
        resp = client.get_object(Bucket = bucket, Key = key)
        body = resp["Body"].read()
        return S3Object(
            bucket = bucket,
            key = key,
            body = body,
            content_type = resp.get("ContentType"),
            etag = resp.get("ETag", "").strip('"') or None,
        )

    def list_objects(self, bucket: str, prefix: str) -> Iterator[dict[str, Any]]:
        if self._settings.use_dummy:
            base = self._local_root / bucket
            if not base.exists():
                return iter([])
            results: list[dict[str, Any]] = []
            for f in base.rglob("*"):
                if not f.is_file():
                    continue
                rel = str(f.relative_to(base))
                if not rel.startswith(prefix):
                    continue
                results.append(
                    {
                        "Key": rel,
                        "Size": f.stat().st_size,
                        "ETag": "",
                    }
                )
            return iter(results)

        client = self._get_boto_s3()
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket = bucket, Prefix = prefix):
            for obj in page.get("Contents", []) or []:
                yield obj

    # ---------- write ----------

    def put_object(
        self,
        bucket: str,
        key: str,
        body: bytes,
        content_type: Optional[str] = None,
    ) -> S3Object:
        if self._settings.use_dummy:
            path = self._local_root / bucket / key
            path.parent.mkdir(parents = True, exist_ok = True)
            path.write_bytes(body)
            return S3Object(
                bucket = bucket,
                key = key,
                body = body,
                content_type = content_type or _guess_content_type(key),
                etag = _md5(body),
            )
        client = self._get_boto_s3()
        kwargs: dict[str, Any] = {
            "Bucket": bucket,
            "Key": key,
            "Body": body,
        }
        if content_type:
            kwargs["ContentType"] = content_type
        resp = client.put_object(**kwargs)
        return S3Object(
            bucket = bucket,
            key = key,
            body = body,
            content_type = content_type,
            etag = (resp.get("ETag") or "").strip('"') or None,
        )

    def put_jsonl(
        self,
        bucket: str,
        key: str,
        rows: Iterable[dict[str, Any]],
    ) -> S3Object:
        buf = "\n".join(json.dumps(r, ensure_ascii = False) for r in rows).encode("utf-8")
        return self.put_object(bucket, key, buf, content_type = "application/jsonl")

    # ---------- boto lazy init ----------

    def _get_boto_s3(self):
        if self._boto_session is None:
            import boto3  # local import — only required for real mode

            self._boto_session = boto3.session.Session(
                aws_access_key_id = self._settings.access_key_id or None,
                aws_secret_access_key = self._settings.secret_access_key or None,
                region_name = self._settings.region,
            )
        return self._boto_session.client(
            "s3",
            endpoint_url = self._settings.endpoint_url or None,
        )


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()  # noqa: S324 — etag-style only


def _guess_content_type(key: str) -> Optional[str]:
    if key.endswith(".jsonl"):
        return "application/jsonl"
    if key.endswith(".json"):
        return "application/json"
    if key.endswith(".txt"):
        return "text/plain"
    if key.endswith(".pdf"):
        return "application/pdf"
    if key.endswith(".csv"):
        return "text/csv"
    return None


_singleton: Optional[S3Client] = None


def get_s3_client() -> S3Client:
    global _singleton
    if _singleton is None:
        _singleton = S3Client()
    return _singleton
