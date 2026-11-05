"""Evaluations of a use case version, run as EvalHub jobs (spec 02 section 4.4).

One job runs C11's benchmark `eval-run` on one version, which EvalHub's init
container copies from the registry's bucket to `/test_data`, on all its
tasks or one split. EvalHub keeps the job, its state and its scores; the
adapter's MLflow run keeps every task's verdicts in `run/summary.yaml`.
Nothing about an evaluation is stored here: the job's tags find a use case's
jobs, and every call runs as the caller (remote.py).
"""

from __future__ import annotations

import logging
import os
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .problems import Invalid, NotFound
from .registry import Registry
from .remote import Remote, RemoteError
from .usecase import EVAL_FILE

log = logging.getLogger(__name__)

JOBS = "/api/v1/evaluations/jobs"
BENCHMARK = "eval-run"  # C11's one benchmark, for any use case
TAG = "agent-flywheel"
PAGE = 100  # EvalHub's largest page
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


class Evaluations:
    def __init__(self, registry: Registry, evalhub: Remote, mlflow: Remote, settings: Settings):
        self.registry = registry
        self.evalhub = evalhub
        self.mlflow = mlflow
        self.settings = settings

    def start(self, name: str, request: StartRequest, token: str) -> dict:
        number = request.version or self.registry.get(name)["current"]
        record = self.registry.record(name, number)
        split = _split(name, record, request.split)
        model = request.model or self._default_model(name, number)
        job = self.evalhub.json("POST", JOBS, token, body=self._job(name, number, split, model))
        log.info("use case %s: version %d, split %s, model %s, job %s", name, number, split, model, job["resource"]["id"])
        return summary(job)

    def list(self, name: str, token: str) -> list[dict]:
        """The use case's jobs, newest first."""
        self.registry.get(name)
        jobs, offset = [], 0
        while True:
            query = {"tags": usecase_tag(name), "limit": PAGE, "offset": offset}
            items = self.evalhub.json("GET", JOBS, token, query=query).get("items") or []
            jobs += items
            if len(items) < PAGE:
                break
            offset += PAGE
        return sorted((summary(job) for job in jobs), key=lambda job: job["created"] or "", reverse=True)

    def get(self, name: str, job_id: str, token: str) -> dict:
        """One job, with each task's reward and verdicts once its MLflow run holds them."""
        job = self.evalhub.json("GET", f"{JOBS}/{urllib.parse.quote(job_id, safe='')}", token)
        if usecase_tag(name) not in (job.get("tags") or []):
            raise NotFound(f"no evaluation {job_id!r} of use case {name!r}")
        result = summary(job)
        result["tasks"], result["tasks_detail"] = self._tasks(result["mlflow_run_id"], token)
        return result

    def _default_model(self, name: str, number: int) -> str:
        config = yaml.safe_load(self.registry.file(name, number, EVAL_FILE)) or {}
        model = (config.get("models") or {}).get("skill")
        if not isinstance(model, str) or not model:
            raise Invalid(f"give a model: {EVAL_FILE} of version {number} names no models.skill")
        return model

    def _job(self, name: str, number: int, split: str | None, model: str) -> dict:
        tags = [TAG, usecase_tag(name), f"version:{number}", *([f"split:{split}"] if split else [])]
        test_data = {
            "s3": {
                "bucket": self.settings.bucket,
                "key": self.registry.version_prefix(name, number),
                "secret_ref": self.settings.secret,
            }
        }
        return {
            "name": f"{name}-v{number}-{split or 'all'}-{model}",
            "tags": tags,
            "model": {"name": model, "url": self.settings.model_url},
            "benchmarks": [
                {
                    "id": BENCHMARK,
                    "provider_id": self.settings.provider,
                    "parameters": {"split": split} if split else {},
                    "test_data_ref": test_data,
                }
            ],
            "experiment": {
                "name": f"{TAG}-{name}",
                "tags": [
                    {"key": "usecase", "value": name},
                    {"key": "usecase_version", "value": str(number)},
                    {"key": "split", "value": split or "all"},
                ],
            },
        }

    def _tasks(self, run_id: str | None, token: str) -> tuple[list[dict] | None, str | None]:
        """Each task's result, or None and why not: the job's scores stand without them."""
        if not run_id:
            return None, "the job has no MLflow run yet"
        try:
            data = self._summary_file(run_id, token)
        except RemoteError as exc:
            log.warning("run %s: %s", run_id, exc)
            return None, str(exc)
        return tasks_of(yaml.safe_load(data) or {}), None

    def _summary_file(self, run_id: str, token: str) -> bytes:
        run = self.mlflow.json("GET", "/api/2.0/mlflow/runs/get", token, query={"run_id": run_id})
        uri = run["run"]["info"]["artifact_uri"]
        if not uri.startswith(ARTIFACTS_SCHEME):
            raise RemoteError(502, f"MLflow keeps run {run_id}'s files at {uri}, which the API cannot read")
        return self.mlflow.raw("GET", f"/api/2.0/mlflow-artifacts/artifacts/{uri[len(ARTIFACTS_SCHEME) :]}/{SUMMARY}", token)


def usecase_tag(name: str) -> str:
    return f"usecase:{name}"


def _split(name: str, record: dict, split: str | None) -> str | None:
    splits = record["tasks_per_split"]
    if split is not None and split not in splits:
        known = ", ".join(splits) or "none"
        raise Invalid(f"version {record['number']} of use case {name!r} has no split {split!r}; its splits: {known}")
    return split


def summary(job: dict) -> dict:
    """An EvalHub job in the API's words: what ran, its state, and its scores."""
    resource = job.get("resource") or {}
    status = job.get("status") or {}
    progress = _first(status.get("benchmarks"))
    results = job.get("results") or {}
    result = _first(results.get("benchmarks"))
    test = results.get("test") or {}
    config = _first(job.get("benchmarks"))
    metrics = result.get("metrics") or {}
    return {
        "id": resource.get("id"),
        "name": job.get("name"),
        "created": resource.get("created_at"),
        "owner": resource.get("owner"),
        "version": _tag_number(job.get("tags") or [], "version"),
        "split": (config.get("parameters") or {}).get("split"),
        "model": (job.get("model") or {}).get("name"),
        "state": status.get("state"),
        "message": (status.get("message") or {}).get("message"),
        "phase": progress.get("phase"),
        "error": (progress.get("error_message") or {}).get("message"),
        "started": progress.get("started_at"),
        "completed": progress.get("completed_at"),
        "reward": metrics.get("reward"),
        "metrics": metrics,
        "passed": test.get("pass"),
        "threshold": test.get("threshold"),
        "mlflow_run_id": result.get("mlflow_run_id"),
    }


def tasks_of(summary_yaml: Mapping[str, Any]) -> list[dict]:
    """Each task's reward and each judge's verdict, from the harness's summary.yaml."""
    rewards = (summary_yaml.get("reward") or {}).get("per_case") or {}
    cases = summary_yaml.get("per_case") or {}
    return [
        {
            "id": case,
            "reward": rewards.get(case),
            "judges": {judge: _verdict(verdict) for judge, verdict in sorted((cases.get(case) or {}).items())},
        }
        for case in sorted(set(cases) | set(rewards))
    ]


def _verdict(verdict: Mapping[str, Any]) -> dict:
    return {key: verdict.get(key) for key in ("value", "rationale", "error")}


def _first(items: list | None) -> dict:
    return items[0] if items else {}


def _tag_number(tags: list[str], key: str) -> int | None:
    for tag in tags:
        prefix, _, value = tag.partition(":")
        if prefix == key and value.isdigit():
            return int(value)
    return None


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
