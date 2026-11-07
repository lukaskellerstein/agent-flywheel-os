"""The files of an MLflow run, read through MLflow's artifact proxy as the
caller: an evaluation's run folder (evaluations.py) and a training run's
brains and adjuster reports (trainings.py)."""

from __future__ import annotations

import json
from typing import Any

from .remote import Remote, RemoteError

ARTIFACTS_SCHEME = "mlflow-artifacts:/"


class RunFiles:
    def __init__(self, mlflow: Remote):
        self.mlflow = mlflow

    def base(self, run_id: str, token: str) -> str:
        """The run's artifact folder on MLflow's artifact proxy."""
        run = self.mlflow.json("GET", "/api/2.0/mlflow/runs/get", token, query={"run_id": run_id})
        uri = run["run"]["info"]["artifact_uri"]
        if not uri.startswith(ARTIFACTS_SCHEME):
            raise RemoteError(502, f"MLflow keeps run {run_id}'s files at {uri}, which the API cannot read")
        return uri[len(ARTIFACTS_SCHEME) :]

    def paths(self, run_id: str, folder: str, token: str, skip: frozenset[str] = frozenset()) -> list[str]:
        """Every file under *folder* in the run, those named in *skip* left out."""
        query = {"run_id": run_id, "path": folder}
        listing = self.mlflow.json("GET", "/api/2.0/mlflow/artifacts/list", token, query=query) or {}
        found = []
        for entry in listing.get("files") or []:
            if entry.get("is_dir"):
                found += self.paths(run_id, entry["path"], token, skip)
            elif entry["path"].rsplit("/", 1)[-1] not in skip:
                found.append(entry["path"])
        return found

    def read(self, base: str, path: str, token: str) -> bytes:
        return self.mlflow.raw("GET", f"/api/2.0/mlflow-artifacts/artifacts/{base}/{path}", token)

    def optional(self, base: str, path: str, token: str) -> bytes | None:
        try:
            return self.read(base, path, token)
        except RemoteError as exc:
            if exc.status == 404:
                return None
            raise

    def optional_json(self, base: str, path: str, token: str) -> Any:
        data = self.optional(base, path, token)
        return json.loads(data) if data is not None else None
