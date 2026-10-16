"""The registry of use cases (spec 02 section 4.3), in one store:

    usecases/<name>/usecase.json            title, source, current version, versions
    usecases/<name>/versions/<n>/version.json
                                            number, content hash, source, time,
                                            tasks per split, the diff to n-1
    usecases/<name>/versions/<n>/...        the version's files, as imported

A version is written file by file, then its version.json, then usecase.json:
a version exists once its version.json does, and is current once usecase.json
names it. Nothing that was a version is overwritten or deleted. Writes to one
use case are serialised in this process, so the API runs as one replica.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass
from datetime import UTC, datetime

from .files import Files
from .problems import BadRequest, NotFound
from .store import Store
from .usecase import VERSION_FILE, UseCase, check, load
from .versions import content_hash, diff, tasks_per_split

log = logging.getLogger(__name__)

ROOT = "usecases/"
ENTRY_FILE = "usecase.json"
# A DNS label: the name also names EvalHub collections and MLflow tags.
NAME = re.compile(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?")


@dataclass(frozen=True)
class ImportResult:
    status: str  # "created" or "unchanged"
    version: dict  # the version.json of the new version, or of the current one


class Registry:
    def __init__(self, store: Store):
        self.store = store
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def list(self) -> list[dict]:
        entries = (self._entry(name) for name in self.store.folders(ROOT))
        return [entry for entry in entries if entry is not None]

    def get(self, name: str) -> dict:
        entry = self._entry(name) if NAME.fullmatch(name) else None
        if entry is None:
            raise NotFound(f"no use case {name!r}")
        return entry

    def version(self, name: str, number: int) -> dict:
        """version.json with the version's definition, tasks, judges and file list."""
        record = self._record(name, number)
        files = self._files(name, number)
        usecase = load(files)
        return {
            **record,
            "usecase": usecase.definition.model_dump(),
            "judges": usecase.judges,
            "tasks": [task.data for task in usecase.tasks],
            "files": sorted(files),
        }

    def import_files(self, name: str, files: Files, source: dict) -> ImportResult:
        """Check the whole use case, then write it as the next version unless its hash is the current one's."""
        check_name(name)
        usecase = check(files)
        digest = content_hash(files)
        with self._lock(name):
            entry = self._entry(name)
            if entry is not None:
                current = self._record(name, entry["current"])
                if current["hash"] == digest:
                    return ImportResult("unchanged", current)
            record = self._new_record(name, entry, usecase, files, digest, source)
            self._write(name, files, record, usecase, entry)
        log.info("use case %s: version %d, %s", name, record["number"], digest)
        return ImportResult("created", record)

    def _new_record(
        self, name: str, entry: dict | None, usecase: UseCase, files: Files, digest: str, source: dict
    ) -> dict:
        previous = None
        if entry is not None:
            previous_files = self._files(name, entry["current"])
            previous = (load(previous_files), previous_files)
        number = entry["current"] + 1 if entry else 1
        return {
            "number": number,
            "hash": digest,
            "source": source,
            "created": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "task_count": len(usecase.tasks),
            "tasks_per_split": tasks_per_split(usecase.tasks),
            "diff": diff(previous, (usecase, files), entry["current"] if entry else None),
        }

    def _write(self, name: str, files: Files, record: dict, usecase: UseCase, entry: dict | None) -> None:
        prefix = self._version_prefix(name, record["number"])
        self._clear_unfinished(prefix)
        for path in sorted(files):
            self.store.put(prefix + path, files[path])
        self.store.put(prefix + VERSION_FILE, _json(record))
        self.store.put(f"{ROOT}{name}/{ENTRY_FILE}", _json(_next_entry(name, entry, record, usecase)))

    def _clear_unfinished(self, prefix: str) -> None:
        """Files under a version's folder without its version.json are what an
        interrupted import left; they were never a version, so they go."""
        keys = self.store.keys(prefix)
        if prefix + VERSION_FILE in keys:
            raise RuntimeError(f"{prefix} is a version already, but {ENTRY_FILE} does not name it")
        for key in keys:
            log.warning("removing %s, left by an unfinished import", key)
            self.store.delete(key)

    def _entry(self, name: str) -> dict | None:
        data = self.store.get(f"{ROOT}{name}/{ENTRY_FILE}")
        return json.loads(data) if data is not None else None

    def _record(self, name: str, number: int) -> dict:
        data = self.store.get(self._version_prefix(name, number) + VERSION_FILE) if NAME.fullmatch(name) else None
        if data is None:
            raise NotFound(f"no version {number} of use case {name!r}")
        return json.loads(data)

    def _files(self, name: str, number: int) -> Files:
        prefix = self._version_prefix(name, number)
        files: Files = {}
        for key in self.store.keys(prefix):
            if key == prefix + VERSION_FILE:
                continue
            data = self.store.get(key)
            if data is None:
                raise RuntimeError(f"{key} was listed but cannot be read")
            files[key[len(prefix) :]] = data
        return files

    def _version_prefix(self, name: str, number: int) -> str:
        return f"{ROOT}{name}/versions/{number}/"

    def _lock(self, name: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(name, threading.Lock())


def check_name(name: str) -> None:
    if not NAME.fullmatch(name):
        raise BadRequest(f"a use case name is a DNS label ({NAME.pattern}), not {name!r}")


def _next_entry(name: str, entry: dict | None, record: dict, usecase: UseCase) -> dict:
    summary = {key: record[key] for key in ("number", "hash", "created", "task_count")}
    return {
        "name": name,
        "title": usecase.definition.title,
        "description": usecase.definition.description,
        "source": record["source"],
        "current": record["number"],
        "versions": [*(entry["versions"] if entry else []), summary],
    }


def _json(value: dict) -> bytes:
    return json.dumps(value, indent=2, ensure_ascii=False).encode() + b"\n"
