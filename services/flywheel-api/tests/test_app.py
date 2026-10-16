"""The HTTP routes, through FastAPI's test client."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from helpers import git_repo, tar_gz, zip_bytes

from flywheel_api import app as app_module
from flywheel_api.app import create_app
from flywheel_api.registry import Registry
from flywheel_api.store import FileStore


@pytest.fixture
def client(tmp_path) -> TestClient:
    return TestClient(create_app(Registry(FileStore(tmp_path / "store")), allow_file_urls=True))


def upload(client: TestClient, data: bytes, name: str = "sample.tar.gz", usecase: str = "sample"):
    return client.post(f"/api/usecases/{usecase}/imports", files={"file": (name, data, "application/gzip")})


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_an_upload_then_the_same_upload(client, files):
    assert client.get("/api/usecases").json() == []
    first = upload(client, tar_gz(files))
    assert first.status_code == 201
    assert first.json()["status"] == "created"
    assert first.json()["version"]["number"] == 1
    assert first.json()["version"]["source"] == {"type": "upload", "file": "sample.tar.gz"}
    again = upload(client, zip_bytes(files, top="sample/"), name="sample.zip")
    assert again.status_code == 200
    assert again.json() == {"status": "unchanged", "version": first.json()["version"]}


def test_the_reads(client, files):
    upload(client, tar_gz(files))
    [entry] = client.get("/api/usecases").json()
    assert (entry["name"], entry["title"], entry["current"]) == ("sample", "Product questions", 1)
    assert client.get("/api/usecases/sample").json() == entry
    version = client.get("/api/usecases/sample/versions/1").json()
    assert [t["id"] for t in version["tasks"]] == ["export-data", "pricing", "reset-password"]
    assert [j["name"] for j in version["judges"]] == ["must_mention", "style"]
    assert version["diff"]["tasks"]["added"] == ["export-data", "pricing", "reset-password"]
    assert version["usecase"]["task"]["label"] == "question"


def test_a_git_import_of_the_same_content_is_unchanged(client, files, tmp_path):
    upload(client, tar_gz(files))
    sha = git_repo(files, tmp_path / "repo")
    body = {"git": {"url": f"file://{tmp_path / 'repo'}", "ref": "main", "path": "usecases/sample"}}
    response = client.post("/api/usecases/sample/imports", json=body)
    assert response.status_code == 200
    assert response.json()["status"] == "unchanged"
    other = client.post("/api/usecases/from-git/imports", json=body)
    assert other.status_code == 201
    assert other.json()["version"]["source"]["commit"] == sha


def test_a_refused_import_names_file_and_field(client, files):
    files["tasks/pricing.yaml"] = b"input: {question: q}\nanswer: yes\n"
    response = upload(client, tar_gz(files))
    assert response.status_code == 422
    assert response.json() == {
        "status": "refused",
        "detail": "the import is refused: 1 problem(s)",
        "errors": [
            {
                "file": "tasks/pricing.yaml",
                "field": "answer",
                "line": None,
                "message": "unknown key; a task has only id, split, tags, input, expected, files",
            }
        ],
    }
    assert client.get("/api/usecases").json() == []


def test_hugging_face_comes_later(client):
    response = client.post("/api/usecases/sample/imports", json={"hf": {"dataset": "x/y"}})
    assert response.status_code == 501


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"git": {"url": "https://github.com/x/y"}, "hf": {}},
        {"git": {"url": "https://github.com/x/y", "branch": "main"}},
        {"svn": {}},
    ],
)
def test_a_json_import_names_exactly_one_source(client, body):
    response = client.post("/api/usecases/sample/imports", json=body)
    assert response.status_code == 400


def test_file_urls_only_where_the_tests_allow_them(tmp_path, files):
    git_repo(files, tmp_path / "repo")
    client = TestClient(create_app(Registry(FileStore(tmp_path / "store"))))
    body = {"git": {"url": f"file://{tmp_path / 'repo'}", "path": "usecases/sample"}}
    response = client.post("/api/usecases/sample/imports", json=body)
    assert response.status_code == 400
    assert "https" in response.json()["detail"]


def test_a_url_with_a_password_is_refused(client):
    body = {"git": {"url": "https://lukas:secret@github.com/x/y.git"}}
    response = client.post("/api/usecases/sample/imports", json=body)
    assert response.status_code == 400
    assert "secret" not in response.text


def test_other_bodies(client, files):
    text = client.post("/api/usecases/sample/imports", content=b"x", headers={"content-type": "text/plain"})
    assert text.status_code == 415
    no_file = client.post("/api/usecases/sample/imports", files={"archive": ("a.zip", zip_bytes(files))})
    assert no_file.status_code == 400
    assert upload(client, b"not an archive").status_code == 400


def test_a_too_large_upload(client, files, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_UPLOAD_BYTES", 1000)
    assert upload(client, tar_gz(files) + b"\0" * 2000).status_code == 413


def test_names_and_numbers(client, files):
    assert upload(client, tar_gz(files), usecase="Not_A_Label").status_code == 400
    assert client.get("/api/usecases/none").status_code == 404
    upload(client, tar_gz(files))
    assert client.get("/api/usecases/sample/versions/2").status_code == 404
    assert client.get("/api/usecases/sample/versions/0").status_code == 422
    assert client.get("/api/usecases/sample/versions/one").status_code == 422


def test_there_is_no_delete(client, files):
    upload(client, tar_gz(files))
    assert client.delete("/api/usecases/sample").status_code == 405
    assert client.get("/api/usecases/sample").status_code == 200
