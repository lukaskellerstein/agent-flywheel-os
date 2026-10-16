"""Archives read safely into memory; git imports from a local repository."""

from __future__ import annotations

import io
import os
import subprocess
import tarfile
import zipfile

import pytest
from helpers import git, git_repo, tar_gz, zip_bytes

from flywheel_api import files as files_module
from flywheel_api import sources
from flywheel_api.files import read_folder
from flywheel_api.problems import BadRequest, ImportRefused, TooLarge
from flywheel_api.sources import from_archive, from_git


def tar_with(*members: tarfile.TarInfo, data: bytes = b"x") -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for member in members:
            tar.addfile(member, io.BytesIO(data) if member.isfile() else None)
    return buffer.getvalue()


def member(name: str, kind: bytes = tarfile.REGTYPE, size: int = 1) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.type = kind
    info.size = size if kind == tarfile.REGTYPE else 0
    if kind == tarfile.SYMTYPE:
        info.linkname = "/etc/passwd"
    return info


def refused_files(data: bytes) -> list[str]:
    with pytest.raises(ImportRefused) as refused:
        from_archive("upload.tar.gz", data)
    return [p.file for p in refused.value.problems]


@pytest.mark.parametrize("name", ["../evil.yaml", "/etc/evil.yaml", "a/../../evil.yaml", "a\\..\\evil.yaml"])
def test_a_path_that_leaves_the_folder_is_refused(name):
    assert refused_files(tar_with(member(name))) == [name]


def test_links_in_a_tar_are_refused():
    data = tar_with(member("usecase.yaml"), member("kb", tarfile.SYMTYPE), member("hard", tarfile.LNKTYPE))
    assert refused_files(data) == ["hard", "kb"]


def test_a_symlink_in_a_zip_is_refused():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        link = zipfile.ZipInfo("resources")
        link.external_attr = 0o120777 << 16
        archive.writestr(link, "/etc")
    assert refused_files(buffer.getvalue()) == ["resources"]


def test_a_name_twice_is_refused():
    assert refused_files(tar_with(member("usecase.yaml"), member("./usecase.yaml"))) == ["usecase.yaml"]


def test_what_git_and_macos_add_is_ignored(files):
    junk = dict.fromkeys([".git/config", "__MACOSX/sample/._usecase.yaml", ".DS_Store", "tasks/._pricing.yaml"], b"x")
    assert from_archive("sample.zip", zip_bytes({**files, **junk})).files == files


def test_not_an_archive():
    with pytest.raises(BadRequest, match="neither"):
        from_archive("sample.txt", b"usecase.yaml")


def test_a_broken_archive():
    with pytest.raises(BadRequest, match="cannot be read"):
        from_archive("sample.tar.gz", tar_gz({"usecase.yaml": b"x" * 1000})[:40])


def test_the_size_limit(files, monkeypatch):
    monkeypatch.setattr(files_module, "MAX_BYTES", 100)
    with pytest.raises(TooLarge):
        from_archive("sample.tar.gz", tar_gz(files))


def test_the_file_count_limit(files, monkeypatch):
    monkeypatch.setattr(files_module, "MAX_FILES", 3)
    with pytest.raises(TooLarge):
        from_archive("sample.zip", zip_bytes(files))


def test_a_symlink_in_a_folder_is_refused(files, tmp_path):
    root = tmp_path / "usecase"
    root.mkdir()
    (root / "usecase.yaml").write_bytes(files["usecase.yaml"])
    (root / "resources").symlink_to(tmp_path)
    (root / "eval.yaml").symlink_to(root / "usecase.yaml")
    with pytest.raises(ImportRefused) as refused:
        read_folder(root)
    assert [p.file for p in refused.value.problems] == ["eval.yaml", "resources"]


@pytest.fixture
def repo(files, tmp_path):
    path = tmp_path / "repo"
    return path, git_repo(files, path)


def test_a_git_import_reads_the_folder_at_the_commit(files, repo):
    path, sha = repo
    fetched = from_git(f"file://{path}", "main", "usecases/sample", allow_file_urls=True)
    assert fetched.files == files
    url = f"file://{path}"
    assert fetched.source == {"type": "git", "url": url, "ref": "main", "path": "usecases/sample", "commit": sha}


def test_a_git_import_takes_a_tag_and_the_default_branch(files, repo):
    path, sha = repo
    git(path, "tag", "v1")
    assert from_git(f"file://{path}", "v1", "usecases/sample/", allow_file_urls=True).source["commit"] == sha
    assert from_git(f"file://{path}", None, "./usecases/sample", allow_file_urls=True).files == files


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp/repo",  # only the tests allow file://, and this one does not
        "http://github.com/x/y.git",
        "ssh://git@github.com/x/y.git",
        "git@github.com:x/y.git",
        "https://user:secret@github.com/x/y.git",
        "https://token@github.com/x/y.git",
        "https://github.com/x/y.git?token=secret",
        "https:///x/y.git",
        "ext::sh -c touch% /tmp/pwned",
    ],
)
def test_a_refused_url(url):
    with pytest.raises(BadRequest):
        from_git(url, "main", ".")


@pytest.mark.parametrize("ref", ["-upload-pack=touch /tmp/x", "--help", "a b", ""])
def test_a_refused_ref(repo, ref):
    with pytest.raises(BadRequest, match="not a branch or tag"):
        from_git(f"file://{repo[0]}", ref, ".", allow_file_urls=True)


@pytest.mark.parametrize("path", ["../repo", "/etc", "README.md", "usecases/none"])
def test_a_path_outside_or_missing(repo, path):
    with pytest.raises(BadRequest, match="path"):
        from_git(f"file://{repo[0]}", "main", path, allow_file_urls=True)


def test_an_unknown_branch(repo):
    with pytest.raises(BadRequest, match="git clone failed"):
        from_git(f"file://{repo[0]}", "no-such-branch", ".", allow_file_urls=True)


def test_git_never_sees_the_bucket_key(repo, monkeypatch):
    seen = []
    real_run = subprocess.run

    def spy(command, **kwargs):
        seen.append(kwargs["env"])
        return real_run(command, **kwargs)

    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "not-for-git")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "not-for-git")
    monkeypatch.setattr(sources.subprocess, "run", spy)
    from_git(f"file://{repo[0]}", "main", "usecases/sample", allow_file_urls=True)
    assert seen and all("AWS_SECRET_ACCESS_KEY" not in env and "AWS_ACCESS_KEY_ID" not in env for env in seen)
    assert all(env["GIT_CONFIG_GLOBAL"] == os.devnull and env["GIT_TERMINAL_PROMPT"] == "0" for env in seen)
