"""A use case as a set of files in memory, whatever it came from.

An upload and a git checkout both end as `Files`: a relative POSIX path to its
bytes. Checks, the content hash and the store work on that, so the same folder
gives the same version from either source, and an archive is never unpacked
onto disk. Only regular files count: a symlink is refused, a folder is implied
by its files.
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

from .problems import ImportRefused, Problem, TooLarge

Files = dict[str, bytes]

# Never part of a use case: git's own folder, and what macOS adds to archives
# (`__MACOSX/`, `.DS_Store`, and `._<name>` for extended attributes).
IGNORED_DIRS = frozenset({".git", "__MACOSX"})
IGNORED_FILES = frozenset({".DS_Store"})
APPLE_DOUBLE = "._"
REGULAR_ONLY = "only regular files are imported"

# The whole use case is held in memory, twice during an import (it and the
# version before it), so the pod's memory limit bounds these.
MAX_FILES = 20_000
MAX_BYTES = 256 * 1024 * 1024


class FileSet:
    """Collects the files of one use case, refusing unsafe paths and enforcing the limits."""

    def __init__(self) -> None:
        self.files: Files = {}
        self.problems: list[Problem] = []
        self._bytes = 0

    def path(self, name: str) -> str | None:
        """The clean relative path for *name*; None when it is ignored or refused."""
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or "\\" in name:
            self.problems.append(Problem(name, "the path leaves the use case folder"))
            return None
        parts = pure.parts
        if not parts or ignored(parts):
            return None
        path = pure.as_posix()
        if path in self.files:
            self.problems.append(Problem(path, "appears twice"))
            return None
        return path

    def reserve(self, size: int) -> None:
        """Count *size* bytes and one file against the limits before they are read."""
        self._bytes += size
        if len(self.files) + 1 > MAX_FILES:
            raise TooLarge(f"a use case holds at most {MAX_FILES} files")
        if self._bytes > MAX_BYTES:
            raise TooLarge(f"a use case holds at most {MAX_BYTES // (1024 * 1024)} MiB")

    def result(self) -> Files:
        if self.problems:
            raise ImportRefused(self.problems)
        return self.files


def ignored(parts: tuple[str, ...]) -> bool:
    name = parts[-1]
    return any(p in IGNORED_DIRS for p in parts) or name in IGNORED_FILES or name.startswith(APPLE_DOUBLE)


def strip_root(files: Files) -> Files:
    """An archive of the folder itself holds `<folder>/usecase.yaml`: drop that one top folder."""
    if "usecase.yaml" in files or not files:
        return files
    tops = {path.split("/", 1)[0] for path in files}
    if len(tops) != 1 or not all("/" in path for path in files):
        return files
    top = tops.pop()
    return {path[len(top) + 1 :]: data for path, data in files.items()}


def read_folder(root: Path) -> Files:
    """Every regular file under *root*; a symlink anywhere is refused."""
    found = FileSet()
    for current, dirs, names in os.walk(root, followlinks=False):
        here = Path(current)
        for name in sorted(dirs):
            if (here / name).is_symlink():
                found.problems.append(Problem((here / name).relative_to(root).as_posix(), f"a symlink; {REGULAR_ONLY}"))
                dirs.remove(name)
            elif name in IGNORED_DIRS:
                dirs.remove(name)
        for name in sorted(names):
            _add_file(found, root, here / name)
    return found.result()


def _add_file(found: FileSet, root: Path, file: Path) -> None:
    rel = file.relative_to(root).as_posix()
    if file.is_symlink() or not file.is_file():
        found.problems.append(Problem(rel, f"a symlink or special file; {REGULAR_ONLY}"))
        return
    path = found.path(rel)
    if path is None:
        return
    found.reserve(file.stat().st_size)
    found.files[path] = file.read_bytes()
