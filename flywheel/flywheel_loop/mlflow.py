"""MLflow's REST API, the part a training run writes: an experiment, runs
with tags, params and metrics, and artifact folders.

ODH's MLflow serves one workspace per namespace and refuses a call without
the `X-MLflow-Workspace` header (docs/research.md), so the Http client
carries it. Artifacts go through MLflow's artifact proxy, the same path the
flywheel API reads them from.
"""

from __future__ import annotations

import time
import urllib.parse
from collections.abc import Mapping
from pathlib import Path

from . import FlywheelError
from .http import Http, HttpError

ARTIFACTS_SCHEME = "mlflow-artifacts:/"
# MLflow's limits: a tag value 8000 characters, a param value 6000.
TAG_LIMIT = 5000


def _now_ms() -> int:
    return int(time.time() * 1000)


class MLflow:
    def __init__(self, http: Http):
        self.http = http

    def experiment(self, name: str) -> str:
        """The experiment's id, created when it does not exist yet."""
        try:
            found = self.http.json("GET", "/api/2.0/mlflow/experiments/get-by-name", query={"experiment_name": name})
            return found["experiment"]["experiment_id"]
        except HttpError as exc:
            if exc.status != 404:
                raise
        return self.http.json("POST", "/api/2.0/mlflow/experiments/create", body={"name": name})["experiment_id"]

    def start_run(self, experiment_id: str, name: str, tags: Mapping[str, str]) -> str:
        body = {
            "experiment_id": experiment_id,
            "run_name": name,
            "start_time": _now_ms(),
            "tags": _pairs(tags),
        }
        return self.http.json("POST", "/api/2.0/mlflow/runs/create", body=body)["run"]["info"]["run_id"]

    def log(
        self,
        run_id: str,
        *,
        metrics: Mapping[str, float] | None = None,
        params: Mapping[str, str] | None = None,
        tags: Mapping[str, str] | None = None,
    ) -> None:
        stamp = _now_ms()
        body = {
            "run_id": run_id,
            "metrics": [{"key": k, "value": float(v), "timestamp": stamp, "step": 0} for k, v in (metrics or {}).items()],
            "params": _pairs(params or {}),
            "tags": _pairs(tags or {}),
        }
        self.http.json("POST", "/api/2.0/mlflow/runs/log-batch", body=body)

    def end_run(self, run_id: str, status: str = "FINISHED") -> None:
        body = {"run_id": run_id, "status": status, "end_time": _now_ms()}
        self.http.json("POST", "/api/2.0/mlflow/runs/update", body=body)

    def upload(self, run_id: str, folder: Path, artifact_path: str) -> None:
        """Every file under *folder*, at artifact_path/<its path in folder>."""
        base = self._artifact_base(run_id)
        for path in sorted(p for p in folder.rglob("*") if p.is_file()):
            relative = f"{artifact_path}/{path.relative_to(folder).as_posix()}"
            route = f"/api/2.0/mlflow-artifacts/artifacts/{base}/{urllib.parse.quote(relative)}"
            self.http.raw("PUT", route, path.read_bytes(), content_type="application/octet-stream")

    def _artifact_base(self, run_id: str) -> str:
        run = self.http.json("GET", "/api/2.0/mlflow/runs/get", query={"run_id": run_id})
        uri = run["run"]["info"]["artifact_uri"]
        if not uri.startswith(ARTIFACTS_SCHEME):
            raise FlywheelError(f"MLflow keeps run {run_id}'s files at {uri}, which the loop cannot write")
        return uri[len(ARTIFACTS_SCHEME) :].strip("/")


def _pairs(values: Mapping[str, object]) -> list[dict]:
    return [{"key": key, "value": str(value)[:TAG_LIMIT]} for key, value in values.items()]
