"""The task format of decision 13: one YAML file per task in `tasks/`, or one
JSON line per task in `tasks.jsonl`.

    id: sno-registry-removed      # unique; default: the YAML file's name
    split: train                  # optional
    tags: [plain-fix]             # optional
    input: {ticket: "Hi, ..."}    # what the agent gets; any keys
    expected: {must_mention: []}  # optional; what only the judges see; any keys
    files: [screenshot.png]       # optional; files for the agent, in the task's folder

The rules are the harness's reader's (C19, `agent_eval/task_format.py` on the
fork's `flywheel-integration`), so a version this API accepts is one the
harness reads: the same six keys, the same id pattern, a task's files in
`tasks/<id>/` (or `<id>/` beside `tasks.jsonl`), and the names its converter
writes into a case folder are not a task's files. The keys inside `input`
and `expected` stay free here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from .files import Files
from .problems import Problem, read_yaml

TASK_KEYS = ("id", "split", "tags", "input", "expected", "files")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
TASKS_DIR = "tasks"
TASKS_JSONL = "tasks.jsonl"
YAML_SUFFIXES = (".yaml", ".yml")
# What the harness's converter writes into a task's case folder (C19).
CONVERTED_FILES = frozenset({"input.yaml", "input.yml", "input.json", "annotations.yaml", "task.yaml"})
# Beside tasks.jsonl a task's files sit in `<id>/` at the use case's top
# level, so an id must not name one of the use case's own folders: a task
# called `hidden` would hand the judges' files to the agent.
USECASE_DIRS = frozenset({TASKS_DIR, "resources", "hidden"})


@dataclass(frozen=True)
class Task:
    id: str
    data: dict  # the six keys, in the contract's order, `id` filled in
    file: str  # where it came from
    line: int | None  # its line in tasks.jsonl
    files_dir: str  # the folder its `files` are relative to


@dataclass(frozen=True)
class _Raw:
    data: Any
    file: str
    line: int | None
    default_id: str | None


def read_tasks(files: Files, problems: list[Problem]) -> list[Task]:
    """Every task of the use case, sorted by id; each problem is appended."""
    has_dir = any(path.startswith(f"{TASKS_DIR}/") for path in files)
    if has_dir and TASKS_JSONL in files:
        problems.append(Problem(TASKS_JSONL, f"a use case holds {TASKS_DIR}/ or {TASKS_JSONL}, not both"))
        return []
    before = len(problems)
    if TASKS_JSONL in files:
        raw, base, origin = _jsonl_entries(files, problems), "", TASKS_JSONL
    elif has_dir:
        raw, base, origin = _yaml_entries(files, problems), f"{TASKS_DIR}/", f"{TASKS_DIR}/"
    else:
        where = f"{TASKS_DIR}/ (one YAML file per task) or {TASKS_JSONL}"
        problems.append(Problem(f"{TASKS_DIR}/", f"no tasks: a use case holds {where}"))
        return []
    if not raw and len(problems) == before:
        problems.append(Problem(origin, "no tasks"))
    tasks = _unique(_validate_all(raw, base, files, problems), problems)
    if base:
        _check_task_dirs(files, raw, problems)
    return sorted(tasks, key=lambda t: t.id)


def task_file_paths(task: Task, files: Files) -> list[str]:
    """The paths of the files a task lists, a listed folder expanded to its files."""
    paths: list[str] = []
    for rel in task.data.get("files", []):
        full = f"{task.files_dir}/{PurePosixPath(rel).as_posix()}"
        paths += [full] if full in files else sorted(p for p in files if p.startswith(f"{full}/"))
    return paths


def is_task_path(path: str, tasks: list[Task]) -> bool:
    """Whether *path* belongs to the tasks rather than to the rest of the use case."""
    if path == TASKS_JSONL or path.startswith(f"{TASKS_DIR}/"):
        return True
    return any(path.startswith(f"{t.files_dir}/") for t in tasks)


def _yaml_entries(files: Files, problems: list[Problem]) -> list[_Raw]:
    entries = []
    for path in sorted(files):
        rel = path[len(TASKS_DIR) + 1 :]
        if not path.startswith(f"{TASKS_DIR}/") or "/" in rel or rel.startswith("."):
            continue
        if not rel.endswith(YAML_SUFFIXES):
            problems.append(Problem(path, f"not a task: {TASKS_DIR}/ holds <id>.yaml files and <id>/ folders"))
            continue
        data = read_yaml(files, path, problems)
        if data is not None:
            entries.append(_Raw(data, path, None, PurePosixPath(rel).stem))
    return entries


def _jsonl_entries(files: Files, problems: list[Problem]) -> list[_Raw]:
    try:
        lines = files[TASKS_JSONL].decode("utf-8").splitlines()
    except UnicodeDecodeError:
        problems.append(Problem(TASKS_JSONL, "not UTF-8 text"))
        return []
    entries = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            entries.append(_Raw(json.loads(line), TASKS_JSONL, number, None))
        except json.JSONDecodeError as exc:
            problems.append(Problem(TASKS_JSONL, f"not valid JSON: {exc.msg}", line=number))
    return entries


def _validate_all(raw: list[_Raw], base: str, files: Files, problems: list[Problem]) -> list[Task]:
    tasks = (_validate(entry, base, files, problems) for entry in raw)
    return [task for task in tasks if task is not None]


def _validate(entry: _Raw, base: str, files: Files, problems: list[Problem]) -> Task | None:
    def problem(message: str, field: str | None = None) -> None:
        problems.append(Problem(entry.file, message, field, entry.line))

    data = entry.data
    if not isinstance(data, dict):
        problem("a task must be a mapping")
        return None
    before = len(problems)
    _check_keys(data, entry.default_id, base, problem)
    if len(problems) > before:
        return None
    task_id = data.get("id", entry.default_id)
    files_dir = f"{base}{task_id}"
    _check_files(data.get("files", []), files_dir, files, problem)
    if len(problems) > before:
        return None
    data = {"id": task_id, **data}
    return Task(task_id, {k: data[k] for k in TASK_KEYS if k in data}, entry.file, entry.line, files_dir)


def _check_keys(data: dict, default_id: str | None, base: str, problem) -> None:
    for key in sorted(set(data) - set(TASK_KEYS), key=str):
        problem(f"unknown key; a task has only {', '.join(TASK_KEYS)}", str(key))
    _check_id(data.get("id", default_id), base, problem)
    if "input" not in data:
        problem("required: what the agent gets", "input")
    elif not isinstance(data["input"], dict):
        problem("must be a mapping", "input")
    if "expected" in data and not isinstance(data["expected"], dict):
        problem("must be a mapping", "expected")
    if "split" in data and not (isinstance(data["split"], str) and data["split"]):
        problem("must be a non-empty string", "split")
    if "tags" in data and not (isinstance(data["tags"], list) and all(isinstance(t, str) for t in data["tags"])):
        problem("must be a list of strings", "tags")


def _check_id(task_id: Any, base: str, problem) -> None:
    if task_id is None:
        problem("required in a JSONL line, which has no file name to default to", "id")
    elif not isinstance(task_id, str) or not ID.fullmatch(task_id):
        problem(f"must match {ID.pattern}: it names the task's folder", "id")
    elif not base and task_id in USECASE_DIRS:
        problem(f"names a folder of the use case ({', '.join(sorted(USECASE_DIRS))})", "id")


def _check_files(listed: Any, files_dir: str, files: Files, problem) -> None:
    if not isinstance(listed, list) or not all(isinstance(f, str) for f in listed):
        problem("must be a list of paths", "files")
        return
    for index, rel in enumerate(listed):
        field = f"files[{index}]"
        pure = PurePosixPath(rel)
        if not rel or pure.is_absolute() or ".." in pure.parts or pure.as_posix() == ".":
            problem(f"must be a path inside {files_dir}/", field)
        elif pure.parts[0] in CONVERTED_FILES:
            problem("a name the harness writes into the task's case folder", field)
        elif not _exists(f"{files_dir}/{pure.as_posix()}", files):
            problem(f"not found: {files_dir}/{pure.as_posix()}", field)


def _exists(path: str, files: Files) -> bool:
    return path in files or any(p.startswith(f"{path}/") for p in files)


def _unique(tasks: list[Task], problems: list[Problem]) -> list[Task]:
    seen: dict[str, Task] = {}
    for task in tasks:
        first = seen.get(task.id)
        if first is None:
            seen[task.id] = task
            continue
        where = f"{first.file}:{first.line}" if first.line else first.file
        problems.append(Problem(task.file, f"duplicate: {where} has the same id", "id", task.line))
    return list(seen.values())


def _check_task_dirs(files: Files, raw: list[_Raw], problems: list[Problem]) -> None:
    """A folder in tasks/ holds the files of the task with its id; any other folder is refused
    (the harness would read it as a case folder beside task files, an error there)."""
    ids = [e.data.get("id") for e in raw if isinstance(e.data, dict)]
    # A task file's name claims its folder even when the file did not parse.
    stems = [PurePosixPath(p).stem for p in files if p.startswith(f"{TASKS_DIR}/") and p.count("/") == 1]
    claimed = {task_id for task_id in ids + stems if isinstance(task_id, str)}
    folders = {path.split("/")[1] for path in files if path.startswith(f"{TASKS_DIR}/") and path.count("/") >= 2}
    message = "belongs to no task: a folder here holds the files of the task with its id"
    for folder in sorted(folders - claimed):
        if not folder.startswith("."):
            problems.append(Problem(f"{TASKS_DIR}/{folder}/", message))
