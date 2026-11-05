"""The HTTP client to EvalHub and MLflow, against a local server."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from flywheel_api.remote import Remote, RemoteError


class Handler(BaseHTTPRequestHandler):
    seen: list[dict] = []

    def do_GET(self):
        self._answer()

    def do_POST(self):
        self._answer()

    def _answer(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        self.seen.append({"method": self.command, "path": self.path, "headers": dict(self.headers), "body": body})
        routes = {
            "/ok": (200, b'{"items": []}'),
            "/empty": (204, b""),
            "/forbidden": (403, b'{"message": "user cannot create evaluations"}'),
            "/broken": (500, b"panic: something"),
            "/redirect": (302, b""),
        }
        status, data = routes.get(self.path.split("?")[0], (404, b'{"detail": "no route"}'))
        self.send_response(status)
        if status == 302:
            self.send_header("Location", "http://example.com/steal")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def server() -> Iterator[str]:
    Handler.seen = []
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()
    httpd.server_close()


def test_a_call_carries_the_callers_token_its_headers_and_its_body(server):
    remote = Remote("EvalHub", server + "/", headers={"X-Tenant": "agent-flywheel"})
    assert remote.json("POST", "/ok", "t0ken", query={"tags": "usecase:smoke", "limit": 100}, body={"a": 1}) == {"items": []}
    [seen] = Handler.seen
    assert seen["path"] == "/ok?tags=usecase%3Asmoke&limit=100"
    assert seen["headers"]["Authorization"] == "Bearer t0ken"
    assert seen["headers"]["X-Tenant"] == "agent-flywheel"
    assert seen["headers"]["Content-Type"] == "application/json"
    assert json.loads(seen["body"]) == {"a": 1}


def test_an_empty_answer_is_none(server):
    assert Remote("EvalHub", server).json("GET", "/empty", "t") is None


@pytest.mark.parametrize(
    ("path", "status", "detail"),
    [
        ("/forbidden", 403, "EvalHub answered 403: user cannot create evaluations"),
        ("/missing", 404, "EvalHub answered 404: no route"),
        ("/broken", 502, "EvalHub answered 500: panic: something"),
        ("/redirect", 502, "EvalHub answered 302: no body"),
    ],
)
def test_a_refusal_keeps_the_services_words(server, path, status, detail):
    with pytest.raises(RemoteError) as refused:
        Remote("EvalHub", server).json("GET", path, "t")
    assert (refused.value.status, str(refused.value)) == (status, detail)
    assert [seen["path"] for seen in Handler.seen] == [path]  # the redirect was not followed


def test_a_service_that_does_not_answer_is_502():
    with pytest.raises(RemoteError) as refused:
        Remote("MLflow", "http://127.0.0.1:9", timeout=2).raw("GET", "/x", "t")
    assert refused.value.status == 502
    assert str(refused.value).startswith("MLflow did not answer:")
