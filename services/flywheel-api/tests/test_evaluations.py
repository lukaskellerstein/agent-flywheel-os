"""The evaluation routes, with EvalHub and MLflow faked in their real shapes
(read from cluster-nm8mw on 2026-11-05: EvalHub 4315523, ODH's MLflow)."""

from __future__ import annotations

import copy

import pytest
import yaml
from fastapi.testclient import TestClient
from helpers import tar_gz

from flywheel_api.app import create_app
from flywheel_api.evaluations import JOBS, Evaluations, Settings, evaluations_from_env
from flywheel_api.registry import Registry
from flywheel_api.remote import RemoteError
from flywheel_api.results import judges_of, tasks_of, thresholds_of
from flywheel_api.store import FileStore

TOKEN = "caller-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
SETTINGS = Settings(
    provider="agent-eval-harness",
    bucket="flywheel-usecases-1234",
    secret="flywheel-usecases",
    model_url="http://gateway.agent-flywheel.svc:4000/v1",
)
# What the tests add to the sample's eval.yaml: the agent, the reward and the thresholds (C20).
EVAL_ADDITIONS = b"""
models:
  skill: enmaas-glm-5-3
runner:
  type: codex
reward:
  weights: {must_mention: 0.7, style: 0.3}
thresholds:
  reward: {min_mean: 0.6, min_per_case: 0.5}
  must_mention: {min_pass_rate: 1.0}
"""
# The harness's summary.yaml (the shape of job 6bbcc140's, smoke version 2), cut to what the API reads.
CHECKS = [
    {"target": "must_mention", "check": "min_pass_rate", "metric": "pass_rate", "limit": 1.0, "value": 0.5, "passed": False},
    {"target": "reward", "check": "min_mean", "metric": "mean", "limit": 0.6, "value": 0.5, "passed": False},
    {
        "target": "reward",
        "check": "min_per_case",
        "metric": "lowest_case",
        "limit": 0.5,
        "value": 0.0,
        "passed": False,
        "cases_below": ["export-data"],
        "detail": "1 of 2 cases below 0.5",
    },
]
SUMMARY = {
    "judges": {
        "must_mention": {"mean": 0.5, "pass_rate": 0.5, "scored_cases": 2, "errored_cases": 0},
        "style": {"mean": 1.0, "pass_rate": 1.0, "scored_cases": 2, "errored_cases": 0},
    },
    "per_case": {
        "export-data": {
            "style": {"judge_type": "llm", "rationale": "follows the guide", "value": True},
            "must_mention": {"judge_type": "check", "rationale": "missing: CSV", "value": False},
        },
        "pricing": {"must_mention": {"judge_type": "check", "rationale": "mentions every expected fact", "value": True}},
    },
    "reward": {"mean": 0.5, "per_case": {"export-data": 0.0, "pricing": 1.0, "unscored": None}, "scored_cases": 2},
    "thresholds": {"passed": False, "enforced": False, "checks": CHECKS},
}


class FakeEvalHub:
    """EvalHub's job routes: a job is its request plus resource, status and results."""

    def __init__(self):
        self.jobs: dict[str, dict] = {}
        self.calls: list[tuple] = []

    def json(self, method, path, token, *, query=None, body=None):
        self.calls.append((method, path, token, query, body))
        if (method, path) == ("POST", JOBS):
            job_id = f"job-{len(self.jobs) + 1}"
            resource = {
                "id": job_id,
                "created_at": f"2026-11-05T10:0{len(self.jobs)}:00Z",
                "owner": "lukas",
                "mlflow_experiment_id": "2",
            }
            self.jobs[job_id] = {**copy.deepcopy(body), "resource": resource, "status": {"state": "pending"}}
            return self.jobs[job_id]
        if (method, path) == ("GET", JOBS):
            matching = [job for job in self.jobs.values() if query["tags"] in job["tags"]]
            return {"items": matching[query["offset"] : query["offset"] + query["limit"]]}
        job_id = path.removeprefix(JOBS + "/")
        if method == "GET" and job_id in self.jobs:
            return self.jobs[job_id]
        raise RemoteError(404, f"EvalHub answered 404: no job {job_id}")

    def raw(self, method, path, token, *, query=None, body=None, accept="application/json"):
        """DELETE (cancel, or remove with hard_delete) and the job's logs."""
        self.calls.append((method, path, token, query, body))
        job_id = path.removeprefix(JOBS + "/").removesuffix("/logs")
        if job_id not in self.jobs:
            raise RemoteError(404, f"EvalHub answered 404: no job {job_id}")
        if path.endswith("/logs"):
            assert (method, accept) == ("GET", "text/plain")
            return f"=== pod={job_id}-adapter container=adapter benchmark_id=eval-run ===\nINFO starting evaluation\n".encode()
        assert method == "DELETE"
        if query["hard_delete"] == "true":
            del self.jobs[job_id]
        elif self.jobs[job_id]["status"]["state"] == "completed":
            raise RemoteError(409, "EvalHub answered 409: the job is completed")
        else:
            self.jobs[job_id]["status"]["state"] = "cancelled"
        return b""

    def complete(self, job_id: str, reward: float, run_id: str | None) -> None:
        self.jobs[job_id]["status"] = {
            "state": "completed",
            "message": {"message": "Evaluation job is completed"},
            "benchmarks": [{"phase": "completed", "started_at": "2026-11-05T10:01:00Z"}],
        }
        result = {"metrics": {"reward": reward, "must_mention_mean": reward}, "mlflow_run_id": run_id}
        self.jobs[job_id]["results"] = {"benchmarks": [result], "test": {"pass": reward >= 0.5, "threshold": 0.5}}


class FakeMLflow:
    def __init__(self, files: dict[str, bytes], artifact_uri: str = "mlflow-artifacts:/workspaces/agent-flywheel/2/run-1/artifacts"):
        self.files = files
        self.artifact_uri = artifact_uri
        self.calls: list[tuple] = []

    def json(self, method, path, token, *, query=None, body=None):
        self.calls.append((method, path, token))
        assert path == "/api/2.0/mlflow/runs/get"
        return {"run": {"info": {"run_id": query["run_id"], "artifact_uri": self.artifact_uri}}}

    def raw(self, method, path, token, *, query=None, body=None):
        self.calls.append((method, path, token))
        if path not in self.files:
            raise RemoteError(404, "MLflow answered 404: No such artifact")
        return self.files[path]


SUMMARY_PATH = "/api/2.0/mlflow-artifacts/artifacts/workspaces/agent-flywheel/2/run-1/artifacts/run/summary.yaml"


@pytest.fixture
def evalhub() -> FakeEvalHub:
    return FakeEvalHub()


@pytest.fixture
def mlflow() -> FakeMLflow:
    return FakeMLflow({SUMMARY_PATH: yaml.safe_dump(SUMMARY).encode()})


@pytest.fixture
def client(tmp_path, files, evalhub, mlflow) -> TestClient:
    """The sample use case imported twice: version 2 adds a split-less change."""
    registry = Registry(FileStore(tmp_path / "store"))
    app = create_app(registry, Evaluations(registry, evalhub, mlflow, SETTINGS))
    client = TestClient(app)
    files["eval.yaml"] = files["eval.yaml"] + EVAL_ADDITIONS
    _upload(client, files)
    files["usecase.yaml"] = files["usecase.yaml"].replace(b"Product questions", b"Product questions, again")
    _upload(client, files)
    return client


def _upload(client: TestClient, files) -> None:
    response = client.post("/api/usecases/sample/imports", files={"file": ("s.tar.gz", tar_gz(files), "application/gzip")})
    assert response.status_code == 201, response.text


def test_a_start_sends_the_job_as_the_caller(client, evalhub):
    response = client.post("/api/usecases/sample/evaluations", json={"version": 1, "split": "validation"}, headers=AUTH)
    assert response.status_code == 201, response.text
    [(method, path, token, _, body)] = evalhub.calls
    assert (method, path, token) == ("POST", JOBS, TOKEN)
    assert body == {
        "name": "sample-v1-validation-enmaas-glm-5-3",
        "tags": ["agent-flywheel", "usecase:sample", "version:1", "split:validation"],
        "model": {"name": "enmaas-glm-5-3", "url": "http://gateway.agent-flywheel.svc:4000/v1"},
        "benchmarks": [
            {
                "id": "eval-run",
                "provider_id": "agent-eval-harness",
                "parameters": {"split": "validation"},
                "test_data_ref": {
                    "s3": {
                        "bucket": "flywheel-usecases-1234",
                        "key": "usecases/sample/versions/1/",
                        "secret_ref": "flywheel-usecases",
                    }
                },
                "pass_criteria": {"threshold": 0.6},
            }
        ],
        "experiment": {
            "name": "agent-flywheel-sample",
            "tags": [
                {"key": "usecase", "value": "sample"},
                {"key": "usecase_version", "value": "1"},
                {"key": "split", "value": "validation"},
            ],
        },
    }
    started = response.json()
    assert (started["id"], started["version"], started["split"], started["state"]) == ("job-1", 1, "validation", "pending")
    assert (started["agent"], started["thresholds"], started["tasks_detail"]) == ("codex", None, "the job has no MLflow run yet")


def test_a_version_says_what_eval_yaml_sets_for_a_run(client):
    version = client.get("/api/usecases/sample/versions/2").json()
    assert (version["agent"], version["model"]) == ("codex", "enmaas-glm-5-3")
    assert version["reward"] == {"weights": {"must_mention": 0.7, "style": 0.3}}
    assert version["thresholds"] == {"reward": {"min_mean": 0.6, "min_per_case": 0.5}, "must_mention": {"min_pass_rate": 1.0}}


def test_without_a_reward_min_mean_evalhub_keeps_its_own_pass_criteria(tmp_path, files, evalhub, mlflow):
    registry = Registry(FileStore(tmp_path / "store"))
    client = TestClient(create_app(registry, Evaluations(registry, evalhub, mlflow, SETTINGS)))
    files["eval.yaml"] += b"\nmodels:\n  skill: enmaas-glm-5-3\n"
    _upload(client, files)
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert "pass_criteria" not in evalhub.calls[0][4]["benchmarks"][0]


def test_a_bare_start_takes_the_current_version_every_task_and_the_eval_model(client, evalhub):
    response = client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert response.status_code == 201, response.text
    body = evalhub.calls[0][4]
    assert body["name"] == "sample-v2-all-enmaas-glm-5-3"
    assert body["benchmarks"][0]["parameters"] == {}
    assert body["benchmarks"][0]["test_data_ref"]["s3"]["key"] == "usecases/sample/versions/2/"
    assert "split:all" not in body["tags"]
    other = client.post("/api/usecases/sample/evaluations", json={"model": "enmaas-gemini"}, headers=AUTH)
    assert evalhub.calls[1][4]["model"]["name"] == "enmaas-gemini", other.text


@pytest.mark.parametrize(
    ("request_body", "status", "detail"),
    [
        ({"split": "holdout"}, 422, "has no split 'holdout'; its splits: train, validation"),
        ({"version": 9}, 404, "no version 9 of use case 'sample'"),
        ({"version": 0}, 422, "greater than or equal to 1"),
        ({"brain": "runs:/x/y"}, 422, "Extra inputs are not permitted"),
    ],
)
def test_a_start_that_cannot_run_reaches_no_evalhub(client, evalhub, request_body, status, detail):
    response = client.post("/api/usecases/sample/evaluations", json=request_body, headers=AUTH)
    assert response.status_code == status
    assert detail in response.text
    assert evalhub.calls == []


def test_a_start_without_a_model_anywhere_is_refused(tmp_path, files, evalhub, mlflow):
    registry = Registry(FileStore(tmp_path / "store"))
    client = TestClient(create_app(registry, Evaluations(registry, evalhub, mlflow, SETTINGS)))
    _upload(client, files)
    response = client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert response.status_code == 422
    assert response.json()["detail"] == "give a model: eval.yaml of version 1 names no models.skill"


@pytest.mark.parametrize("header", [{}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer  "}])
def test_every_evaluation_route_needs_the_callers_token(client, evalhub, header):
    for method, path in [
        ("POST", "/api/usecases/sample/evaluations"),
        ("GET", "/api/usecases/sample/evaluations"),
        ("GET", "/api/usecases/sample/evaluations/job-1"),
        ("DELETE", "/api/usecases/sample/evaluations/job-1"),
        ("GET", "/api/usecases/sample/evaluations/job-1/logs"),
    ]:
        response = client.request(method, path, headers=header)
        assert response.status_code == 401, (method, path)
    assert evalhub.calls == []


def test_the_list_is_the_use_cases_jobs_newest_first(client, evalhub):
    for version in (1, 2):
        client.post("/api/usecases/sample/evaluations", json={"version": version}, headers=AUTH)
    evalhub.json("POST", JOBS, TOKEN, body={"name": "other", "tags": ["usecase:other"]})
    evalhub.calls.clear()
    response = client.get("/api/usecases/sample/evaluations", headers=AUTH)
    assert [(job["id"], job["version"]) for job in response.json()] == [("job-2", 2), ("job-1", 1)]
    [(_, _, token, query, _)] = evalhub.calls
    assert (token, query) == (TOKEN, {"tags": "usecase:sample", "limit": 100, "offset": 0})


def test_the_list_reads_every_page(client, evalhub, monkeypatch):
    monkeypatch.setattr("flywheel_api.evaluations.PAGE", 2)
    for _ in range(5):
        client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert len(client.get("/api/usecases/sample/evaluations", headers=AUTH).json()) == 5


def test_the_list_of_an_unknown_use_case_is_404(client):
    assert client.get("/api/usecases/nothing/evaluations", headers=AUTH).status_code == 404


def test_a_finished_job_carries_its_scores_and_each_tasks_verdicts(client, evalhub, mlflow):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    evalhub.complete("job-1", 0.5, "run-1")
    job = client.get("/api/usecases/sample/evaluations/job-1", headers=AUTH).json()
    assert (job["state"], job["phase"], job["reward"], job["passed"], job["threshold"]) == (
        "completed",
        "completed",
        0.5,
        True,
        0.5,
    )
    assert job["message"] == "Evaluation job is completed"
    assert (job["mlflow_experiment_id"], job["mlflow_run_id"], job["agent"], job["tasks_detail"]) == ("2", "run-1", "codex", None)
    assert job["judges"] == [
        {
            "name": "must_mention",
            "description": "The answer mentions every expected fact",
            "weight": 0.7,
            "mean": 0.5,
            "pass_rate": 0.5,
            "scored_cases": 2,
            "errored_cases": 0,
        },
        {
            "name": "style",
            "description": "The answer follows the style guide",
            "weight": 0.3,
            "mean": 1.0,
            "pass_rate": 1.0,
            "scored_cases": 2,
            "errored_cases": 0,
        },
    ]
    assert job["thresholds"] == {"passed": False, "checks": CHECKS}
    assert job["tasks"] == [
        {
            "id": "export-data",
            "reward": 0.0,
            "judges": {
                "must_mention": {"value": False, "rationale": "missing: CSV", "error": None},
                "style": {"value": True, "rationale": "follows the guide", "error": None},
            },
        },
        {
            "id": "pricing",
            "reward": 1.0,
            "judges": {"must_mention": {"value": True, "rationale": "mentions every expected fact", "error": None}},
        },
        {"id": "unscored", "reward": None, "judges": {}},
    ]
    assert all(token == TOKEN for _, _, token in mlflow.calls)


def test_the_list_carries_each_ended_jobs_threshold_verdicts(client, evalhub):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    evalhub.complete("job-1", 0.5, "run-1")
    rows = {row["id"]: row for row in client.get("/api/usecases/sample/evaluations", headers=AUTH).json()}
    assert rows["job-1"]["thresholds"] == {"passed": False, "checks": CHECKS}
    assert (rows["job-2"]["thresholds"], rows["job-2"]["tasks_detail"]) == (None, "the job has no MLflow run yet")
    assert {row["agent"] for row in rows.values()} == {"codex"}


def test_an_ended_jobs_summary_is_read_from_mlflow_once(client, evalhub, mlflow):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    evalhub.complete("job-1", 0.5, "run-1")
    for _ in range(3):
        client.get("/api/usecases/sample/evaluations", headers=AUTH)
        client.get("/api/usecases/sample/evaluations/job-1", headers=AUTH)
    assert len(mlflow.calls) == 2  # the run's record and its summary.yaml, once


def test_a_running_jobs_summary_is_read_again(client, evalhub, mlflow):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    evalhub.complete("job-1", 0.5, "run-1")
    evalhub.jobs["job-1"]["status"]["state"] = "running"
    for _ in range(2):
        client.get("/api/usecases/sample/evaluations/job-1", headers=AUTH)
    assert len(mlflow.calls) == 4


def test_tasks_of_orders_the_judges_as_eval_yaml_and_the_rest_by_name():
    summary_yaml = {"per_case": {"t": {"b": {"value": 1}, "z": {"value": 2}, "a": {"value": 3}}}}
    [task] = tasks_of(summary_yaml, ["z", "b"])
    assert list(task["judges"]) == ["z", "b", "a"]


def test_judges_of_a_run_without_aggregates_keeps_eval_yamls_judges():
    config = {"judges": [{"name": "exit"}], "reward": {"weights": {}}}
    assert judges_of(config, {}) == [
        {"name": "exit", "description": None, "weight": None, "mean": None, "pass_rate": None, "scored_cases": None, "errored_cases": None}
    ]


def test_thresholds_of_a_summary_without_thresholds_is_none():
    assert thresholds_of({"judges": {}}) is None


def test_a_job_without_its_mlflow_run_still_answers_and_says_why(client, evalhub, mlflow):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    pending = client.get("/api/usecases/sample/evaluations/job-1", headers=AUTH).json()
    assert (pending["tasks"], pending["tasks_detail"]) == (None, "the job has no MLflow run yet")
    evalhub.complete("job-1", 0.0, "run-1")
    mlflow.files.clear()
    missing = client.get("/api/usecases/sample/evaluations/job-1", headers=AUTH).json()
    assert missing["tasks"] is None
    assert missing["tasks_detail"] == "MLflow answered 404: No such artifact"
    mlflow.artifact_uri = "s3://bucket/runs/run-1/artifacts"
    elsewhere = client.get("/api/usecases/sample/evaluations/job-1", headers=AUTH).json()
    assert "s3://bucket/runs/run-1/artifacts, which the API cannot read" in elsewhere["tasks_detail"]


def test_a_job_of_another_use_case_or_none_is_404(client, evalhub):
    evalhub.json("POST", JOBS, TOKEN, body={"name": "other", "tags": ["usecase:other"]})
    assert client.get("/api/usecases/sample/evaluations/job-1", headers=AUTH).status_code == 404
    response = client.get("/api/usecases/sample/evaluations/job-9", headers=AUTH)
    assert response.status_code == 404
    assert response.json()["detail"] == "EvalHub answered 404: no job job-9"


def test_a_stop_cancels_the_job_and_a_delete_removes_it(client, evalhub):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    evalhub.calls.clear()
    assert client.delete("/api/usecases/sample/evaluations/job-1", headers=AUTH).status_code == 204
    assert evalhub.calls[-1][:4] == ("DELETE", f"{JOBS}/job-1", TOKEN, {"hard_delete": "false"})
    assert client.get("/api/usecases/sample/evaluations/job-1", headers=AUTH).json()["state"] == "cancelled"
    assert client.delete("/api/usecases/sample/evaluations/job-2?delete=true", headers=AUTH).status_code == 204
    assert [job["id"] for job in client.get("/api/usecases/sample/evaluations", headers=AUTH).json()] == ["job-1"]


def test_a_stop_of_an_ended_job_is_evalhubs_409(client, evalhub):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    evalhub.complete("job-1", 0.5, "run-1")
    response = client.delete("/api/usecases/sample/evaluations/job-1", headers=AUTH)
    assert (response.status_code, response.json()) == (409, {"detail": "EvalHub answered 409: the job is completed"})


def test_the_logs_are_evalhubs_text(client):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    response = client.get("/api/usecases/sample/evaluations/job-1/logs", headers=AUTH)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text.endswith("INFO starting evaluation\n")


def test_a_stop_or_the_logs_of_another_use_cases_job_is_404(client, evalhub):
    evalhub.json("POST", JOBS, TOKEN, body={"name": "other", "tags": ["usecase:other"]})
    evalhub.calls.clear()
    assert client.delete("/api/usecases/sample/evaluations/job-1", headers=AUTH).status_code == 404
    assert client.get("/api/usecases/sample/evaluations/job-1/logs", headers=AUTH).status_code == 404
    assert [call[0] for call in evalhub.calls] == ["GET", "GET"]  # nothing deleted, no logs read


def test_evalhubs_refusal_is_passed_on(client, evalhub, monkeypatch):
    def forbidden(*args, **kwargs):
        raise RemoteError(403, "EvalHub answered 403: Forbidden")

    monkeypatch.setattr(evalhub, "json", forbidden)
    response = client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert response.status_code == 403
    assert response.json() == {"detail": "EvalHub answered 403: Forbidden"}


def test_tasks_of_an_empty_summary():
    assert tasks_of({}) == []


def test_evaluations_turn_on_with_evalhub_and_need_the_rest(tmp_path):
    registry = Registry(FileStore(tmp_path))
    assert evaluations_from_env(registry, {}) is None
    with pytest.raises(RuntimeError, match="MLFLOW_URL, FLYWHEEL_NAMESPACE, BUCKET_NAME"):
        evaluations_from_env(registry, {"EVALHUB_URL": "https://evalhub:8443"})
    env = {
        "EVALHUB_URL": "https://evalhub:8443",
        "MLFLOW_URL": "https://mlflow:8443/mlflow",
        "FLYWHEEL_NAMESPACE": "agent-flywheel",
        "BUCKET_NAME": "b",
    }
    evaluations = evaluations_from_env(registry, env)
    assert evaluations.settings == Settings("agent-eval-harness", "b", "flywheel-usecases", "http://gateway.agent-flywheel.svc:4000/v1")
    assert evaluations.evalhub.headers == {"X-Tenant": "agent-flywheel"}
    assert evaluations.mlflow.headers == {"X-MLflow-Workspace": "agent-flywheel"}


def test_without_evaluations_the_routes_do_not_exist(tmp_path):
    client = TestClient(create_app(Registry(FileStore(tmp_path))))
    assert client.get("/api/usecases/sample/evaluations", headers=AUTH).status_code == 404
