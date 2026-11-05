"""Evaluations of a use case version, run as EvalHub jobs (spec 02 section 4.4).

One job runs C11's benchmark `eval-run` on one version, which EvalHub's init
container copies from the registry's bucket to `/test_data`, on all its
tasks or one split. EvalHub keeps the job, its state and its scores; the
adapter's MLflow run keeps the harness's `run/summary.yaml`, with every
task's verdicts and the threshold verdicts. Nothing about an evaluation is
stored here: the job's tags find a use case's jobs, and every call runs as
the caller (remote.py).

Caches of what never changes: a version's eval.yaml and record, and the
summary.yaml of a job that has ended.
"""

from __future__ import annotations

import logging
import os
import threading
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from . import results
from .problems import Invalid, NotFound
from .registry import Registry
from .remote import Remote, RemoteError
from .usecase import EVAL_FILE

log = logging.getLogger(__name__)

JOBS = "/api/v1/evaluations/jobs"
BENCHMARK = "eval-run"  # C11's one benchmark, for any use case
TAG = "agent-flywheel"
PAGE = 100  # EvalHub's largest page
CACHE_SIZE = 512
# Where the adapter puts the harness's run folder in its MLflow run (C11).
SUMMARY = "run/summary.yaml"
ARTIFACTS_SCHEME = "mlflow-artifacts:/"


@dataclass(frozen=True)
class Settings:
    provider: str  # C11's provider, mounted into EvalHub (deploy/platform/evalhub/)
    bucket: str  # the registry's bucket
    secret: str  # the Secret EvalHub's init container reads the bucket with
    model_url: str  # the gateway the agents reach their model through


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int | None = Field(default=None, ge=1)  # the current version when left out
    split: str | None = Field(default=None, min_length=1)  # every task when left out
    model: str | None = Field(default=None, min_length=1)  # eval.yaml's models.skill when left out


class _Cache:
    """A bounded map for values that never change once known."""

    def __init__(self, size: int = CACHE_SIZE):
        self._items: dict = {}
        self._size = size
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            return self._items.get(key)

    def put(self, key, value) -> None:
        with self._lock:
            if len(self._items) >= self._size:
                self._items.clear()
            self._items[key] = value


class Evaluations:
    def __init__(self, registry: Registry, evalhub: Remote, mlflow: Remote, settings: Settings):
        self.registry = registry
        self.evalhub = evalhub
        self.mlflow = mlflow
        self.settings = settings
        self._configs = _Cache()
        self._records = _Cache()
        self._summaries = _Cache()

    def start(self, name: str, request: StartRequest, token: str) -> dict:
        number = request.version or self.registry.get(name)["current"]
        record = self.registry.record(name, number)
        split = _split(name, record, request.split)
        config = self._eval_config(name, number)
        model = request.model or _default_model(config, number)
        job = self.evalhub.json("POST", JOBS, token, body=self._job(name, number, split, model, config))
        log.info("use case %s: version %d, split %s, model %s, job %s", name, number, split, model, job["resource"]["id"])
        return self._read(name, job, token)[0]

    def list(self, name: str, token: str) -> list[dict]:
        """The use case's jobs, newest first, each with its threshold verdicts once it has ended."""
        self.registry.get(name)
        jobs, offset = [], 0
        while True:
            query = {"tags": usecase_tag(name), "limit": PAGE, "offset": offset}
            items = self.evalhub.json("GET", JOBS, token, query=query).get("items") or []
            jobs += items
            if len(items) < PAGE:
                break
            offset += PAGE
        rows = (self._read(name, job, token)[0] for job in jobs)
        return sorted(rows, key=lambda row: row["created"] or "", reverse=True)

    def get(self, name: str, job_id: str, token: str) -> dict:
        """One job, with its judges, every task's verdicts and the threshold verdicts."""
        row, config, summary_yaml = self._read(name, self._job_of(name, job_id, token), token)
        row["judges"] = results.judges_of(config, summary_yaml or {})
        row["tasks"] = results.tasks_of(summary_yaml, results.judge_names(config)) if summary_yaml else None
        return row

    def stop(self, name: str, job_id: str, token: str, *, delete: bool) -> None:
        """Cancel a job, or with *delete* remove it and its record from EvalHub.
        Its MLflow run stays."""
        self._job_of(name, job_id, token)
        self.evalhub.raw("DELETE", _job_path(job_id), token, query={"hard_delete": str(delete).lower()})
        log.info("use case %s: job %s %s", name, job_id, "deleted" if delete else "cancelled")

    def logs(self, name: str, job_id: str, token: str) -> str:
        """The job's pod logs, as EvalHub has them: none once its pods are gone."""
        self._job_of(name, job_id, token)
        return self.evalhub.raw("GET", f"{_job_path(job_id)}/logs", token, accept="text/plain").decode("utf-8", "replace")

    def _job_of(self, name: str, job_id: str, token: str) -> dict:
        job = self.evalhub.json("GET", _job_path(job_id), token)
        if usecase_tag(name) not in (job.get("tags") or []):
            raise NotFound(f"no evaluation {job_id!r} of use case {name!r}")
        return job

    def _read(self, name: str, job: Mapping[str, Any], token: str) -> tuple[dict, dict, dict | None]:
        """The job's row (its summary, agent, task count and threshold
        verdicts), its version's eval.yaml, and its summary.yaml once MLflow has it."""
        row = results.summary(job)
        config = self._eval_config(name, row["version"]) if row["version"] else {}
        row["agent"] = (config.get("runner") or {}).get("type")
        row["task_count"] = self._task_count(name, row["version"], row["split"]) if row["version"] else None
        summary_yaml, row["tasks_detail"] = self._summary_yaml(row, token)
        row["thresholds"] = results.thresholds_of(summary_yaml) if summary_yaml else None
        return row, config, summary_yaml

    def _summary_yaml(self, row: Mapping[str, Any], token: str) -> tuple[dict | None, str | None]:
        """summary.yaml, or None and why not: the job's scores stand without it."""
        run_id = row["mlflow_run_id"]
        if not run_id:
            return None, "the job has no MLflow run yet"
        if (cached := self._summaries.get(run_id)) is not None:
            return cached, None
        try:
            data = yaml.safe_load(self._summary_file(run_id, token)) or {}
        except RemoteError as exc:
            log.warning("run %s: %s", run_id, exc)
            return None, str(exc)
        if results.is_final(row):
            self._summaries.put(run_id, data)
        return data, None

    def _summary_file(self, run_id: str, token: str) -> bytes:
        run = self.mlflow.json("GET", "/api/2.0/mlflow/runs/get", token, query={"run_id": run_id})
        uri = run["run"]["info"]["artifact_uri"]
        if not uri.startswith(ARTIFACTS_SCHEME):
            raise RemoteError(502, f"MLflow keeps run {run_id}'s files at {uri}, which the API cannot read")
        return self.mlflow.raw("GET", f"/api/2.0/mlflow-artifacts/artifacts/{uri[len(ARTIFACTS_SCHEME) :]}/{SUMMARY}", token)

    def _task_count(self, name: str, number: int, split: str | None) -> int | None:
        """How many tasks the job ran: the split's, or every task of the version."""
        key = (name, number)
        if (record := self._records.get(key)) is None:
            record = self.registry.record(name, number)
            self._records.put(key, record)
        return record["tasks_per_split"].get(split) if split else record["task_count"]

    def _eval_config(self, name: str, number: int) -> dict:
        """A version's eval.yaml, which never changes."""
        key = (name, number)
        if (cached := self._configs.get(key)) is None:
            cached = yaml.safe_load(self.registry.file(name, number, EVAL_FILE)) or {}
            self._configs.put(key, cached)
        return cached

    def _job(self, name: str, number: int, split: str | None, model: str, config: Mapping[str, Any]) -> dict:
        tags = [TAG, usecase_tag(name), f"version:{number}", *([f"split:{split}"] if split else [])]
        test_data = {
            "s3": {
                "bucket": self.settings.bucket,
                "key": self.registry.version_prefix(name, number),
                "secret_ref": self.settings.secret,
            }
        }
        benchmark = {
            "id": BENCHMARK,
            "provider_id": self.settings.provider,
            "parameters": {"split": split} if split else {},
            "test_data_ref": test_data,
        }
        job: dict[str, Any] = {
            "name": f"{name}-v{number}-{split or 'all'}-{model}",
            "tags": tags,
            "model": {"name": model, "url": self.settings.model_url},
            "benchmarks": [benchmark],
            "experiment": {
                "name": f"{TAG}-{name}",
                "tags": [
                    {"key": "usecase", "value": name},
                    {"key": "usecase_version", "value": str(number)},
                    {"key": "split", "value": split or "all"},
                ],
            },
        }
        # EvalHub's own verdict (results.test) takes the job's pass criteria, else
        # 0.5 (evaluations_results.go, getPassCriteriaThreshold): give it the use
        # case's mean-reward rule, the first rule of the module's release gate.
        min_mean = ((config.get("thresholds") or {}).get("reward") or {}).get("min_mean")
        if isinstance(min_mean, int | float) and not isinstance(min_mean, bool):
            job["pass_criteria"] = {"threshold": min_mean}
        return job


def usecase_tag(name: str) -> str:
    return f"usecase:{name}"


def _job_path(job_id: str) -> str:
    return f"{JOBS}/{urllib.parse.quote(job_id, safe='')}"


def _split(name: str, record: dict, split: str | None) -> str | None:
    splits = record["tasks_per_split"]
    if split is not None and split not in splits:
        known = ", ".join(splits) or "none"
        raise Invalid(f"version {record['number']} of use case {name!r} has no split {split!r}; its splits: {known}")
    return split


def _default_model(config: Mapping[str, Any], number: int) -> str:
    model = (config.get("models") or {}).get("skill")
    if not isinstance(model, str) or not model:
        raise Invalid(f"give a model: {EVAL_FILE} of version {number} names no models.skill")
    return model


def evaluations_from_env(registry: Registry, env: Mapping[str, str] = os.environ) -> Evaluations | None:
    """EVALHUB_URL turns evaluations on; without it the API serves the registry alone.

    MLFLOW_URL, FLYWHEEL_NAMESPACE (the tenant and the MLflow workspace) and
    BUCKET_NAME are then required; FLYWHEEL_CA_FILE verifies both services'
    certificates (the cluster's service CA).
    """
    evalhub_url = env.get("EVALHUB_URL")
    if not evalhub_url:
        log.warning("evaluations: off, no EVALHUB_URL")
        return None
    missing = [key for key in ("MLFLOW_URL", "FLYWHEEL_NAMESPACE", "BUCKET_NAME") if not env.get(key)]
    if missing:
        raise RuntimeError(f"evaluations need {', '.join(missing)} beside EVALHUB_URL")
    namespace, ca_file = env["FLYWHEEL_NAMESPACE"], env.get("FLYWHEEL_CA_FILE")
    evalhub = Remote("EvalHub", evalhub_url, ca_file=ca_file, headers={"X-Tenant": namespace})
    mlflow = Remote("MLflow", env["MLFLOW_URL"], ca_file=ca_file, headers={"X-MLflow-Workspace": namespace})
    settings = Settings(
        provider=env.get("FLYWHEEL_EVALHUB_PROVIDER", "agent-eval-harness"),
        bucket=env["BUCKET_NAME"],
        secret=env.get("FLYWHEEL_BUCKET_SECRET", "flywheel-usecases"),
        model_url=env.get("FLYWHEEL_MODEL_URL", f"http://gateway.{namespace}.svc:4000/v1"),
    )
    log.info("evaluations: EvalHub %s, MLflow %s, provider %s", evalhub_url, env["MLFLOW_URL"], settings.provider)
    return Evaluations(registry, evalhub, mlflow, settings)
