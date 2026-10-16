"""Where the registry keeps its files: one S3 bucket, or a folder with the same
layout for local runs and tests.

On the cluster the bucket is the ObjectBucketClaim `flywheel-usecases`
(`deploy/bucket/`). NooBaa answers it with a ConfigMap (BUCKET_HOST,
BUCKET_PORT, BUCKET_NAME, BUCKET_REGION) and a Secret (AWS_ACCESS_KEY_ID,
AWS_SECRET_ACCESS_KEY), which the pod reads as env. boto3 reads the key from
env itself: this module never touches it, and nothing logs it.
"""

from __future__ import annotations

import logging
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)


class Store(Protocol):
    def get(self, key: str) -> bytes | None: ...

    def put(self, key: str, data: bytes) -> None: ...

    def keys(self, prefix: str) -> list[str]:
        """Every key under *prefix*, sorted."""
        ...

    def folders(self, prefix: str) -> list[str]:
        """The names one level under *prefix* (which ends with '/'), sorted."""
        ...

    def delete(self, key: str) -> None: ...


class FileStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def get(self, key: str) -> bytes | None:
        path = self._path(key)
        return path.read_bytes() if path.is_file() else None

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Written beside and renamed, so a reader never sees half a file.
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".put-")
        with os.fdopen(fd, "wb") as out:
            out.write(data)
        os.replace(tmp, path)

    def keys(self, prefix: str) -> list[str]:
        base = self._path(prefix.rstrip("/")) if prefix.rstrip("/") else self.root
        if not base.is_dir():
            return []
        files = (p for p in base.rglob("*") if p.is_file() and not p.name.startswith(".put-"))
        return sorted(p.relative_to(self.root).as_posix() for p in files)

    def folders(self, prefix: str) -> list[str]:
        base = self._path(prefix.rstrip("/"))
        return sorted(p.name for p in base.iterdir() if p.is_dir()) if base.is_dir() else []

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"key {key!r} leaves the store")
        return path


class S3Store:
    def __init__(self, client, bucket: str):
        self.client = client
        self.bucket = bucket

    def get(self, key: str) -> bytes | None:
        try:
            return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("NoSuchKey", "404"):
                return None
            raise

    def put(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def keys(self, prefix: str) -> list[str]:
        pages = self.client.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=prefix)
        return sorted(item["Key"] for page in pages for item in page.get("Contents", []))

    def folders(self, prefix: str) -> list[str]:
        pages = self.client.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=prefix, Delimiter="/")
        names = (p["Prefix"][len(prefix) :].rstrip("/") for page in pages for p in page.get("CommonPrefixes", []))
        return sorted(names)

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


def store_from_env(env: Mapping[str, str] = os.environ) -> Store:
    """FLYWHEEL_STORE_DIR for a folder; else the bucket the claim's ConfigMap names."""
    if folder := env.get("FLYWHEEL_STORE_DIR"):
        log.info("store: the folder %s", folder)
        return FileStore(Path(folder))
    bucket = env.get("BUCKET_NAME")
    if not bucket:
        raise RuntimeError("set BUCKET_NAME (the bucket claim's ConfigMap) or FLYWHEEL_STORE_DIR")
    endpoint = s3_endpoint(env)
    log.info("store: the bucket %s at %s", bucket, endpoint or "AWS S3")
    return S3Store(s3_client(endpoint, env.get("BUCKET_REGION") or "us-east-1"), bucket)


def s3_endpoint(env: Mapping[str, str]) -> str | None:
    """S3_ENDPOINT_URL first; else BUCKET_HOST and BUCKET_PORT, https only on 443; else AWS."""
    if url := env.get("S3_ENDPOINT_URL"):
        return url
    host = env.get("BUCKET_HOST")
    if not host:
        return None
    port = env.get("BUCKET_PORT") or "443"
    return f"{'https' if port == '443' else 'http'}://{host}:{port}"


def s3_client(endpoint: str | None, region: str):
    config = Config(
        s3={"addressing_style": "path"},
        retries={"max_attempts": 5, "mode": "standard"},
        # boto3 sends a CRC checksum with every upload by default since 1.36;
        # S3-compatible stores such as NooBaa may not accept it.
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    )
    return boto3.client("s3", endpoint_url=endpoint, region_name=region, config=config)
