"""A brain: AGENTS.md and up to the use case's max_skills skills, as files.

C11's adapter lays a brain's folder over the eval folder and links it into
every task's workspace, so an agent finds AGENTS.md beside its prompt and
the skills under .agents/skills/. Brain v0 is empty: the agent bare.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

AGENTS = "AGENTS.md"
SKILL = re.compile(r"\.agents/skills/([a-z0-9][a-z0-9-]*)/SKILL\.md")

Brain = dict[str, str]  # path in the brain -> text


def is_brain_file(key: str) -> bool:
    return key == AGENTS or SKILL.fullmatch(key) is not None


def read(folder: Path) -> Brain:
    """The brain files under *folder*; any other file is not part of a brain."""
    found = {}
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        key = path.relative_to(folder).as_posix()
        if is_brain_file(key):
            found[key] = path.read_text()
    return found


def write(brain: Brain, folder: Path) -> Path:
    for key, text in brain.items():
        target = folder / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return folder


def skill_count(brain: Brain) -> int:
    return sum(1 for key in brain if SKILL.fullmatch(key))


def repair_skill(key: str, text: str, label: str) -> str:
    """An agent loads a skill by its frontmatter: `name` must be the folder
    name and `description` says when to use it. Fix the name and fill in a
    missing description; keep every other field."""
    name = SKILL.fullmatch(key).group(1)
    block, body = _split_frontmatter(text)
    fields = _fields(block)
    if fields.get("name") == name and str(fields.get("description") or "").strip():
        return text
    description = str(fields.pop("description", "") or "").strip() or (
        f"Use for {label}s that need the {name.replace('-', ' ')} procedure."
    )
    fields.pop("name", None)
    ordered = {"name": name, "description": description, **fields}
    head = yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True, width=1000)
    return f"---\n{head}---\n\n{body.lstrip()}"


def _split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"---\n.*?\n---(?:\n|$)", text, re.S)
    return (match.group(0), text[match.end() :]) if match else ("", text)


def _fields(block: str) -> dict:
    inner = re.match(r"---\n(.*?)\n?---", block, re.S)
    try:
        fields = yaml.safe_load(inner.group(1)) if inner else None
    except yaml.YAMLError:
        fields = None
    return fields if isinstance(fields, dict) else {}
