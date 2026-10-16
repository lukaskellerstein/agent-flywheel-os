"""Archives and git repositories made from a use case's files, for the tests."""

from __future__ import annotations

import io
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

from flywheel_api.files import Files
from flywheel_api.problems import ImportRefused
from flywheel_api.usecase import check

FIXTURE = Path(__file__).parent / "fixtures" / "sample"


def tar_gz(files: Files, top: str = "") -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path, data in sorted(files.items()):
            info = tarfile.TarInfo(f"{top}{path}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def zip_bytes(files: Files, top: str = "") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, data in sorted(files.items()):
            archive.writestr(f"{top}{path}", data)
    return buffer.getvalue()


def write_folder(files: Files, root: Path) -> Path:
    for path, data in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(data)
    return root


def git(repo: Path, *args: str) -> str:
    config = ["-c", "user.name=Test", "-c", "user.email=test@example.com", "-c", "init.defaultBranch=main"]
    return subprocess.run(["git", *config, *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def git_repo(files: Files, repo: Path, folder: str = "usecases/sample") -> str:
    """A repository holding *files* in *folder*, one commit on `main`; its SHA."""
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "--quiet")
    write_folder(files, repo / folder)
    (repo / "README.md").write_text("A repository with a use case in it.\n")
    git(repo, "add", ".")
    git(repo, "commit", "--quiet", "-m", "the sample use case")
    return git(repo, "rev-parse", "HEAD")


def refusal(files: Files) -> list[tuple[str, str | None]]:
    """The (file, field) of every problem `check` finds; fails the test if it finds none."""
    with pytest.raises(ImportRefused) as refused:
        check(files)
    return [(p.file, p.field) for p in refused.value.problems]
