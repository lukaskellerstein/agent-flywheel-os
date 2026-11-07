"""One training run: score brain v0, then adjust the best brain, score the
new one, and keep it or revert, until the iterations run out or too many
steps in a row brought no better brain.

Keep or revert is on the train score only (openshift-eval `controller.py`
`decide()`): keep when it is at least the best one's. The validation split
never decides; it shows whether a gain carries over.

MLflow, in the use case's experiment (the one its evaluations log to): one
parent run for the training run, and one child run per brain with the
brain as its artifact folder `brain/` (what C11 applies), the adjuster's
reports and transcript under `adjuster/`, the scores per split and judge,
the evaluations' ids, and the decision.
"""

from __future__ import annotations

import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import FlywheelError
from . import brain as brains
from . import report
from .adjust import Adjusted, Adjuster, Words
from .api import FlywheelAPI
from .mlflow import MLflow
from .report import Iteration

TRAIN, VALIDATION = "train", "validation"
BRAIN_FOLDER = "brain"


@dataclass(frozen=True)
class Plan:
    usecase: str
    training: str  # the training run's id, a DNS label
    version: int | None = None  # the current version when None
    iterations: int = 3  # adjust steps after brain v0
    patience: int = 2  # stop after this many steps in a row with no better brain
    agent: str | None = None  # AI hub › Agents; eval.yaml's runner when None
    model: str | None = None
    poll_s: float = 15
    evaluation_timeout_s: float = 5400


class Training:
    def __init__(self, plan: Plan, api: FlywheelAPI, mlflow: MLflow, adjuster: Adjuster):
        self.plan = plan
        self.api = api
        self.mlflow = mlflow
        self.adjuster = adjuster
        self.iterations: list[Iteration] = []

    def run(self) -> Iteration:
        """The best brain; every record is in MLflow."""
        plan = self.plan
        self.version = self.api.version(plan.usecase, plan.version)
        self.words = Words.of(self.version["usecase"])
        if TRAIN not in self.version["tasks_per_split"]:
            raise FlywheelError(f"version {self.version['number']} of {plan.usecase} has no train split to learn from")
        self.experiment = self.mlflow.experiment(f"agent-flywheel-{plan.usecase}")
        self.parent = self.mlflow.start_run(self.experiment, f"training {plan.training}", self._tags(kind="training"))
        self.mlflow.log(self.parent, params=self._params())
        try:
            best, reason = self._loop()
        except BaseException as exc:
            self.mlflow.log(self.parent, tags={"error": str(exc)})
            self.mlflow.end_run(self.parent, "FAILED")
            raise
        self._finish(best, reason)
        return best

    def _loop(self) -> tuple[Iteration, str]:
        with tempfile.TemporaryDirectory(prefix="flywheel-") as tmp:
            work = Path(tmp)
            best = self._score(Iteration(number=0, brain={}, decision="baseline"), None, work)
            self.mlflow.log(best.run_id, tags={"decision": best.decision})
            misses = 0
            for step in range(1, self.plan.iterations + 1):
                candidate, adjusted = self._adjust(best, step, work / f"adjust-{step}")
                best, kept = self._decide(candidate, best, adjusted, work)
                misses = 0 if kept else misses + 1
                if misses >= self.plan.patience and step < self.plan.iterations:
                    return best, f"{misses} steps in a row brought no better brain"
            return best, f"all {self.plan.iterations} iterations ran"

    def _adjust(self, best: Iteration, step: int, work: Path) -> tuple[Iteration, Adjusted]:
        evaluation = self.api.evaluation(self.plan.usecase, best.train_job)
        answers = {task_id: self._answer(best.train_job, task_id) for task_id in report.failed_ids(self.version, evaluation)}
        failures = report.failures(self.version, evaluation, answers, best.number)
        history = report.history(self.iterations, best.number, self.words.label)
        adjusted = self.adjuster.adjust(work, best.brain, failures, history, self.words, step, best.number)
        candidate = Iteration(
            number=step,
            brain={**best.brain, **adjusted.updates},
            base=best.number,
            files=sorted(adjusted.updates),
            hypothesis=adjusted.hypothesis,
            change=adjusted.change,
        )
        return candidate, adjusted

    def _decide(self, candidate: Iteration, best: Iteration, adjusted: Adjusted, work: Path) -> tuple[Iteration, bool]:
        if not adjusted.updates:
            candidate.decision = "no change"
            print(f"v{candidate.number}: the adjuster changed no brain file; the best stays v{best.number}", flush=True)
            run_id = self._record(candidate, adjusted, work / f"adjust-{candidate.number}")
            self.mlflow.log(run_id, tags={"decision": candidate.decision})
            self.mlflow.end_run(run_id)
            self.iterations.append(candidate)
            return best, False
        scored = self._score(candidate, adjusted, work)
        kept = scored.train >= best.train
        scored.decision = "kept" if kept else "reverted"
        self.mlflow.log(scored.run_id, tags={"decision": scored.decision})
        print(f"v{scored.number}: train {scored.train:.3f} against v{best.number}'s {best.train:.3f}, {scored.decision}", flush=True)
        return (scored, True) if kept else (best, False)

    def _score(self, it: Iteration, adjusted: Adjusted | None, work: Path) -> Iteration:
        """Create the brain's run, upload the brain, and score it on every split."""
        run_id = self._record(it, adjusted, work / f"adjust-{it.number}")
        it.run_id = run_id
        brain_uri = None
        if it.brain:
            folder = brains.write(it.brain, work / f"brain-{it.number}")
            self.mlflow.upload(run_id, folder, BRAIN_FOLDER)
            brain_uri = f"runs:/{run_id}/{BRAIN_FOLDER}"
        splits = [s for s in (TRAIN, VALIDATION) if s in self.version["tasks_per_split"]]
        jobs = {split: self._start(split, brain_uri)["id"] for split in splits}
        results = {split: self.api.wait(self.plan.usecase, job, self.plan.poll_s, self.plan.evaluation_timeout_s) for split, job in jobs.items()}
        if not isinstance(results[TRAIN].get("reward"), int | float):
            raise FlywheelError(f"evaluation {jobs[TRAIN]} of brain v{it.number} has no train reward")
        it.train, it.train_job = results[TRAIN]["reward"], jobs[TRAIN]
        it.train_judges = report.judge_means(results[TRAIN])
        it.validation = results[VALIDATION].get("reward") if VALIDATION in results else None
        self.mlflow.log(run_id, metrics=_score_metrics(results), tags=_job_tags(results))
        self.mlflow.end_run(run_id)
        self.iterations.append(it)
        return it

    def _record(self, it: Iteration, adjusted: Adjusted | None, adjust_dir: Path) -> str:
        """The brain's child run, with how the adjuster made it."""
        tags = {**self._tags(kind="iteration"), "mlflow.parentRunId": self.parent, "iteration": str(it.number)}
        tags["mlflow.note.content"] = f"Brain v{it.number}" + (f", made from v{it.base}: {it.change}" if it.base is not None else ", the agent bare")
        if it.base is not None:
            tags |= {"adjust_base": str(it.base), "adjusted_files": ", ".join(it.files) or "none"}
            tags |= {"adjuster_hypothesis": it.hypothesis, "adjuster_change": it.change}
        run_id = self.mlflow.start_run(self.experiment, f"{self.plan.training} v{it.number}", tags)
        if adjusted is not None:
            self.mlflow.log(run_id, metrics=adjusted.metrics)
            self.mlflow.upload(run_id, adjust_dir / "logs", "adjuster")
        return run_id

    def _start(self, split: str, brain_uri: str | None) -> dict:
        plan = self.plan
        return self.api.start(
            plan.usecase,
            version=self.version["number"],
            split=split,
            agent=plan.agent,
            model=plan.model,
            brain=brain_uri,
            training=plan.training,
        )

    def _answer(self, job_id: str, task_id: str) -> str:
        files = self.api.task(self.plan.usecase, job_id, task_id).get("answer") or []
        return "\n\n".join(f"#### {f['path']}\n\n{f['text']}" if len(files) > 1 else f["text"] for f in files if f.get("text"))

    def _finish(self, best: Iteration, reason: str) -> None:
        if best.brain:
            with tempfile.TemporaryDirectory(prefix="flywheel-best-") as tmp:
                self.mlflow.upload(self.parent, brains.write(best.brain, Path(tmp)), BRAIN_FOLDER)
        metrics = {"best/iteration": best.number, "best/train/score": best.train}
        if best.validation is not None:
            metrics["best/validation/score"] = best.validation
        self.mlflow.log(self.parent, metrics=metrics, tags={"best_iteration": str(best.number), "stop_reason": reason})
        self.mlflow.end_run(self.parent)
        print(f"training {self.plan.training}: best brain v{best.number}, train {best.train:.3f}; {reason}", flush=True)

    def _tags(self, kind: str) -> dict[str, str]:
        v = self.version
        return {
            "kind": kind,
            "training": self.plan.training,
            "usecase": self.plan.usecase,
            "usecase_version": str(v["number"]),
            "usecase_hash": v["hash"],
        }

    def _params(self) -> dict[str, Any]:
        plan = self.plan
        return {
            "iterations": plan.iterations,
            "patience": plan.patience,
            "agent": plan.agent or "eval.yaml's runner",
            "model": plan.model or "eval.yaml's models.skill",
            "adjuster_model": self.adjuster.model,
            "max_skills": self.words.max_skills,
        }


def _score_metrics(results: Mapping[str, Mapping[str, Any]]) -> dict[str, float]:
    metrics = {}
    for split, row in results.items():
        if isinstance(row.get("reward"), int | float):
            metrics[f"{split}/score"] = row["reward"]
        metrics |= {f"{split}/{name}": value for name, value in report.judge_means(row).items()}
    return metrics


def _job_tags(results: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    tags = {}
    for split, row in results.items():
        tags[f"{split}_evaluation"] = row["id"]
        if row.get("mlflow_run_id"):
            tags[f"{split}_mlflow_run"] = row["mlflow_run_id"]
    return tags
