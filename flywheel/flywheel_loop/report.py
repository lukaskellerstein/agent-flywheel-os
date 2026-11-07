"""What the adjuster reads: failures.md, the best brain's failures on the
train tasks, and history.md, every brain this training run tried.

Never a validation number: the validation split is the benchmark set, so a
brain changed for it would be ranked on the data that changed it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .brain import Brain


@dataclass
class Iteration:
    """One brain of the training run, and what became of it."""

    number: int
    brain: Brain
    base: int | None = None  # the brain it was made from; None for v0
    files: list[str] = field(default_factory=list)
    hypothesis: str = ""
    change: str = ""
    train: float | None = None
    validation: float | None = None
    train_judges: dict[str, float] = field(default_factory=dict)
    decision: str = "not decided"
    train_job: str | None = None
    run_id: str | None = None  # its MLflow run


def judge_tops(judges: list[Mapping[str, Any]]) -> dict[str, float]:
    """Each numeric judge's best score, from its score_range; a pass/fail judge has none."""
    return {j["name"]: float(j["score_range"][1]) for j in judges if j.get("score_range")}


def failed(verdict: Mapping[str, Any], top: float | None) -> bool:
    value = verdict.get("value")
    if isinstance(value, bool):
        return not value
    if isinstance(value, int | float):
        return value < (top if top is not None else 1.0)
    return verdict.get("error") is not None  # None and no error: the judge abstained


def judge_means(evaluation: Mapping[str, Any]) -> dict[str, float]:
    means = {}
    for judge in evaluation.get("judges") or []:
        value = judge.get("mean") if judge.get("mean") is not None else judge.get("pass_rate")
        if isinstance(value, int | float):
            means[judge["name"]] = float(value)
    return means


def failures(version: Mapping[str, Any], evaluation: Mapping[str, Any], answers: Mapping[str, str], brain: int) -> str:
    """The report of brain v*brain* on the train tasks: every task a judge
    scored below its top, with its input, the expectations, every verdict
    and the agent's answer."""
    words = version["usecase"]["task"]
    label = words.get("label") or "task"
    tasks = {task["id"]: task for task in version["tasks"]}
    tops = judge_tops(version["judges"])
    rows = evaluation["tasks"]
    means = ", ".join(f"{name} {mean:.2f}" for name, mean in judge_means(evaluation).items())
    lines = [
        f"# Eval failures of brain v{brain}",
        "",
        f"This report covers all {len(rows)} train {label}s of the score run.",
        f"Judge means over them: {means}.",
        f"A {label} is listed when any judge scored below its top, with every judge's verdict.",
        f"A {label} that is not listed scored the top on every judge.",
        "",
    ]
    for row in rows:
        if any(failed(v, tops.get(name)) for name, v in row["judges"].items()):
            lines += _failed_task(row, tasks[row["id"]], words, tops, answers.get(row["id"], ""))
    return "\n".join(lines) + "\n"


def failed_ids(version: Mapping[str, Any], evaluation: Mapping[str, Any]) -> list[str]:
    tops = judge_tops(version["judges"])
    return [row["id"] for row in evaluation["tasks"] if any(failed(v, tops.get(n)) for n, v in row["judges"].items())]


def _failed_task(row: Mapping, task: Mapping, words: Mapping, tops: Mapping[str, float], answer: str) -> list[str]:
    label = (words.get("label") or "task").capitalize()
    inputs = task.get("input") or {}
    shown = ", ".join(f"{key} {inputs.get(key)}" for key in words.get("show") or [])
    lines = [f"## {label} {row['id']}" + (f" ({shown})" if shown else ""), "", f"### {label}", ""]
    lines += [str(inputs.get(words["prompt"], "")).strip(), "", "### Expected", ""]
    lines += [f"- {key}: {value}" for key, value in (task.get("expected") or {}).items()]
    lines += ["", "### Judges", ""]
    for name, verdict in row["judges"].items():
        note = str(verdict.get("rationale") or verdict.get("error") or "").strip()
        lines.append(f"- {name}: {_verdict(verdict.get('value'), tops.get(name))}. {note}")
    return lines + ["", "### The agent's answer", "", answer.strip() or "(no answer)", ""]


def _verdict(value: Any, top: float | None) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, int | float):
        return f"{value:g} of {top if top is not None else 1:g}"
    return "ERROR"


def history(iterations: list[Iteration], base: int, label: str) -> str:
    """Every brain so far, on the train tasks: from which brain, what changed and why, kept or not."""
    scores = {it.number: it.train for it in iterations if it.train is not None}
    lines = [
        "# History of this flywheel",
        "",
        f"Every brain this flywheel scored so far, on the train {label}s. The flywheel keeps a new brain",
        "when its train score is at least the best so far, else it reverts to the best brain.",
        "A step that changed no brain file is `no change`, and counts as a revert.",
        f"You start from brain v{base}, the best so far (train score {scores[base]:.3f}).",
        "",
        "| Brain | Built from | Files changed | Train score | Change against its base | Decision |",
        "|:--|:--|:--|:--|:--|:--|",
    ]
    lines += [_history_row(it, scores) for it in iterations]
    lines += ["", "## What each change tried", ""]
    tried = [it for it in iterations if it.base is not None]
    lines += [f"- v{it.number}, {it.decision}. Hypothesis: {it.hypothesis} Change: {it.change}" for it in tried]
    if not tried:
        lines.append("Nothing yet: this is the first adjust step.")
    return "\n".join(lines + _judge_table(iterations, label)) + "\n"


def _history_row(it: Iteration, scores: Mapping[int, float]) -> str:
    if it.base is None:
        return f"| v0 | - | none, the starting brain | {it.train:.3f} | - | {it.decision} |"
    files = ", ".join(it.files) or "none"
    if it.train is None:
        return f"| v{it.number} | v{it.base} | {files} | - | - | {it.decision} |"
    delta = it.train - scores[it.base]
    return f"| v{it.number} | v{it.base} | {files} | {it.train:.3f} | {delta:+.3f} | {it.decision} |"


def _judge_table(iterations: list[Iteration], label: str) -> list[str]:
    scored = [it for it in iterations if it.train is not None]
    judges = list(dict.fromkeys(name for it in scored for name in it.train_judges))
    lines = ["", f"## Judge means on the train {label}s", "", "Higher is better.", ""]
    lines += ["| Brain | " + " | ".join(judges) + " |", "|:--|" + ":--|" * len(judges)]
    for it in scored:
        cells = [f"{it.train_judges[j]:.2f}" if j in it.train_judges else "-" for j in judges]
        lines.append(f"| v{it.number} | " + " | ".join(cells) + " |")
    return lines
