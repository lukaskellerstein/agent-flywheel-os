"""Fakes for the loop's three neighbours, in the shapes it reads: the
flywheel API, MLflow, and OpenCode as a script that edits the brain."""

from __future__ import annotations

import itertools
import json
import stat
import sys
import textwrap
from pathlib import Path

import pytest

from flywheel_loop.adjust import Adjuster
from flywheel_loop.controller import Plan, Training

JUDGES = [
    {"name": "kb_citation", "description": "Cites the articles"},
    {"name": "must_mention", "description": "Facts", "score_range": [0, 1]},
]
TASKS = [
    {"id": "t1", "split": "train", "input": {"ticket": "Registry removed", "severity": 3}, "expected": {"must_mention": ["oc patch"]}},
    {"id": "t2", "split": "train", "input": {"ticket": "Node NotReady", "severity": 2}, "expected": {"must_mention": ["MTU"]}},
    {"id": "v1", "split": "validation", "input": {"ticket": "Proxy", "severity": 4}, "expected": {"must_mention": ["proxy"]}},
]
DEFINITION = {
    "title": "Support",
    "task": {"label": "ticket", "prompt": "ticket", "show": ["severity"]},
    "brain": {"max_skills": 1},
    "adjuster": {"role": "a support agent", "causes": ["missing citation"], "hidden": "The policy is hidden."},
}


def version(definition=DEFINITION) -> dict:
    return {
        "number": 1,
        "hash": "abc123",
        "tasks_per_split": {"train": 2, "validation": 1},
        "usecase": definition,
        "judges": JUDGES,
        "tasks": TASKS,
    }


class FakeMLflow:
    def __init__(self):
        self.runs: dict[str, dict] = {}
        self._ids = itertools.count(1)

    def experiment(self, name):
        self.experiment_name = name
        return "7"

    def start_run(self, experiment_id, name, tags):
        run_id = f"run{next(self._ids)}"
        self.runs[run_id] = {"name": name, "tags": dict(tags), "metrics": {}, "params": {}, "files": {}, "status": "RUNNING"}
        return run_id

    def log(self, run_id, *, metrics=None, params=None, tags=None):
        run = self.runs[run_id]
        run["metrics"] |= dict(metrics or {})
        for key, value in (params or {}).items():  # MLflow refuses to change a param
            assert run["params"].get(key, str(value)) == str(value), f"param {key} written twice"
            run["params"][key] = str(value)
        run["tags"] |= dict(tags or {})

    def end_run(self, run_id, status="FINISHED"):
        self.runs[run_id]["status"] = status

    def upload(self, run_id, folder, artifact_path):
        for path in folder.rglob("*"):
            if path.is_file():
                self.runs[run_id]["files"][f"{artifact_path}/{path.relative_to(folder).as_posix()}"] = path.read_text()

    def by_name(self, name):
        return next(run for run in self.runs.values() if run["name"] == name)


class FakeAPI:
    """Scores a brain by what its AGENTS.md says: `score: <train>` sets the
    train reward, and every train task fails must_mention below 0.9."""

    def __init__(self, mlflow: FakeMLflow, version_record: dict):
        self.mlflow = mlflow
        self.version_record = version_record
        self.starts: list[dict] = []
        self.jobs: dict[str, dict] = {}
        self.fail_split: str | None = None

    def version(self, usecase, number=None):
        return self.version_record

    def start(self, usecase, **request):
        job_id = f"job{len(self.starts) + 1}"
        self.starts.append(request)
        ran = {"agent": request.get("agent") or "codex", "model": request.get("model") or "enmaas-glm-5-3"}
        self.jobs[job_id] = {"id": job_id, **self._score(request), **ran, "mlflow_run_id": f"ml-{job_id}"}
        return {"id": job_id, "state": "pending"}

    def wait(self, usecase, job_id, poll_s, timeout_s):
        if self.jobs[job_id]["split"] == self.fail_split:
            from flywheel_loop import FlywheelError

            raise FlywheelError(f"evaluation {job_id} ended failed: the pod died")
        return self.evaluation(usecase, job_id)

    def evaluation(self, usecase, job_id):
        return self.jobs[job_id]

    def task(self, usecase, job_id, task_id):
        return {"answer": [{"path": "output/answer.md", "text": f"answer of {task_id} in {job_id}"}]}

    def _score(self, request):
        reward = 0.5
        if request.get("brain"):
            run_id = request["brain"].split("/")[1]
            agents = self.mlflow.runs[run_id]["files"].get("brain/AGENTS.md", "")
            reward = float(agents.split("score:")[1].split()[0]) if "score:" in agents else 0.5
        if request["split"] == "validation":
            reward = round(reward - 0.1, 3)
        ids = [t["id"] for t in TASKS if t["split"] == request["split"]]
        tasks = [
            {
                "id": task_id,
                "reward": reward,
                "judges": {
                    "kb_citation": {"value": True, "rationale": "cited", "error": None},
                    "must_mention": {"value": 0.5, "rationale": f"missing fact of {task_id}", "error": None},
                },
            }
            for task_id in ids
        ]
        judges = [{"name": "kb_citation", "mean": None, "pass_rate": 1.0}, {"name": "must_mention", "mean": 0.5}]
        return {"split": request["split"], "state": "completed", "reward": reward, "tasks": tasks, "judges": judges}


FAKE_OPENCODE = """\
#!{python}
# A stand-in for `opencode run`: each call takes the next edit of the plan
# file, writes it into brain/, writes change.md, and prints JSON events.
import json, os, sys
from pathlib import Path
ws = Path(sys.argv[sys.argv.index("--dir") + 1])
plan = Path(os.environ["FAKE_PLAN"])
edits = json.loads(plan.read_text())
edit = edits.pop(0) if edits else {{}}
plan.write_text(json.dumps(edits))
Path(os.environ["FAKE_PLAN"] + ".tasks").open("a").write(sys.argv[2] + "\\n=====\\n")
for key, text in edit.get("files", {{}}).items():
    path = ws / "brain" / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
if edit.get("change"):
    (ws / "change.md").write_text(edit["change"])
print(json.dumps({{"type": "tool_use", "part": {{"tool": "edit", "state": {{"input": {{"path": "brain/AGENTS.md"}}}}}}}}))
print(json.dumps({{"type": "step_finish", "part": {{"tokens": {{"input": 100, "output": 20, "cache": {{"read": 50}}}}, "cost": 0}}}}))
print(json.dumps({{"type": "text", "part": {{"text": edit.get("message", "Changed AGENTS.md.")}}}}))
sys.exit(edit.get("exit", 0))
"""


@pytest.fixture
def opencode(tmp_path, monkeypatch):
    """The fake OpenCode; call it with the list of edits its sessions make."""
    script = tmp_path / "opencode"
    script.write_text(FAKE_OPENCODE.format(python=sys.executable))
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    plan = tmp_path / "plan.json"
    monkeypatch.setenv("FAKE_PLAN", str(plan))

    def edits(*steps):
        plan.write_text(json.dumps(list(steps)))
        return script

    edits.tasks = lambda: (Path(str(plan) + ".tasks").read_text() if Path(str(plan) + ".tasks").exists() else "")
    return edits


@pytest.fixture
def mlflow():
    return FakeMLflow()


@pytest.fixture
def make_training(mlflow):
    def make(script, *, iterations=2, patience=2, definition=DEFINITION, agent=None, model=None):
        api = FakeAPI(mlflow, version(definition))
        adjuster = Adjuster("enmaas-glm-5-3", "http://gateway:4000", 30, opencode=str(script))
        plan = Plan(usecase="support", training="tr-1", iterations=iterations, patience=patience, poll_s=0, agent=agent, model=model)
        return Training(plan, api, mlflow, adjuster), api

    return make


def change(hypothesis: str, what: str) -> str:
    return textwrap.dedent(f"Hypothesis: {hypothesis}\nChange: {what}\n")
