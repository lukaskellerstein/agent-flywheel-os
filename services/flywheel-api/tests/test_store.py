"""Both stores keep one contract; the S3 one runs against moto, with no network."""

from __future__ import annotations

import logging

import pytest
import yaml
from moto import mock_aws

from flywheel_api.registry import Registry
from flywheel_api.store import FileStore, S3Store, s3_client, store_from_env

BUCKET = "flywheel-usecases-1a2b3c"


@pytest.fixture
def aws_env(monkeypatch):
    """Fake credentials, so no real ones are ever read; moto accepts any."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    for name in ("AWS_PROFILE", "AWS_SESSION_TOKEN", "S3_ENDPOINT_URL", "BUCKET_HOST", "BUCKET_PORT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("FLYWHEEL_STORE_DIR", raising=False)


@pytest.fixture
def s3_store(aws_env):
    with mock_aws():
        client = s3_client(None, "us-east-1")
        client.create_bucket(Bucket=BUCKET)
        yield S3Store(client, BUCKET)


@pytest.fixture(params=["file", "s3"])
def store(request, tmp_path):
    if request.param == "file":
        return FileStore(tmp_path / "store")
    return request.getfixturevalue("s3_store")


def test_get_and_put(store):
    assert store.get("usecases/a/usecase.json") is None
    store.put("usecases/a/usecase.json", b"{}")
    store.put("usecases/a/usecase.json", b'{"current": 1}')
    assert store.get("usecases/a/usecase.json") == b'{"current": 1}'


def test_keys_and_folders(store):
    for key in ("usecases/a/usecase.json", "usecases/a/versions/1/tasks/t.yaml", "usecases/b/usecase.json", "other/x"):
        store.put(key, b"x")
    assert store.keys("usecases/a/") == ["usecases/a/usecase.json", "usecases/a/versions/1/tasks/t.yaml"]
    assert store.keys("usecases/none/") == []
    assert store.folders("usecases/") == ["a", "b"]
    assert store.folders("usecases/a/versions/") == ["1"]
    assert store.folders("missing/") == []


def test_delete(store):
    store.put("usecases/a/versions/2/stray", b"x")
    store.delete("usecases/a/versions/2/stray")
    assert store.keys("usecases/a/") == []


def test_a_file_store_key_cannot_leave_its_folder(tmp_path):
    with pytest.raises(ValueError):
        FileStore(tmp_path / "store").put("../outside", b"x")


def test_the_registry_over_s3(s3_store, files):
    registry = Registry(s3_store)
    assert registry.import_files("sample", files, {"type": "upload", "file": "s.zip"}).status == "created"
    assert registry.import_files("sample", files, {"type": "upload", "file": "s.zip"}).status == "unchanged"
    data = yaml.safe_load(files["tasks/pricing.yaml"])
    data["expected"]["must_mention"].append("no card needed")
    files["tasks/pricing.yaml"] = yaml.safe_dump(data).encode()
    assert registry.import_files("sample", files, {"type": "upload", "file": "s.zip"}).version["number"] == 2
    old = {t["id"]: t for t in registry.version("sample", 1)["tasks"]}
    assert old["pricing"]["expected"]["must_mention"] == ["five seats"]
    assert [e["current"] for e in registry.list()] == [2]
    assert "usecases/sample/versions/1/hidden/style.md" in s3_store.keys("usecases/sample/versions/1/")


def test_the_env_names_a_folder(tmp_path, aws_env, monkeypatch):
    monkeypatch.setenv("FLYWHEEL_STORE_DIR", str(tmp_path))
    assert isinstance(store_from_env(), FileStore)


def test_the_endpoint_from_env_first(aws_env):
    env = {"BUCKET_NAME": BUCKET, "S3_ENDPOINT_URL": "http://s3.openshift-storage.svc:80"}
    store = store_from_env({**env, "BUCKET_HOST": "elsewhere", "BUCKET_PORT": "443"})
    assert isinstance(store, S3Store)
    assert store.bucket == BUCKET
    assert store.client.meta.endpoint_url == "http://s3.openshift-storage.svc:80"


@pytest.mark.parametrize(
    "port, url",
    [
        ("80", "http://s3.openshift-storage.svc:80"),
        ("443", "https://s3.openshift-storage.svc:443"),
        (None, "https://s3.openshift-storage.svc:443"),
    ],
)
def test_the_endpoint_from_the_claims_configmap(aws_env, port, url):
    env = {"BUCKET_NAME": BUCKET, "BUCKET_HOST": "s3.openshift-storage.svc", "BUCKET_REGION": ""}
    if port:
        env["BUCKET_PORT"] = port
    store = store_from_env(env)
    assert isinstance(store, S3Store)
    assert store.client.meta.endpoint_url == url
    assert store.client.meta.region_name == "us-east-1"


def test_no_bucket_no_store(aws_env):
    with pytest.raises(RuntimeError, match="BUCKET_NAME"):
        store_from_env({})


def test_the_key_is_never_logged(aws_env, monkeypatch, caplog):
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "s3cr3t-never-logged")
    with caplog.at_level(logging.DEBUG, logger="flywheel_api"):
        store_from_env({"BUCKET_NAME": BUCKET, "S3_ENDPOINT_URL": "http://s3.openshift-storage.svc:80"})
    assert caplog.text and "s3cr3t-never-logged" not in caplog.text
