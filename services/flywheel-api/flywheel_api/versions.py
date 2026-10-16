"""The content hash of a version and its diff to the version before.

The hash is over the files alone, sorted by path, so the same folder gives
the same hash from an upload or from git. A new version is made only when it
changes (decision 13).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

from .files import Files
from .taskformat import Task, is_task_path, task_file_paths
from .usecase import UseCase


def content_hash(files: Files) -> str:
    """sha256 over each file's path (UTF-8), its length and its bytes, by sorted path."""
    digest = hashlib.sha256()
    for path in sorted(files):
        _add(digest, path, files[path])
    return digest.hexdigest()


def tasks_per_split(tasks: list[Task]) -> dict[str, int]:
    """The count per named split; a task without a split is in none of them."""
    return dict(sorted(Counter(t.data["split"] for t in tasks if "split" in t.data).items()))


def diff(previous: tuple[UseCase, Files] | None, current: tuple[UseCase, Files], number: int | None) -> dict:
    """Tasks added, removed and changed (its six keys or the bytes of its files),
    and the same for every file that is not a task's: a judge or a resource
    moves the scores as much as a task does."""
    before_tasks, before_files = _digests(previous) if previous else ({}, {})
    after_tasks, after_files = _digests(current)
    return {"from": number, "tasks": _compare(before_tasks, after_tasks), "files": _compare(before_files, after_files)}


def _digests(version: tuple[UseCase, Files]) -> tuple[dict[str, str], dict[str, str]]:
    usecase, files = version
    tasks = {task.id: _task_digest(task, files) for task in usecase.tasks}
    others = {path: data for path, data in files.items() if not is_task_path(path, usecase.tasks)}
    return tasks, {path: hashlib.sha256(data).hexdigest() for path, data in others.items()}


def _task_digest(task: Task, files: Files) -> str:
    digest = hashlib.sha256(json.dumps(_canonical(task.data), sort_keys=True, ensure_ascii=False).encode())
    for path in task_file_paths(task, files):
        _add(digest, path, files[path])
    return digest.hexdigest()


def _compare(before: dict[str, str], after: dict[str, str]) -> dict[str, list[str]]:
    return {
        "added": sorted(after.keys() - before.keys()),
        "removed": sorted(before.keys() - after.keys()),
        "changed": sorted(k for k in after.keys() & before.keys() if after[k] != before[k]),
    }


def _add(digest: Any, path: str, data: bytes) -> None:
    digest.update(path.encode() + b"\0" + str(len(data)).encode() + b"\0")
    digest.update(data)


def _canonical(value: Any) -> Any:
    """A parsed YAML value as JSON holds it: keys and non-JSON scalars (dates) as strings."""
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonical(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
