"""The evaluation routes, with EvalHub and MLflow faked in their real shapes
(read from cluster-nm8mw on 2026-11-05: EvalHub 4315523, ODH's MLflow)."""

from __future__ import annotations

import copy
import json

import pytest
import yaml
from fastapi.testclient import TestClient
from helpers import tar_gz

from flywheel_api.agents import Agents
from flywheel_api.app import create_app
from flywheel_api.evaluations import JOBS, Evaluations, Settings, evaluations_from_env
from flywheel_api.registry import Registry
from flywheel_api.remote import RemoteError
from flywheel_api.results import judges_of, tasks_of, thresholds_of
from flywheel_api.gateway import Gateway
from flywheel_api.store import FileStore
from test_agents import CODEX, GATEWAY

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
outputs:
  - path: output
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
        if path == "/api/2.0/mlflow/artifacts/list":
            return self._listing(query["path"])
        assert path == "/api/2.0/mlflow/runs/get"
        return {"run": {"info": {"run_id": query["run_id"], "artifact_uri": self.artifact_uri}}}

    def _listing(self, folder: str) -> dict:
        """MLflow's artifacts/list: the entries right under *folder*, dirs marked."""
        root = "/api/2.0/mlflow-artifacts/artifacts/" + self.artifact_uri.removeprefix("mlflow-artifacts:/") + "/"
        entries = {}
        for key in self.files:
            path = key.removeprefix(root)
            if path.startswith(folder + "/"):
                child = folder + "/" + path[len(folder) + 1 :].split("/")[0]
                entries[child] = {"path": child, "is_dir": child != path}
        return {"files": sorted(entries.values(), key=lambda entry: entry["path"])} if entries else {}

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


CLAUDE = {
    "name": "claude-code",
    "title": "Claude Code",
    "runner": {
        "type": "claude-code",
        "permission_mode": "bypassPermissions",
        "env": {"ANTHROPIC_BASE_URL": "http://gateway.agent-flywheel.svc:4000", "ANTHROPIC_AUTH_TOKEN": "gateway-takes-no-key"},
    },
    "brain": {"instructions_file": "CLAUDE.md", "skills_folder": ".claude/skills/"},
    "models": ["enmaas-glm-5-3"],
    "default_model": "enmaas-glm-5-3",
}
# The gateway fixture's prices of the agents' models, per million tokens.
PRICING = {
    "enmaas-glm-5-3": {"input_per_mtok": 0, "output_per_mtok": 0},
    "enmaas-gpt-5-mini": {"input_per_mtok": 0.25, "output_per_mtok": 2.0},
}
CODEX_RUNNER = {**CODEX["runner"], "pricing": PRICING}


def _service(tmp_path, evalhub, mlflow) -> TestClient:
    """The API with Codex and Claude Code in AI hub › Agents."""
    store = FileStore(tmp_path / "store")
    registry = Registry(store)
    agents = Agents(store, Gateway(GATEWAY))
    for agent in (CODEX, CLAUDE):
        agents.add(copy.deepcopy(agent))
    return TestClient(create_app(registry, Evaluations(registry, agents, evalhub, mlflow, SETTINGS), agents))


@pytest.fixture
def client(tmp_path, files, evalhub, mlflow) -> TestClient:
    """The sample use case imported twice: version 2 adds a split-less change."""
    client = _service(tmp_path, evalhub, mlflow)
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
        "name": "sample-v1-validation-codex-enmaas-glm-5-3",
        "tags": ["agent-flywheel", "usecase:sample", "version:1", "split:validation", "agent:codex"],
        "model": {"name": "enmaas-glm-5-3", "url": "http://gateway.agent-flywheel.svc:4000/v1"},
        "benchmarks": [
            {
                "id": "eval-run",
                "provider_id": "agent-eval-harness",
                "parameters": {"split": "validation", "runner": CODEX_RUNNER},
                "test_data_ref": {
                    "s3": {
                        "bucket": "flywheel-usecases-1234",
                        "key": "usecases/sample/versions/1/",
                        "secret_ref": "flywheel-usecases",
                    }
                },
            }
        ],
        "experiment": {
            "name": "agent-flywheel-sample",
            "tags": [
                {"key": "usecase", "value": "sample"},
                {"key": "usecase_version", "value": "1"},
                {"key": "split", "value": "validation"},
                {"key": "agent", "value": "codex"},
            ],
        },
        "pass_criteria": {"threshold": 0.6},
    }
    started = response.json()
    assert (started["id"], started["version"], started["split"], started["state"]) == ("job-1", 1, "validation", "pending")
    assert (started["agent"], started["thresholds"], started["tasks_detail"]) == ("codex", None, "the job has no MLflow run yet")
    assert started["task_count"] == 1


def test_a_version_says_what_eval_yaml_sets_for_a_run(client):
    version = client.get("/api/usecases/sample/versions/2").json()
    assert (version["agent"], version["model"]) == ("codex", "enmaas-glm-5-3")
    assert version["reward"] == {"weights": {"must_mention": 0.7, "style": 0.3}}
    assert version["thresholds"] == {"reward": {"min_mean": 0.6, "min_per_case": 0.5}, "must_mention": {"min_pass_rate": 1.0}}


def test_without_a_reward_min_mean_evalhub_keeps_its_own_pass_criteria(tmp_path, files, evalhub, mlflow):
    client = _service(tmp_path, evalhub, mlflow)
    _upload(client, files)
    response = client.post("/api/usecases/sample/evaluations", json={"agent": "codex"}, headers=AUTH)
    assert response.status_code == 201, response.text
    assert "pass_criteria" not in evalhub.calls[0][4]


def test_a_bare_start_takes_the_current_version_every_task_and_the_eval_model(client, evalhub):
    response = client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert response.status_code == 201, response.text
    body = evalhub.calls[0][4]
    assert body["name"] == "sample-v2-all-codex-enmaas-glm-5-3"
    assert body["benchmarks"][0]["parameters"] == {"runner": CODEX_RUNNER}
    assert body["benchmarks"][0]["test_data_ref"]["s3"]["key"] == "usecases/sample/versions/2/"
    assert "split:all" not in body["tags"]
    other = client.post("/api/usecases/sample/evaluations", json={"model": "enmaas-gpt-5-mini"}, headers=AUTH)
    assert evalhub.calls[1][4]["model"]["name"] == "enmaas-gpt-5-mini", other.text


def test_another_agent_brings_its_own_runner_block(client, evalhub):
    response = client.post("/api/usecases/sample/evaluations", json={"agent": "claude-code"}, headers=AUTH)
    assert response.status_code == 201, response.text
    body = evalhub.calls[0][4]
    assert body["benchmarks"][0]["parameters"]["runner"] == {
        **CLAUDE["runner"],
        "pricing": {"enmaas-glm-5-3": PRICING["enmaas-glm-5-3"]},
    }
    assert "agent:claude-code" in body["tags"]
    assert body["name"] == "sample-v2-all-claude-code-enmaas-glm-5-3"
    assert response.json()["agent"] == "claude-code"


def test_the_agents_default_model_when_eval_yaml_names_one_it_may_not_use(tmp_path, files, evalhub, mlflow):
    client = _service(tmp_path, evalhub, mlflow)
    files["eval.yaml"] += b"\nmodels:\n  skill: enmaas-gpt-5-mini\n"
    _upload(client, files)
    client.post("/api/usecases/sample/evaluations", json={"agent": "claude-code"}, headers=AUTH)
    assert evalhub.calls[0][4]["model"]["name"] == "enmaas-glm-5-3"


@pytest.mark.parametrize(
    ("request_body", "detail"),
    [
        ({"agent": "cursor"}, "no agent 'cursor' in AI hub › Agents"),
        ({"agent": "claude-code", "model": "enmaas-gpt-5-mini"}, "agent 'claude-code' may not use 'enmaas-gpt-5-mini'; its models: enmaas-glm-5-3"),
        ({"model": "enmaas-gemini"}, "agent 'codex' may not use 'enmaas-gemini'; its models: enmaas-glm-5-3, enmaas-gpt-5-mini"),
    ],
)
def test_only_a_listed_agent_with_one_of_its_models_runs(client, evalhub, request_body, detail):
    response = client.post("/api/usecases/sample/evaluations", json=request_body, headers=AUTH)
    assert (response.status_code, response.json()["detail"]) == (422, detail)
    assert evalhub.calls == []


def test_a_model_the_gateway_dropped_does_not_run(client, evalhub, monkeypatch):
    monkeypatch.setattr(Gateway, "names", lambda self: ["enmaas-gpt-5-mini"])
    response = client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert (response.status_code, response.json()["detail"]) == (422, "the gateway no longer routes 'enmaas-glm-5-3'")
    assert evalhub.calls == []


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


def test_a_start_without_an_agent_for_eval_yamls_runner_is_refused(tmp_path, files, evalhub, mlflow):
    client = _service(tmp_path, evalhub, mlflow)
    _upload(client, files)
    response = client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert (response.status_code, response.json()["detail"]) == (422, "eval.yaml names no runner.type: pick an agent")
    files["eval.yaml"] += b"\nrunner:\n  type: opencode\n"
    _upload(client, files)
    response = client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert response.json()["detail"] == "no agent in AI hub › Agents runs 'opencode', which eval.yaml names: add one, or pick an agent"
    assert evalhub.calls == []


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
    assert {row["task_count"] for row in rows.values()} == {3}  # every task of the version


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


def test_a_tasks_results_are_every_scored_run_of_its_version(client, evalhub):
    for version in (2, 2, 1):
        client.post("/api/usecases/sample/evaluations", json={"version": version}, headers=AUTH)
    evalhub.complete("job-1", 0.5, "run-1")
    evalhub.complete("job-3", 0.5, "run-1")  # version 1: not on this page
    response = client.get("/api/usecases/sample/versions/2/tasks/export-data/results", headers=AUTH)
    assert response.status_code == 200, response.text
    [row] = response.json()  # job-2 has no summary yet
    assert (row["evaluation"]["id"], row["evaluation"]["agent"], row["reward"]) == ("job-1", "codex", 0.0)
    assert list(row["judges"]) == ["must_mention", "style"]
    assert row["judges"]["must_mention"] == {"value": False, "rationale": "missing: CSV", "error": None}
    assert row["evaluation"]["thresholds"]["checks"] == CHECKS
    assert client.get("/api/usecases/sample/versions/2/tasks/nothing/results", headers=AUTH).json() == []
    assert client.get("/api/usecases/sample/versions/9/tasks/export-data/results", headers=AUTH).status_code == 404
    assert client.get("/api/usecases/sample/versions/2/tasks/export-data/results").status_code == 401


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
    agents = Agents(FileStore(tmp_path), Gateway(GATEWAY))
    assert evaluations_from_env(registry, agents, {}) is None
    with pytest.raises(RuntimeError, match="MLFLOW_URL, FLYWHEEL_NAMESPACE, BUCKET_NAME"):
        evaluations_from_env(registry, agents, {"EVALHUB_URL": "https://evalhub:8443"})
    env = {
        "EVALHUB_URL": "https://evalhub:8443",
        "MLFLOW_URL": "https://mlflow:8443/mlflow",
        "FLYWHEEL_NAMESPACE": "agent-flywheel",
        "BUCKET_NAME": "b",
    }
    evaluations = evaluations_from_env(registry, agents, env)
    assert evaluations.settings == Settings("agent-eval-harness", "b", "flywheel-usecases", "http://gateway.agent-flywheel.svc:4000/v1")
    assert evaluations.evalhub.headers == {"X-Tenant": "agent-flywheel"}
    assert evaluations.mlflow.headers == {"X-MLflow-Workspace": "agent-flywheel"}


def test_without_evaluations_the_routes_do_not_exist(tmp_path):
    client = TestClient(create_app(Registry(FileStore(tmp_path))))
    assert client.get("/api/usecases/sample/evaluations", headers=AUTH).status_code == 404


def test_a_model_without_a_gateway_price_gets_none(client, evalhub, monkeypatch):
    real = Gateway.models

    def unpriced_mini(self):
        return [{**m, "price_output": None} if m["name"] == "enmaas-gpt-5-mini" else m for m in real(self)]

    monkeypatch.setattr(Gateway, "models", unpriced_mini)
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    assert evalhub.calls[0][4]["benchmarks"][0]["parameters"]["runner"]["pricing"] == {
        "enmaas-glm-5-3": PRICING["enmaas-glm-5-3"]
    }


CASE = "/api/2.0/mlflow-artifacts/artifacts/workspaces/agent-flywheel/2/run-1/artifacts/run/cases/export-data"
WORKSPACE = "/tmp/agent-eval-harness-x/tmp/agent-eval/sample/job-1_0/cases/export-data"
# events.json as the harness writes it, one Claude Code turn and one Codex shell call.
EVENTS = [
    {"type": "system", "subtype": "init", "model": "enmaas-glm-5-3"},
    {"type": "assistant", "text": "", "tools": [{"name": "Grep", "id": "t1", "input": {"pattern": "export", "path": f"{WORKSPACE}/resources/kb"}}]},
    {"type": "tool_result", "tool_use_id": "t1", "tool_name": "Grep", "content": "kb/002-export.md", "is_error": False},
    {"type": "assistant", "text": "", "tools": [{"name": "Read", "id": "t2", "input": {"file_path": f"{WORKSPACE}/screen.txt"}}]},
    {"type": "tool_result", "tool_use_id": "t2", "tool_name": "Read", "content": "no such file", "is_error": True},
    {"type": "assistant", "text": "", "tools": [{"name": "Bash", "id": "t3", "input": {"command": "/usr/bin/bash -lc 'cat output/answer.md'"}}]},
    {"type": "assistant", "text": "Answer written to output/answer.md.", "tools": []},
    {"type": "result", "cost_usd": 0.0, "num_turns": 4},
]
RUN_RESULT = {
    "exit_code": 0,
    "duration_s": 27.5,
    "token_usage": {"input": 3107, "output": 769, "cache_read": 45568},
    "cost_usd": 0.0,
    "num_turns": 4,
    "model": "enmaas-glm-5-3",
    "message_ids": ["msg_1"],
    "cost_source": "harness:estimate",
    "error_class": None,
}
ANSWER = "Reports export at most 10,000 rows, as CSV."


def _completed_task_run(client, evalhub, mlflow) -> None:
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    evalhub.complete("job-1", 0.5, "run-1")
    mlflow.files.update({
        f"{CASE}/run_result.json": json.dumps(RUN_RESULT).encode(),
        f"{CASE}/events.json": json.dumps(EVENTS).encode(),
        f"{CASE}/output/answer.md": ANSWER.encode(),
        f"{CASE}/output/stdout.log": b"the runner's own log",
    })


def test_one_task_has_its_answer_steps_and_cost(client, evalhub, mlflow):
    _completed_task_run(client, evalhub, mlflow)
    response = client.get("/api/usecases/sample/evaluations/job-1/tasks/export-data", headers=AUTH)
    assert response.status_code == 200, response.text
    task = response.json()
    assert (task["evaluation"]["id"], task["evaluation"]["agent"]) == ("job-1", "codex")
    assert task["task"]["reward"] == 0.0
    assert task["task"]["judges"]["must_mention"] == {"value": False, "rationale": "missing: CSV", "error": None}
    assert task["answer"] == [{"path": "output/answer.md", "size": len(ANSWER), "text": ANSWER, "truncated": False}]
    assert task["run"] == {
        "exit_code": 0,
        "duration_s": 27.5,
        "num_turns": 4,
        "model": "enmaas-glm-5-3",
        "cost_usd": 0.0,
        "cost_source": "harness:estimate",
        "error_class": None,
        "tokens": {"input": 3107, "output": 769, "cache_read": 45568, "cache_create": None},
    }
    assert task["steps"] == [
        {"kind": "tool", "tool": "Grep", "input": "export resources/kb", "error": False},
        {"kind": "tool", "tool": "Read", "input": "screen.txt", "error": True},
        {"kind": "tool", "tool": "Bash", "input": "cat output/answer.md", "error": False},
        {"kind": "message", "text": "Answer written to output/answer.md."},
    ]


def test_a_finished_tasks_files_are_read_once(client, evalhub, mlflow):
    _completed_task_run(client, evalhub, mlflow)
    client.get("/api/usecases/sample/evaluations/job-1/tasks/export-data", headers=AUTH)
    reads = len(mlflow.calls)
    client.get("/api/usecases/sample/evaluations/job-1/tasks/export-data", headers=AUTH)
    assert not [call for call in mlflow.calls[reads:] if "/cases/" in call[1] or "artifacts/list" in call[1]]


def test_a_task_without_its_trace_still_has_its_verdicts(client, evalhub, mlflow):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    evalhub.complete("job-1", 0.5, "run-1")
    task = client.get("/api/usecases/sample/evaluations/job-1/tasks/pricing", headers=AUTH).json()
    assert (task["task"]["reward"], task["answer"], task["run"], task["steps"]) == (1.0, [], None, None)


@pytest.mark.parametrize(
    ("task_id", "status", "detail"),
    [
        ("reset-password", 404, "evaluation 'job-1' has no task 'reset-password'"),
        (".env", 404, "evaluation 'job-1' has no task '.env'"),
    ],
)
def test_a_task_the_run_did_not_score_is_404(client, evalhub, mlflow, task_id, status, detail):
    _completed_task_run(client, evalhub, mlflow)
    response = client.get(f"/api/usecases/sample/evaluations/job-1/tasks/{task_id}", headers=AUTH)
    assert (response.status_code, response.json()["detail"]) == (status, detail)


def test_a_task_of_a_job_without_results_is_422(client, evalhub):
    client.post("/api/usecases/sample/evaluations", headers=AUTH)
    response = client.get("/api/usecases/sample/evaluations/job-1/tasks/export-data", headers=AUTH)
    assert (response.status_code, response.json()["detail"]) == (
        422,
        "evaluation 'job-1' has no results yet: the job has no MLflow run yet",
    )
