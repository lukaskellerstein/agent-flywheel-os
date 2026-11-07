"""Training Jobs on the cluster: the loop of flywheel/, started as the caller.

The Job is deploy/flywheel/training-job.yaml, mounted into the API from the
ConfigMap `flywheel-training-job`; the launcher sets its use case, its
settings and a label, and creates it through the Kubernetes API with the
caller's token. So only a caller who may create Jobs in the namespace can
start a training run, and the API holds no right of its own for it. The
Job runs as the loop's own ServiceAccount, flywheel-loop.
"""

from __future__ import annotations

import copy
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from .remote import Remote, RemoteError

log = logging.getLogger(__name__)

USECASE_LABEL = "agent-flywheel/usecase"
SA_CA = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
# What the loop's env says, as a training row names it (flywheel_loop/__main__.py).
ROW_ENV = {"agent": "AGENT", "model": "MODEL", "adjuster_model": "ADJUSTER_MODEL"}


class Launcher:
    def __init__(self, kube: Remote, namespace: str, template: Mapping[str, Any]):
        self.kube = kube
        self.namespace = namespace
        self.template = template
        self._jobs = f"/apis/batch/v1/namespaces/{namespace}/jobs"

    def start(self, usecase: str, env: Mapping[str, str], token: str) -> dict:
        """Create the Job; its generated name is the training run's id."""
        job = copy.deepcopy(dict(self.template))
        metadata = job.setdefault("metadata", {})
        metadata["namespace"] = self.namespace
        metadata.setdefault("labels", {})[USECASE_LABEL] = usecase
        container = job["spec"]["template"]["spec"]["containers"][0]
        kept = [item for item in container.get("env") or [] if item["name"] not in env]
        container["env"] = kept + [{"name": key, "value": value} for key, value in env.items()]
        created = self.kube.json("POST", self._jobs, token, body=job)
        log.info("use case %s: training Job %s", usecase, created["metadata"]["name"])
        return created

    def jobs(self, usecase: str, token: str) -> list[dict]:
        """The use case's training Jobs; none when the caller may not list Jobs."""
        try:
            answer = self.kube.json("GET", self._jobs, token, query={"labelSelector": f"{USECASE_LABEL}={usecase}"})
        except RemoteError as exc:
            if exc.status in (401, 403):
                log.warning("training Jobs of %s: %s", usecase, exc)
                return []
            raise
        return answer.get("items") or []

    def job(self, usecase: str, name: str, token: str) -> dict | None:
        try:
            job = self.kube.json("GET", f"{self._jobs}/{name}", token)
        except RemoteError as exc:
            if exc.status in (401, 403, 404):
                return None
            raise
        return job if (job.get("metadata", {}).get("labels") or {}).get(USECASE_LABEL) == usecase else None


def failure(job: Mapping[str, Any]) -> str | None:
    """Why the Job failed, or None while it has not."""
    for condition in (job.get("status") or {}).get("conditions") or []:
        if condition.get("type") == "Failed" and condition.get("status") == "True":
            return condition.get("message") or condition.get("reason") or "the training Job failed"
    return None


def row_of(job: Mapping[str, Any]) -> dict:
    """A training row for a Job whose loop has not reached MLflow."""
    env = {item["name"]: item.get("value") for item in job["spec"]["template"]["spec"]["containers"][0].get("env") or []}
    error = failure(job)
    return {
        "id": job["metadata"]["name"],
        "usecase": env.get("USECASE"),
        "version": int(env["USECASE_VERSION"]) if (env.get("USECASE_VERSION") or "").isdigit() else None,
        "state": "failed" if error else "starting",
        "started": None,
        "ended": None,
        "iterations": int(env["ITERATIONS"]) if (env.get("ITERATIONS") or "").isdigit() else None,
        "brains_scored": 0,
        "best": None,
        **{key: env.get(var) for key, var in ROW_ENV.items()},
        "stop_reason": None,
        "error": error,
        "mlflow_run_id": None,
        "mlflow_experiment_id": None,
        "created": job["metadata"].get("creationTimestamp"),  # when it was started, before MLflow knows it
    }


def launcher_from_env(env: Mapping[str, str] = os.environ) -> Launcher | None:
    """FLYWHEEL_TRAINING_JOB, the Job template's path, turns training starts on."""
    path = env.get("FLYWHEEL_TRAINING_JOB")
    if not path or not Path(path).is_file():
        log.warning("training starts: off, no Job template at %r", path)
        return None
    kube = Remote("Kubernetes", env.get("KUBERNETES_URL", "https://kubernetes.default.svc"), ca_file=env.get("KUBERNETES_CA_FILE", SA_CA))
    return Launcher(kube, env.get("FLYWHEEL_NAMESPACE", "agent-flywheel"), yaml.safe_load(Path(path).read_text()))
