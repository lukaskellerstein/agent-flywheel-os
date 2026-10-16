"""What an import refuses, named by file and field, and the YAML reader that
names the line.

Every check appends to one list of problems instead of raising at the first,
so a refused import names everything wrong with it at once.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import yaml


@dataclass(frozen=True)
class Problem:
    file: str
    message: str
    field: str | None = None
    line: int | None = None

    def as_dict(self) -> dict:
        return {"file": self.file, "field": self.field, "line": self.line, "message": self.message}


class ImportRefused(Exception):
    """The use case has problems; nothing of it was written."""

    def __init__(self, problems: list[Problem]):
        self.problems = sorted(problems, key=lambda p: (p.file, p.line or 0, p.field or "", p.message))
        super().__init__(f"the import is refused: {len(problems)} problem(s)")


class BadRequest(ValueError):
    """A request the API cannot read: no archive, a refused URL, a failed clone."""

    status = 400


class TooLarge(BadRequest):
    status = 413


class NotFound(LookupError):
    pass


def read_yaml(files: Mapping[str, bytes], path: str, problems: list[Problem]) -> Any | None:
    """The parsed document at *path*, or None with a problem appended."""
    try:
        data = yaml.safe_load(files[path].decode("utf-8"))
    except UnicodeDecodeError:
        problems.append(Problem(path, "not UTF-8 text"))
        return None
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        line = mark.line + 1 if mark else None
        problems.append(Problem(path, f"not valid YAML: {getattr(exc, 'problem', None) or exc}", line=line))
        return None
    if data is None:
        problems.append(Problem(path, "empty"))
    return data
