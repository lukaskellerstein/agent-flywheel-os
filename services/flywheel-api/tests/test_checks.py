"""Every check of an import, each failing with the file and the field it names."""

from __future__ import annotations

import json

import pytest
import yaml
from helpers import refusal

from flywheel_api.problems import ImportRefused
from flywheel_api.usecase import check

PRICING = "tasks/pricing.yaml"
EXPORT = "tasks/export-data.yaml"


def task(**data) -> bytes:
    base = {"input": {"question": "Is the Console free?", "product": "Console"}}
    return yaml.safe_dump({**base, **data}).encode()


def drop(files, prefix):
    for path in [p for p in files if p.startswith(prefix)]:
        del files[path]


def as_jsonl(files) -> None:
    """The sample's three tasks as tasks.jsonl, their files in <id>/ beside it."""
    lines = []
    for path in sorted(p for p in files if p.startswith("tasks/") and p.count("/") == 1):
        data = yaml.safe_load(files[path])
        lines.append(json.dumps({"id": data.get("id", path[6:-5]), **data}))
    files["export-data/screen.txt"] = files["tasks/export-data/screen.txt"]
    drop(files, "tasks/")
    files["tasks.jsonl"] = ("\n".join(lines) + "\n").encode()


def test_the_sample_passes(files):
    usecase = check(files)
    assert [t.id for t in usecase.tasks] == ["export-data", "pricing", "reset-password"]
    assert usecase.definition.task.label == "question"
    assert [j["name"] for j in usecase.judges] == ["must_mention", "style"]
    assert list(usecase.tasks[0].data) == ["id", "split", "tags", "input", "expected", "files"]


TASK_CASES = {
    "unknown key": (lambda f: f.update({PRICING: task(answer="yes")}), (PRICING, "answer")),
    "no input": (lambda f: f.update({PRICING: b"expected: {a: 1}\n"}), (PRICING, "input")),
    "input not a mapping": (lambda f: f.update({PRICING: task(input="hi")}), (PRICING, "input")),
    "expected not a mapping": (lambda f: f.update({PRICING: task(expected=["x"])}), (PRICING, "expected")),
    "empty split": (lambda f: f.update({PRICING: task(split="")}), (PRICING, "split")),
    "tags not strings": (lambda f: f.update({PRICING: task(tags="billing")}), (PRICING, "tags")),
    "bad id": (lambda f: f.update({PRICING: task(id="-pricing")}), (PRICING, "id")),
    "duplicate id": (lambda f: f.update({"tasks/quote.yaml": task(id="pricing")}), ("tasks/quote.yaml", "id")),
    "named file missing": (
        lambda f: f.update({EXPORT: f[EXPORT].replace(b"[screen.txt]", b"[screen.txt, gone.png]")}),
        (EXPORT, "files[1]"),
    ),
    "file outside its folder": (lambda f: f.update({PRICING: task(files=["../pricing.yaml"])}), (PRICING, "files[0]")),
    "file named like the converter's": (
        lambda f: f.update({PRICING: task(files=["input.yaml"]), "tasks/pricing/input.yaml": b"x"}),
        (PRICING, "files[0]"),
    ),
    "files not a list": (lambda f: f.update({PRICING: task(files="screen.txt")}), (PRICING, "files")),
    "not YAML": (lambda f: f.update({PRICING: b"input: [\n"}), (PRICING, None)),
    "not a mapping": (lambda f: f.update({PRICING: b"- input\n"}), (PRICING, None)),
    "empty file": (lambda f: f.update({PRICING: b""}), (PRICING, None)),
    "a folder of no task": (lambda f: f.update({"tasks/ghost/notes.txt": b"x"}), ("tasks/ghost/", None)),
    "a file that is no task": (lambda f: f.update({"tasks/notes.txt": b"x"}), ("tasks/notes.txt", None)),
    "tasks/ and tasks.jsonl": (lambda f: f.update({"tasks.jsonl": b"{}\n"}), ("tasks.jsonl", None)),
    "no tasks at all": (lambda f: drop(f, "tasks/"), ("tasks/", None)),
    "the prompt key missing": (
        lambda f: f.update({PRICING: task(input={"product": "Console"})}),
        (PRICING, "input.question"),
    ),
}


@pytest.mark.parametrize("change, expected", TASK_CASES.values(), ids=TASK_CASES.keys())
def test_a_task_check_names_file_and_field(files, change, expected):
    change(files)
    assert expected in refusal(files)


def test_jsonl_tasks_pass(files):
    as_jsonl(files)
    usecase = check(files)
    assert [t.id for t in usecase.tasks] == ["export-data", "pricing", "reset-password"]
    assert usecase.tasks[0].files_dir == "export-data"


JSONL_CASES = {
    "no id": ('{"input": {"question": "q"}}', ("tasks.jsonl", "id"), 4),
    "not JSON": ("{input: q}", ("tasks.jsonl", None), 4),
    "an id that names a use case folder": ('{"id": "hidden", "input": {"question": "q"}}', ("tasks.jsonl", "id"), 4),
}


@pytest.mark.parametrize("line, expected, number", JSONL_CASES.values(), ids=JSONL_CASES.keys())
def test_a_jsonl_check_names_the_line(files, line, expected, number):
    as_jsonl(files)
    files["tasks.jsonl"] += f"{line}\n".encode()
    with pytest.raises(ImportRefused) as refused:
        check(files)
    problem = refused.value.problems[0]
    assert (problem.file, problem.field, problem.line) == (*expected, number)


def test_an_empty_jsonl_has_no_tasks(files):
    as_jsonl(files)
    files["tasks.jsonl"] = b"\n"
    assert refusal(files) == [("tasks.jsonl", None)]


def usecase_yaml(**changes) -> bytes:
    base = {"title": "Product questions", "task": {"prompt": "question"}}
    return yaml.safe_dump({**base, **changes}).encode()


DEFINITION_CASES = {
    "missing": (lambda f: f.pop("usecase.yaml"), ("usecase.yaml", None)),
    "unknown key": (lambda f: f.update({"usecase.yaml": usecase_yaml(titel="x")}), ("usecase.yaml", "titel")),
    "no title": (lambda f: f.update({"usecase.yaml": b"task: {prompt: question}\n"}), ("usecase.yaml", "title")),
    "no prompt key": (
        lambda f: f.update({"usecase.yaml": usecase_yaml(task={"label": "q"})}),
        ("usecase.yaml", "task.prompt"),
    ),
    "unknown nested key": (
        lambda f: f.update({"usecase.yaml": usecase_yaml(brain={"max_skills": 2, "max_files": 3})}),
        ("usecase.yaml", "brain.max_files"),
    ),
    "wrong type": (
        lambda f: f.update({"usecase.yaml": usecase_yaml(brain={"max_skills": "two"})}),
        ("usecase.yaml", "brain.max_skills"),
    ),
    "a shown key not a string": (
        lambda f: f.update({"usecase.yaml": usecase_yaml(task={"prompt": "question", "show": [3]})}),
        ("usecase.yaml", "task.show[0]"),
    ),
    "not a mapping": (lambda f: f.update({"usecase.yaml": b"- title\n"}), ("usecase.yaml", None)),
}


@pytest.mark.parametrize("change, expected", DEFINITION_CASES.values(), ids=DEFINITION_CASES.keys())
def test_a_usecase_yaml_check_names_the_field(files, change, expected):
    change(files)
    assert expected in refusal(files)


EVAL_CASES = {
    "missing": (lambda f: f.pop("eval.yaml"), ("eval.yaml", None)),
    "not YAML": (lambda f: f.update({"eval.yaml": b"judges: [\n"}), ("eval.yaml", None)),
    "no judges": (lambda f: f.update({"eval.yaml": b"name: x\n"}), ("eval.yaml", "judges")),
    "judges not a list": (lambda f: f.update({"eval.yaml": b"judges: {a: 1}\n"}), ("eval.yaml", "judges")),
    "a judge without a name": (
        lambda f: f.update({"eval.yaml": b"judges:\n  - name: a\n  - description: b\n"}),
        ("eval.yaml", "judges[1].name"),
    ),
    "two judges, one name": (
        lambda f: f.update({"eval.yaml": b"judges:\n  - name: a\n  - name: a\n"}),
        ("eval.yaml", "judges[1].name"),
    ),
}


@pytest.mark.parametrize("change, expected", EVAL_CASES.values(), ids=EVAL_CASES.keys())
def test_an_eval_yaml_check_names_the_field(files, change, expected):
    change(files)
    assert expected in refusal(files)


def test_a_yaml_problem_names_its_line(files):
    files["eval.yaml"] = b"name: x\njudges:\n  - name: a\n   bad: indent\n"
    with pytest.raises(ImportRefused) as refused:
        check(files)
    assert refused.value.problems[0].line == 4


def test_the_registrys_own_file_name_is_refused(files):
    files["version.json"] = b"{}"
    assert refusal(files) == [("version.json", None)]


def test_every_problem_comes_in_one_refusal(files):
    files["usecase.yaml"] = usecase_yaml(titel="x")
    files["eval.yaml"] = b"name: x\n"
    files[PRICING] = task(answer="yes")
    files["tasks/notes.txt"] = b"x"
    assert refusal(files) == [
        ("eval.yaml", "judges"),
        ("tasks/notes.txt", None),
        (PRICING, "answer"),
        ("usecase.yaml", "titel"),
    ]
