"""One use case folder (spec 02 section 4.2), read and checked whole.

    usecase.yaml   ours: what no upstream project has a field for
    eval.yaml      the harness's: the judges, the gate, the workspace files
    tasks/         one YAML file per task, or tasks.jsonl instead
    resources/     what the agent may read
    hidden/        what only the judges see

`usecase.yaml` holds the words of the UI, the brain's limits and the
adjuster's slots: our loop's and our UI's, nothing the harness can hold
(decision 1). Its keys follow `openshift-eval`'s `task.yaml` on its branch
`generalization`, in this repo's words (decision 12: its "case" is our task).
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic_core import ErrorDetails

from .files import Files
from .problems import ImportRefused, Problem, read_yaml
from .taskformat import Task, read_tasks

USECASE_FILE = "usecase.yaml"
EVAL_FILE = "eval.yaml"
# The registry writes this beside a version's files (registry.py).
VERSION_FILE = "version.json"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TaskWords(_Strict):
    """How the UI and the loop name and show one task."""

    label: str = "task"  # the UI's word for one task, e.g. "ticket"
    prompt: str  # the input key that is the agent's prompt
    show: list[str] = []  # the input keys the UI shows beside it


class Brain(_Strict):
    max_skills: int = Field(ge=0)  # AGENTS.md and up to this many skills


class Adjuster(_Strict):
    """The slots of the adjuster's prompt."""

    role: str  # "You improve <role>."
    causes: list[str] = []  # what it sorts the failures into
    hidden: str | None = None  # what its workspace does not hold


class Definition(_Strict):
    """usecase.yaml."""

    title: str = Field(min_length=1)
    description: str = ""
    task: TaskWords
    brain: Brain | None = None
    adjuster: Adjuster | None = None


@dataclass(frozen=True)
class UseCase:
    definition: Definition
    eval: dict
    tasks: list[Task]

    @property
    def judges(self) -> list[dict]:
        return self.eval["judges"]


def check(files: Files) -> UseCase:
    """The use case, or ImportRefused with every problem of every file."""
    problems: list[Problem] = []
    if VERSION_FILE in files:
        problems.append(Problem(VERSION_FILE, "a name the registry writes beside a version's files"))
    definition, eval_config, tasks = _read(files, problems)
    if definition is not None:
        problems += _prompt_problems(definition, tasks)
    # The JSON Schema of `input` and `expected` (C26, the harness's
    # validate_eval.py) joins here as one more check of every task.
    if problems or definition is None or eval_config is None:
        raise ImportRefused(problems)
    return UseCase(definition, eval_config, tasks)


def load(files: Files) -> UseCase:
    """A stored version, which passed `check` when it was imported."""
    problems: list[Problem] = []
    definition, eval_config, tasks = _read(files, problems)
    if problems or definition is None or eval_config is None:
        raise RuntimeError(f"a stored version does not read: {[p.as_dict() for p in problems]}")
    return UseCase(definition, eval_config, tasks)


def _read(files: Files, problems: list[Problem]) -> tuple[Definition | None, dict | None, list[Task]]:
    return _read_definition(files, problems), _read_eval(files, problems), read_tasks(files, problems)


def _read_definition(files: Files, problems: list[Problem]) -> Definition | None:
    data = _read_mapping(files, USECASE_FILE, problems)
    if data is None:
        return None
    try:
        return Definition.model_validate(data)
    except ValidationError as exc:
        problems += [_validation_problem(error) for error in exc.errors()]
        return None


def _validation_problem(error: ErrorDetails) -> Problem:
    field = "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error["loc"]).lstrip(".") or None
    message = {"extra_forbidden": "unknown key", "missing": "required"}.get(error["type"], error["msg"])
    return Problem(USECASE_FILE, message, field)


def _read_eval(files: Files, problems: list[Problem]) -> dict | None:
    """eval.yaml is the harness's to validate; the import checks that it is a
    mapping with a list of named judges, which the API shows and the scores need."""
    data = _read_mapping(files, EVAL_FILE, problems)
    if data is None:
        return None
    judges = data.get("judges")
    if not isinstance(judges, list) or not judges:
        problems.append(Problem(EVAL_FILE, "required: a non-empty list of judges", "judges"))
        return None
    before = len(problems)
    names: set[str] = set()
    for index, judge in enumerate(judges):
        name = judge.get("name") if isinstance(judge, dict) else None
        if not isinstance(name, str) or not name:
            problems.append(Problem(EVAL_FILE, "every judge is a mapping with a name", f"judges[{index}].name"))
        elif name in names:
            problems.append(Problem(EVAL_FILE, f"duplicate judge name {name!r}", f"judges[{index}].name"))
        else:
            names.add(name)
    return data if len(problems) == before else None


def _read_mapping(files: Files, path: str, problems: list[Problem]) -> dict | None:
    if path not in files:
        problems.append(Problem(path, "missing: every use case has one"))
        return None
    data = read_yaml(files, path, problems)
    if data is not None and not isinstance(data, dict):
        problems.append(Problem(path, "must be a mapping"))
        return None
    return data


def _prompt_problems(definition: Definition, tasks: list[Task]) -> list[Problem]:
    key = definition.task.prompt
    return [
        Problem(task.file, f"missing: {USECASE_FILE} names it the prompt (task.prompt)", f"input.{key}", task.line)
        for task in tasks
        if key not in task.data["input"]
    ]
