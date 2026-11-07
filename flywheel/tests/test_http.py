"""The loop's HTTP clients against a real local server: the paths, headers
and bodies MLflow and the flywheel API get."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from flywheel_loop import FlywheelError
from flywheel_loop.api import FlywheelAPI
from flywheel_loop.http import Http, HttpError
from flywheel_loop.mlflow import MLflow


class Server:
    """Answers each (method, path) from a table and records every request."""

    def __init__(self, answers):
        self.answers = answers
        self.requests = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def _answer(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                path, _, query = self.path.partition("?")
                server.requests.append((self.command, path, query, dict(self.headers), body))
                status, payload = server.answers.get((self.command, path), (404, {"error_code": "RESOURCE_DOES_NOT_EXIST"}))
                if callable(payload):
                    payload = payload()
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_PUT = _answer

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()


@pytest.fixture
def token(tmp_path):
    path = tmp_path / "token"
    path.write_text("sa-token\n")
    return path


def test_mlflow_creates_a_missing_experiment_and_uploads_a_folder(tmp_path, token):
    server = Server(
        {
            ("POST", "/api/2.0/mlflow/experiments/create"): (200, {"experiment_id": "12"}),
            ("GET", "/api/2.0/mlflow/runs/get"): (200, {"run": {"info": {"artifact_uri": "mlflow-artifacts:/12/r1/artifacts"}}}),
            ("PUT", "/api/2.0/mlflow-artifacts/artifacts/12/r1/artifacts/brain/AGENTS.md"): (200, {}),
            ("PUT", "/api/2.0/mlflow-artifacts/artifacts/12/r1/artifacts/brain/.agents/skills/sev1/SKILL.md"): (200, {}),
        }
    )
    mlflow = MLflow(Http("MLflow", server.url, token, headers={"X-MLflow-Workspace": "agent-flywheel"}))
    assert mlflow.experiment("agent-flywheel-support") == "12"

    folder = tmp_path / "brain"
    (folder / ".agents/skills/sev1").mkdir(parents=True)
    (folder / "AGENTS.md").write_text("Cite.")
    (folder / ".agents/skills/sev1/SKILL.md").write_text("Page.")
    mlflow.upload("r1", folder, "brain")

    puts = [(path, body) for method, path, _, _, body in server.requests if method == "PUT"]
    assert puts == [
        ("/api/2.0/mlflow-artifacts/artifacts/12/r1/artifacts/brain/.agents/skills/sev1/SKILL.md", b"Page."),
        ("/api/2.0/mlflow-artifacts/artifacts/12/r1/artifacts/brain/AGENTS.md", b"Cite."),
    ]
    headers = {name.lower(): value for name, value in server.requests[0][3].items()}
    assert headers["authorization"] == "Bearer sa-token"
    assert headers["x-mlflow-workspace"] == "agent-flywheel"


def test_mlflow_runs_carry_their_tags_metrics_and_clipped_values(token):
    server = Server(
        {
            ("POST", "/api/2.0/mlflow/runs/create"): (200, {"run": {"info": {"run_id": "r9"}}}),
            ("POST", "/api/2.0/mlflow/runs/log-batch"): (200, {}),
            ("POST", "/api/2.0/mlflow/runs/update"): (200, {}),
        }
    )
    mlflow = MLflow(Http("MLflow", server.url, token))
    assert mlflow.start_run("12", "tr-1 v0", {"kind": "iteration"}) == "r9"
    mlflow.log("r9", metrics={"train/score": 1}, tags={"adjuster_change": "x" * 6000})
    mlflow.end_run("r9", "FAILED")

    create, batch, update = (json.loads(r[4]) for r in server.requests)
    assert (create["experiment_id"], create["run_name"], create["tags"]) == ("12", "tr-1 v0", [{"key": "kind", "value": "iteration"}])
    assert batch["metrics"][0] | {"timestamp": 0} == {"key": "train/score", "value": 1.0, "timestamp": 0, "step": 0}
    assert len(batch["tags"][0]["value"]) == 5000
    assert (update["run_id"], update["status"]) == ("r9", "FAILED")


def test_a_refusal_names_the_service_and_its_status(token):
    server = Server({("GET", "/api/usecases/support"): (403, {"detail": "forbidden"})})
    with pytest.raises(HttpError) as caught:
        FlywheelAPI(Http("flywheel API", server.url, token)).version("support")
    assert caught.value.status == 403
    assert "flywheel API GET /api/usecases/support" in str(caught.value)


def test_the_api_reads_the_current_version_and_starts_with_only_what_is_set(token):
    server = Server(
        {
            ("GET", "/api/usecases/support"): (200, {"current": 2}),
            ("GET", "/api/usecases/support/versions/2"): (200, {"number": 2}),
            ("POST", "/api/usecases/support/evaluations"): (201, {"id": "job1"}),
        }
    )
    api = FlywheelAPI(Http("flywheel API", server.url, token))
    assert api.version("support") == {"number": 2}
    api.start("support", version=2, split="train", agent=None, brain="runs:/r1/brain", training="tr-1")
    assert json.loads(server.requests[-1][4]) == {"version": 2, "split": "train", "brain": "runs:/r1/brain", "training": "tr-1"}


def test_wait_polls_until_the_verdicts_are_in(token):
    rows = iter([{"state": "running"}, {"state": "completed", "tasks": None}, {"state": "completed", "tasks": [], "reward": 1.0}])
    server = Server({("GET", "/api/usecases/support/evaluations/job1"): (200, lambda: next(rows))})
    sleeps = []
    api = FlywheelAPI(Http("flywheel API", server.url, token), sleep=sleeps.append)
    assert api.wait("support", "job1", 5, 600)["reward"] == 1.0
    assert sleeps == [5, 5]


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ({"state": "failed", "error": "the adapter exited 1"}, "ended failed: the adapter exited 1"),
        ({"state": "cancelled", "message": "stopped"}, "ended cancelled: stopped"),
    ],
)
def test_wait_ends_on_a_failed_or_stopped_evaluation(token, row, message):
    server = Server({("GET", "/api/usecases/support/evaluations/job1"): (200, row)})
    with pytest.raises(FlywheelError, match=message):
        FlywheelAPI(Http("flywheel API", server.url, token)).wait("support", "job1", 0, 600)


def test_wait_gives_up_after_its_timeout(token):
    server = Server({("GET", "/api/usecases/support/evaluations/job1"): (200, {"state": "running"})})
    clock = iter([0, 100, 700])
    api = FlywheelAPI(Http("flywheel API", server.url, token), sleep=lambda s: None, clock=lambda: next(clock))
    with pytest.raises(FlywheelError, match="did not finish in 600 s"):
        api.wait("support", "job1", 0, 600)
