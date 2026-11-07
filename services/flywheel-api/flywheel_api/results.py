"""An evaluation's results in the API's words: the EvalHub job, and the
harness's `summary.yaml` that the adapter logs to MLflow (C11), read with the
version's `eval.yaml`.

The verdicts are the harness's (C20): `thresholds` as `summary.yaml` holds
them, every check with its target, limit, value and verdict. Nothing here
judges again.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# EvalHub's final states (pkg/api/evaluations.go, IsTerminalState).
FINAL_STATES = frozenset({"completed", "failed", "cancelled", "partially_failed"})
JUDGE_AGGREGATES = ("mean", "pass_rate", "scored_cases", "errored_cases")


def summary(job: Mapping[str, Any]) -> dict:
    """An EvalHub job: what ran, its state, and EvalHub's scores."""
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
        "mlflow_experiment_id": resource.get("mlflow_experiment_id"),
    }


def is_final(job_summary: Mapping[str, Any]) -> bool:
    return job_summary.get("state") in FINAL_STATES


def judge_names(eval_config: Mapping[str, Any]) -> list[str]:
    return [judge["name"] for judge in eval_config.get("judges") or []]


def judges_of(eval_config: Mapping[str, Any], summary_yaml: Mapping[str, Any]) -> list[dict]:
    """Each judge in eval.yaml's order: what it checks, its weight in the
    reward, and its aggregates over the tasks of this run."""
    weights = (eval_config.get("reward") or {}).get("weights") or {}
    aggregates = summary_yaml.get("judges") or {}
    return [
        {
            "name": judge["name"],
            "description": judge.get("description"),
            "weight": weights.get(judge["name"]),
            **{key: (aggregates.get(judge["name"]) or {}).get(key) for key in JUDGE_AGGREGATES},
        }
        for judge in eval_config.get("judges") or []
    ]


def tasks_of(summary_yaml: Mapping[str, Any], order: list[str] | None = None) -> list[dict]:
    """Each task's reward and each judge's verdict, the judges in *order*
    (eval.yaml's) and any other judge after them by name."""
    rewards = (summary_yaml.get("reward") or {}).get("per_case") or {}
    cases = summary_yaml.get("per_case") or {}
    return [
        {"id": case, "reward": rewards.get(case), "judges": _verdicts(cases.get(case) or {}, order or [])}
        for case in sorted(set(cases) | set(rewards))
    ]


def task_of(summary_yaml: Mapping[str, Any], task_id: str, order: list[str]) -> dict | None:
    """One task's reward and judges' verdicts in a run, or None when the run did not have it."""
    return next((task for task in tasks_of(summary_yaml, order) if task["id"] == task_id), None)


def thresholds_of(summary_yaml: Mapping[str, Any]) -> dict | None:
    """The harness's threshold verdicts, or None when eval.yaml has no thresholds."""
    block = summary_yaml.get("thresholds")
    if not isinstance(block, Mapping):
        return None
    return {"passed": block.get("passed"), "checks": list(block.get("checks") or [])}


def _verdicts(verdicts: Mapping[str, Any], order: list[str]) -> dict:
    names = [name for name in order if name in verdicts] + sorted(set(verdicts) - set(order))
    return {name: {key: verdicts[name].get(key) for key in ("value", "rationale", "error")} for name in names}


def _first(items: list | None) -> dict:
    return items[0] if items else {}


def tag_value(tags: list[str], key: str) -> str | None:
    for tag in tags:
        prefix, _, value = tag.partition(":")
        if prefix == key and value:
            return value
    return None


def _tag_number(tags: list[str], key: str) -> int | None:
    value = tag_value(tags, key)
    return int(value) if value is not None and value.isdigit() else None
