"""Training runs of a use case, as the loop (flywheel/) records them in
MLflow: a parent run per training run (tag kind=training) and a child run
per brain (kind=iteration), in the use case's experiment
`agent-flywheel-<name>`. A start creates the loop's Job (launcher.py), and
a run whose loop has not reached MLflow yet is read from its Job. Nothing
about a training run is stored here; every call runs as the caller.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .evaluations import Evaluations
from .launcher import Launcher, failure, row_of
from .problems import Invalid, NotFound
from .remote import RemoteError
from .runfiles import RunFiles

MAX_ITERATIONS = 10
DEFAULT_ADJUSTER_MODEL = "enmaas-glm-5-3"  # free on EnMaaS (decision 19)
TRAINING_ID = re.compile(r"[a-z0-9]([-a-z0-9]{0,38}[a-z0-9])?")
BRAIN_FOLDER = "brain"
ADJUSTER_FOLDER = "adjuster"
REPORTS = ("failures.md", "history.md", "change.md", "transcript.md")
PAGE = 1000  # MLflow's largest search page
ADJUSTER_METRICS = ("steps", "tool_calls", "tokens_in", "tokens_out", "cost_usd", "sessions")


class StartTraining(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int | None = Field(default=None, ge=1)  # the current version when left out
    iterations: int = Field(default=3, ge=1, le=MAX_ITERATIONS)
    patience: int = Field(default=2, ge=1, le=MAX_ITERATIONS)
    agent: str | None = Field(default=None, min_length=1)  # eval.yaml's runner when left out
    model: str | None = Field(default=None, min_length=1)
    adjuster_model: str = Field(default=DEFAULT_ADJUSTER_MODEL, min_length=1)


class Trainings:
    def __init__(self, evaluations: Evaluations, launcher: Launcher | None = None):
        self.evaluations = evaluations
        self.registry = evaluations.registry
        self.mlflow = evaluations.mlflow
        self.files = RunFiles(self.mlflow)
        self.launcher = launcher

    def start(self, name: str, request: StartTraining, token: str) -> dict:
        """A training Job for the loop, after every check a start can fail."""
        if self.launcher is None:
            raise HTTPException(501, "starting a training run needs the Job template (FLYWHEEL_TRAINING_JOB)")
        number = request.version or self.registry.get(name)["current"]
        version = self.registry.version(name, number)
        if not version["usecase"].get("adjuster"):
            raise Invalid(f"version {number} of use case {name!r} has no adjuster: block in usecase.yaml, so it cannot be trained")
        if "train" not in version["tasks_per_split"]:
            raise Invalid(f"version {number} of use case {name!r} has no train split to learn from")
        if request.patience > request.iterations:
            raise Invalid(f"patience ({request.patience}) is more than the iterations ({request.iterations})")
        agent, model = self.evaluations.pick(name, number, request.agent, request.model)
        if request.adjuster_model not in self.evaluations.agents.gateway.names():
            raise Invalid(f"the gateway does not route the adjuster model {request.adjuster_model!r}")
        env = {
            "USECASE": name,
            "USECASE_VERSION": str(number),
            "ITERATIONS": str(request.iterations),
            "PATIENCE": str(request.patience),
            "AGENT": agent["name"],
            "MODEL": model,
            "ADJUSTER_MODEL": request.adjuster_model,
        }
        return _public(row_of(self.launcher.start(name, env, token)))

    def list(self, name: str, token: str) -> list[dict]:
        """The use case's training runs, newest first, those still starting included."""
        self.registry.get(name)
        jobs = {job["metadata"]["name"]: job for job in (self.launcher.jobs(name, token) if self.launcher else [])}
        experiment = self._experiment(name, token)
        rows = []
        if experiment is not None:
            parents = self._search(experiment, "tags.kind = 'training'", token)
            children = self._search(experiment, "tags.kind = 'iteration'", token)
            for run in parents:
                row = _training(run, [c for c in children if _tag(c, "training") == _tag(run, "training")])
                rows.append(_with_job(row, jobs.pop(row["id"], None)))
        rows += [row_of(job) for job in jobs.values()]
        rows.sort(key=lambda row: row["started"] or row.get("created") or "", reverse=True)
        return [_public(row) for row in rows]

    def get(self, name: str, training: str, token: str) -> dict:
        """One training run with every brain it made, in order."""
        job = self.launcher.job(name, training, token) if self.launcher and TRAINING_ID.fullmatch(training) else None
        try:
            parent, children = self._runs(name, training, token)
        except NotFound:
            if job is None:
                raise
            return {**_public(row_of(job)), "brains": []}
        return {**_with_job(_training(parent, children), job), "brains": [_brain(run) for run in _ordered(children)]}

    def brain(self, name: str, training: str, number: int, token: str) -> dict:
        """One brain's files and the adjuster's reports of the step that made it."""
        _, children = self._runs(name, training, token)
        run = next((c for c in children if _tag(c, "iteration") == str(number)), None)
        if run is None:
            raise NotFound(f"training run {training!r} has no brain v{number}")
        run_id = run["info"]["run_id"]
        base = self.files.base(run_id, token)
        files = [self._text(base, path, BRAIN_FOLDER, token) for path in self.files.paths(run_id, BRAIN_FOLDER, token)]
        reports = [r for r in (self._report(base, name, token) for name in REPORTS) if r is not None]
        return {"number": number, "files": files, "reports": reports}

    def _runs(self, name: str, training: str, token: str) -> tuple[dict, list[dict]]:
        self.registry.get(name)
        if not TRAINING_ID.fullmatch(training):
            raise NotFound(f"no training run {training!r} of use case {name!r}")
        experiment = self._experiment(name, token)
        runs = self._search(experiment, f"tags.training = '{training}'", token) if experiment else []
        parent = next((r for r in runs if _tag(r, "kind") == "training"), None)
        if parent is None:
            raise NotFound(f"no training run {training!r} of use case {name!r}")
        return parent, [r for r in runs if _tag(r, "kind") == "iteration"]

    def _experiment(self, name: str, token: str) -> str | None:
        query = {"experiment_name": f"agent-flywheel-{name}"}
        try:
            found = self.mlflow.json("GET", "/api/2.0/mlflow/experiments/get-by-name", token, query=query)
        except RemoteError as exc:
            if exc.status == 404:
                return None
            raise
        return found["experiment"]["experiment_id"]

    def _search(self, experiment: str, filter_string: str, token: str) -> list[dict]:
        runs, page = [], None
        while True:
            body = {"experiment_ids": [experiment], "filter": filter_string, "max_results": PAGE}
            if page:
                body["page_token"] = page
            answer = self.mlflow.json("POST", "/api/2.0/mlflow/runs/search", token, body=body) or {}
            runs += answer.get("runs") or []
            page = answer.get("next_page_token")
            if not page:
                return runs

    def _text(self, base: str, path: str, folder: str, token: str) -> dict:
        return {"path": path[len(folder) + 1 :], "text": self.files.read(base, path, token).decode("utf-8", "replace")}

    def _report(self, base: str, name: str, token: str) -> dict | None:
        data = self.files.optional(base, f"{ADJUSTER_FOLDER}/{name}", token)
        return {"path": name, "text": data.decode("utf-8", "replace")} if data is not None else None


def _training(run: Mapping[str, Any], children: list[Mapping[str, Any]]) -> dict:
    info, params = run["info"], _pairs(run, "params")
    brains = [_brain(c) for c in _ordered(children)]
    return {
        "id": _tag(run, "training"),
        "usecase": _tag(run, "usecase"),
        "version": _int(_tag(run, "usecase_version")),
        "state": str(info.get("status") or "").lower() or None,
        "started": _time(info.get("start_time")),
        "ended": _time(info.get("end_time")),
        "iterations": _int(params.get("iterations")),
        "brains_scored": sum(1 for b in brains if b["train"] is not None),
        "best": _best(brains, _tag(run, "best_iteration")),
        "agent": params.get("agent"),
        "model": params.get("model"),
        "adjuster_model": params.get("adjuster_model"),
        "stop_reason": _tag(run, "stop_reason"),
        "error": _tag(run, "error"),
        "mlflow_run_id": info.get("run_id"),
        "mlflow_experiment_id": info.get("experiment_id"),
    }


def _with_job(row: dict, job: Mapping[str, Any] | None) -> dict:
    """A run MLflow still calls running whose Job failed (a killed pod never ends its run) failed."""
    error = failure(job) if job else None
    if error and row["state"] == "running":
        return {**row, "state": "failed", "error": row["error"] or error}
    return row


def _public(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "created"}


def _brain(run: Mapping[str, Any]) -> dict:
    metrics = _metrics(run)
    files = _tag(run, "adjusted_files")
    adjuster = {key: metrics[f"adjuster/{key}"] for key in ADJUSTER_METRICS if f"adjuster/{key}" in metrics}
    return {
        "number": _int(_tag(run, "iteration")),
        "base": _int(_tag(run, "adjust_base")),
        "decision": _tag(run, "decision") or "not decided",
        "train": metrics.get("train/score"),
        "validation": metrics.get("validation/score"),
        "train_judges": _judges(metrics, "train"),
        "validation_judges": _judges(metrics, "validation"),
        "files": [] if files in (None, "none") else files.split(", "),
        "hypothesis": _tag(run, "adjuster_hypothesis") or "",
        "change": _tag(run, "adjuster_change") or "",
        "train_evaluation": _tag(run, "train_evaluation"),
        "validation_evaluation": _tag(run, "validation_evaluation"),
        "adjuster": adjuster or None,
        "mlflow_run_id": run["info"].get("run_id"),
    }


def _best(brains: list[dict], best_iteration: str | None) -> dict | None:
    """The finished run's best brain; while it runs, the last kept or baseline one."""
    if best_iteration is not None:
        chosen = next((b for b in brains if b["number"] == _int(best_iteration)), None)
    else:
        kept = [b for b in brains if b["decision"] in ("baseline", "kept") and b["train"] is not None]
        chosen = kept[-1] if kept else None
    return {key: chosen[key] for key in ("number", "train", "validation")} if chosen else None


def _ordered(children: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return sorted(children, key=lambda c: _int(_tag(c, "iteration")) or 0)


def _judges(metrics: Mapping[str, float], split: str) -> dict[str, float]:
    prefix = f"{split}/"
    return {key[len(prefix) :]: value for key, value in metrics.items() if key.startswith(prefix) and key != f"{split}/score"}


def _pairs(run: Mapping[str, Any], kind: str) -> dict[str, str]:
    return {item["key"]: item.get("value") for item in (run.get("data") or {}).get(kind) or []}


def _tag(run: Mapping[str, Any], key: str) -> str | None:
    return _pairs(run, "tags").get(key)


def _metrics(run: Mapping[str, Any]) -> dict[str, float]:
    return {item["key"]: item["value"] for item in (run.get("data") or {}).get("metrics") or []}


def _int(value: str | None) -> int | None:
    return int(value) if value is not None and str(value).isdigit() else None


def _time(millis: int | str | None) -> str | None:
    if millis in (None, "", 0, "0"):
        return None
    return datetime.fromtimestamp(int(millis) / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
