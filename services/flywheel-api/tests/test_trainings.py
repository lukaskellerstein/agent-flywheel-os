"""The training routes, with MLflow faked in the shapes the loop (flywheel/)
writes: a parent run per training run and a child run per brain."""

from __future__ import annotations

import pytest
from test_evaluations import AUTH, TOKEN, FakeEvalHub, _service, _upload

from flywheel_api.remote import RemoteError

EXPERIMENT = "12"


def _run(run_id, tags, *, status="FINISHED", start=1_762_525_142_000, end=None, params=None, metrics=None) -> dict:
    return {
        "info": {
            "run_id": run_id,
            "experiment_id": EXPERIMENT,
            "status": status,
            "start_time": start,
            "end_time": end,
            "artifact_uri": f"mlflow-artifacts:/workspaces/agent-flywheel/{EXPERIMENT}/{run_id}/artifacts",
        },
        "data": {
            "tags": [{"key": k, "value": v} for k, v in tags.items()],
            "params": [{"key": k, "value": v} for k, v in (params or {}).items()],
            "metrics": [{"key": k, "value": v, "timestamp": 0, "step": 0} for k, v in (metrics or {}).items()],
        },
    }


def _parent(training, *, status="FINISHED", start=1_762_525_142_000, **extra_tags) -> dict:
    tags = {"kind": "training", "training": training, "usecase": "sample", "usecase_version": "2", "usecase_hash": "abc"}
    params = {"iterations": "2", "patience": "2", "agent": "eval.yaml's runner", "model": "eval.yaml's models.skill", "adjuster_model": "enmaas-glm-5-3"}
    return _run(f"p-{training}", tags | extra_tags, status=status, start=start, end=None if status == "RUNNING" else start + 3_600_000, params=params)


def _child(training, number, decision, train=None, validation=None, **extra_tags) -> dict:
    tags = {"kind": "iteration", "training": training, "iteration": str(number), "decision": decision}
    metrics = {}
    if train is not None:
        metrics |= {"train/score": train, "train/must_mention": train, "validation/score": validation, "validation/must_mention": validation}
        tags |= {"train_evaluation": f"job-t{number}", "validation_evaluation": f"job-v{number}"}
    if number:
        tags |= {"adjust_base": "0", "adjusted_files": "AGENTS.md", "adjuster_hypothesis": "no citations", "adjuster_change": "AGENTS.md: cite"}
        metrics |= {"adjuster/steps": 9.0, "adjuster/tool_calls": 6.0, "adjuster/cost_usd": 0.0, "adjuster/sessions": 1.0}
    return _run(f"c-{training}-{number}", tags | extra_tags, metrics=metrics)


class FakeTrainingMLflow:
    """MLflow's experiment lookup, run search (paged), run get, artifact list and files."""

    def __init__(self, runs: list[dict], files: dict[tuple[str, str], bytes] | None = None, page: int = 1000):
        self.runs = runs
        self.files = files or {}
        self.page = page
        self.searches: list[dict] = []

    def json(self, method, path, token, *, query=None, body=None):
        assert token == TOKEN
        if path == "/api/2.0/mlflow/experiments/get-by-name":
            if query["experiment_name"] != "agent-flywheel-sample" or not self.runs:
                raise RemoteError(404, "MLflow answered 404: RESOURCE_DOES_NOT_EXIST")
            return {"experiment": {"experiment_id": EXPERIMENT}}
        if path == "/api/2.0/mlflow/runs/search":
            return self._search(body)
        if path == "/api/2.0/mlflow/runs/get":
            return {"run": next(r for r in self.runs if r["info"]["run_id"] == query["run_id"])}
        assert path == "/api/2.0/mlflow/artifacts/list"
        return self._listing(query["run_id"], query["path"])

    def _search(self, body):
        self.searches.append(body)
        assert body["experiment_ids"] == [EXPERIMENT]
        key, value = body["filter"].removeprefix("tags.").split(" = ")
        found = [r for r in self.runs if {t["key"]: t["value"] for t in r["data"]["tags"]}.get(key) == value.strip("'")]
        start = int(body.get("page_token") or 0)
        answer = {"runs": found[start : start + self.page]}
        if start + self.page < len(found):
            answer["next_page_token"] = str(start + self.page)
        return answer

    def _listing(self, run_id, folder):
        entries = {}
        for (owner, path) in self.files:
            if owner == run_id and path.startswith(folder + "/"):
                child = folder + "/" + path[len(folder) + 1 :].split("/")[0]
                entries[child] = {"path": child, "is_dir": child != path}
        return {"files": sorted(entries.values(), key=lambda e: e["path"])} if entries else {}

    def raw(self, method, path, token, *, query=None, body=None):
        for (owner, name), data in self.files.items():
            if path == f"/api/2.0/mlflow-artifacts/artifacts/workspaces/agent-flywheel/{EXPERIMENT}/{owner}/artifacts/{name}":
                return data
        raise RemoteError(404, "MLflow answered 404: No such artifact")


RUNS = [
    _parent("training-old", start=1_762_400_000_000, best_iteration="1", stop_reason="all 2 iterations ran"),
    _child("training-old", 0, "baseline", 0.5, 0.4),
    _child("training-old", 2, "reverted", 0.55, 0.5),
    _child("training-old", 1, "kept", 0.7, 0.6),
    _parent("training-new", status="RUNNING", start=1_762_525_142_000),
    _child("training-new", 0, "baseline", 0.45, 0.4),
    _child("training-new", 1, "not decided"),
]
FILES = {
    ("c-training-old-1", "brain/AGENTS.md"): b"Cite the articles.",
    ("c-training-old-1", "brain/.agents/skills/ask-version/SKILL.md"): b"---\nname: ask-version\n---\nAsk.",
    ("c-training-old-1", "adjuster/failures.md"): b"# Eval failures of brain v0",
    ("c-training-old-1", "adjuster/history.md"): b"# History of this flywheel",
    ("c-training-old-1", "adjuster/transcript.md"): b"ASSISTANT:\nDone.",
}


@pytest.fixture
def make_client(tmp_path, files):
    def make(mlflow):
        client = _service(tmp_path, FakeEvalHub(), mlflow)
        _upload(client, files)
        return client

    return make


def test_the_list_is_every_training_run_newest_first(make_client):
    response = make_client(FakeTrainingMLflow(RUNS)).get("/api/usecases/sample/trainings", headers=AUTH)
    assert response.status_code == 200, response.text
    new, old = response.json()
    assert (new["id"], new["state"], new["ended"], new["brains_scored"]) == ("training-new", "running", None, 1)
    assert new["best"] == {"number": 0, "train": 0.45, "validation": 0.4}  # the last kept or baseline brain while it runs
    assert old == {
        "id": "training-old",
        "usecase": "sample",
        "version": 2,
        "state": "finished",
        "started": "2025-11-06T03:33:20Z",
        "ended": "2025-11-06T04:33:20Z",
        "iterations": 2,
        "brains_scored": 3,
        "best": {"number": 1, "train": 0.7, "validation": 0.6},
        "agent": "eval.yaml's runner",
        "model": "eval.yaml's models.skill",
        "adjuster_model": "enmaas-glm-5-3",
        "stop_reason": "all 2 iterations ran",
        "error": None,
        "mlflow_run_id": "p-training-old",
        "mlflow_experiment_id": "12",
    }


def test_one_training_run_has_its_brains_in_order(make_client):
    response = make_client(FakeTrainingMLflow(RUNS)).get("/api/usecases/sample/trainings/training-old", headers=AUTH)
    assert response.status_code == 200, response.text
    run = response.json()
    assert [(b["number"], b["decision"], b["train"]) for b in run["brains"]] == [(0, "baseline", 0.5), (1, "kept", 0.7), (2, "reverted", 0.55)]
    v0, v1, _ = run["brains"]
    assert (v0["base"], v0["files"], v0["hypothesis"], v0["adjuster"]) == (None, [], "", None)
    assert v1 == {
        "number": 1,
        "base": 0,
        "decision": "kept",
        "train": 0.7,
        "validation": 0.6,
        "train_judges": {"must_mention": 0.7},
        "validation_judges": {"must_mention": 0.6},
        "files": ["AGENTS.md"],
        "hypothesis": "no citations",
        "change": "AGENTS.md: cite",
        "train_evaluation": "job-t1",
        "validation_evaluation": "job-v1",
        "adjuster": {"steps": 9.0, "tool_calls": 6.0, "cost_usd": 0.0, "sessions": 1.0},
        "mlflow_run_id": "c-training-old-1",
    }


def test_a_brain_has_its_files_and_the_adjusters_reports(make_client):
    client = make_client(FakeTrainingMLflow(RUNS, FILES))
    brain = client.get("/api/usecases/sample/trainings/training-old/brains/1", headers=AUTH).json()
    assert brain == {
        "number": 1,
        "files": [
            {"path": ".agents/skills/ask-version/SKILL.md", "text": "---\nname: ask-version\n---\nAsk."},
            {"path": "AGENTS.md", "text": "Cite the articles."},
        ],
        "reports": [
            {"path": "failures.md", "text": "# Eval failures of brain v0"},
            {"path": "history.md", "text": "# History of this flywheel"},
            {"path": "transcript.md", "text": "ASSISTANT:\nDone."},
        ],
    }
    assert client.get("/api/usecases/sample/trainings/training-old/brains/0", headers=AUTH).json() == {"number": 0, "files": [], "reports": []}


@pytest.mark.parametrize(
    ("path", "detail"),
    [
        ("/api/usecases/sample/trainings/training-gone", "no training run 'training-gone' of use case 'sample'"),
        ("/api/usecases/sample/trainings/Bad'Id", "no training run \"Bad'Id\" of use case 'sample'"),
        ("/api/usecases/sample/trainings/training-old/brains/7", "training run 'training-old' has no brain v7"),
        ("/api/usecases/nothing/trainings", "no use case 'nothing'"),
    ],
)
def test_an_unknown_run_brain_or_use_case_is_404(make_client, path, detail):
    response = make_client(FakeTrainingMLflow(RUNS)).get(path, headers=AUTH)
    assert (response.status_code, response.json()["detail"]) == (404, detail)


def test_a_use_case_never_trained_has_no_training_runs(make_client):
    assert make_client(FakeTrainingMLflow([])).get("/api/usecases/sample/trainings", headers=AUTH).json() == []


def test_the_search_reads_every_page(make_client):
    mlflow = FakeTrainingMLflow(RUNS, page=2)
    response = make_client(mlflow).get("/api/usecases/sample/trainings/training-old", headers=AUTH)
    assert len(response.json()["brains"]) == 3
    assert [s.get("page_token") for s in mlflow.searches] == [None, "2"]


def test_the_training_routes_need_the_callers_token(make_client):
    response = make_client(FakeTrainingMLflow(RUNS)).get("/api/usecases/sample/trainings")
    assert response.status_code == 401
