"""Where an import's files come from: an uploaded archive, or a folder of a
git repository. Hugging Face comes with phase 4.

An archive is read member by member into memory, never unpacked onto disk. A
git import clones one ref, shallow, into a temp folder that is gone when the
import returns; the version records the commit it resolved to.
"""

from __future__ import annotations

import io
import os
import re
import stat
import subprocess
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from .files import REGULAR_ONLY, Files, FileSet, read_folder, strip_root
from .problems import BadRequest, Problem

GIT_TIMEOUT_S = 120
# A ref is a branch or a tag; a leading '-' would read as an option.
REF = re.compile(r"[A-Za-z0-9._/][A-Za-z0-9._/-]*")
# What the git child process may see of this process's env: never the
# bucket's key, which the pod holds in its env.
PROXY_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY")
GIT_ENV_KEYS = ("PATH", "HOME", "LANG", "LC_ALL", *PROXY_KEYS, *(key.lower() for key in PROXY_KEYS))


@dataclass(frozen=True)
class Fetched:
    files: Files
    source: dict


def from_archive(filename: str, data: bytes) -> Fetched:
    """A .tar.gz or a .zip of the use case folder, with or without the folder itself at its top."""
    found = FileSet()
    if data[:2] == b"\x1f\x8b":
        _read_tar(data, found)
    elif data[:4] in (b"PK\x03\x04", b"PK\x05\x06"):
        _read_zip(data, found)
    else:
        raise BadRequest("the upload is neither a .tar.gz nor a .zip")
    return Fetched(strip_root(found.result()), {"type": "upload", "file": filename})


def _read_tar(data: bytes, found: FileSet) -> None:
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for member in tar:
                if member.isdir():
                    continue
                if not member.isfile():
                    found.problems.append(Problem(member.name, f"a link or special file; {REGULAR_ONLY}"))
                    continue
                if (path := found.path(member.name)) is not None:
                    found.reserve(member.size)
                    found.files[path] = _member_bytes(tar, member)
    except (tarfile.TarError, EOFError, OSError) as exc:
        raise BadRequest(f"the .tar.gz cannot be read: {exc}") from exc


def _member_bytes(tar: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    handle = tar.extractfile(member)
    if handle is None:  # tarfile has no stream for anything but a regular file
        raise BadRequest(f"{member.name} cannot be read from the archive")
    return handle.read()


def _read_zip(data: bytes, found: FileSet) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                if stat.S_ISLNK(info.external_attr >> 16):
                    found.problems.append(Problem(info.filename, f"a symlink; {REGULAR_ONLY}"))
                    continue
                if (path := found.path(info.filename)) is not None:
                    found.reserve(info.file_size)
                    found.files[path] = archive.read(info)
    except (zipfile.BadZipFile, EOFError, OSError) as exc:
        raise BadRequest(f"the .zip cannot be read: {exc}") from exc


def from_git(url: str, ref: str | None, path: str, *, allow_file_urls: bool = False) -> Fetched:
    """The folder *path* of *url* at *ref* (the default branch when None).

    Only https URLs without a user name, a password, a query or a fragment;
    `file://` only when *allow_file_urls* is set, which only the tests do.
    """
    scheme = _check_url(url, allow_file_urls)
    if ref is not None and not REF.fullmatch(ref):
        raise BadRequest(f"ref {ref!r} is not a branch or tag name")
    folder = _check_path(path)
    with tempfile.TemporaryDirectory(prefix="flywheel-git-") as tmp:
        clone = Path(tmp) / "repo"
        _git(scheme, ["clone", "--quiet", "--depth", "1", *(["--branch", ref] if ref else []), "--", url, str(clone)])
        commit = _git(scheme, ["rev-parse", "HEAD"], cwd=clone).strip()
        root = _folder_in(clone, folder)
        files = read_folder(root)
    source = {"type": "git", "url": url, "ref": ref, "path": folder, "commit": commit}
    return Fetched(files, source)


def _check_url(url: str, allow_file_urls: bool) -> str:
    parts = urlsplit(url)
    if parts.scheme == "file" and allow_file_urls:
        return "file"
    if parts.scheme != "https" or not parts.hostname:
        raise BadRequest("a git url is https://<host>/<path>")
    if parts.username is not None or parts.password is not None:
        raise BadRequest("a git url carries no user name or password")
    if parts.query or parts.fragment:
        raise BadRequest("a git url carries no query or fragment")
    return "https"


def _check_path(path: str) -> str:
    pure = PurePosixPath(path or ".")
    if pure.is_absolute() or ".." in pure.parts:
        raise BadRequest(f"path {path!r} must be a folder inside the repository")
    return pure.as_posix()


def _folder_in(clone: Path, folder: str) -> Path:
    root = (clone / folder).resolve()
    if not root.is_relative_to(clone.resolve()) or not root.is_dir():
        raise BadRequest(f"path {folder!r} is not a folder of the repository at that ref")
    return root


def _git(scheme: str, args: list[str], cwd: Path | None = None) -> str:
    """git with no user or system config (no credential helper, no URL rewrite) and only *scheme* allowed."""
    env = {key: os.environ[key] for key in GIT_ENV_KEYS if key in os.environ}
    env |= {"GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    command = ["git", "-c", "protocol.allow=never", "-c", f"protocol.{scheme}.allow=always", *args]
    try:
        done = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True, timeout=GIT_TIMEOUT_S, check=False
        )
    except subprocess.TimeoutExpired as exc:
        raise BadRequest(f"git {args[0]} took longer than {GIT_TIMEOUT_S} s") from exc
    if done.returncode != 0:
        tail = done.stderr.strip().splitlines()[-1:] or [f"exit {done.returncode}"]
        raise BadRequest(f"git {args[0]} failed: {tail[0]}")
    return done.stdout
