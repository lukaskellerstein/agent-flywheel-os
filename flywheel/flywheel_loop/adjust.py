"""One Adjust step: the OpenCode adjuster agent changes the best brain from
its train failures and the history, and writes its hypothesis to change.md.

The workspace holds the adjuster's agent (adjuster.md) and its OpenCode
config, brain/ (the best brain), failures.md and history.md. The step keeps
only the brain files the adjuster created or changed, repairs a skill's
frontmatter, and drops a new skill beyond the use case's max_skills. A
session that changes no brain file gets one retry in the same workspace.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import FlywheelError
from . import brain as brains
from .brain import Brain

PROMPT = Path(__file__).with_name("adjuster.md")
PROVIDER = "gateway"
CHANGE_FILE = "change.md"
REPORT_FILES = ("failures.md", "history.md")
FIRST_SESSION = "session-1"
TEXT_LIMIT = 1000
# The gateway takes no key inside the cluster; OpenCode's provider wants one.
GATEWAY_KEY = "gateway-takes-no-key"


@dataclass
class Words:
    """What usecase.yaml says about the use case to its adjuster."""

    label: str
    role: str
    causes: list[str]
    hidden: str | None
    max_skills: int

    @classmethod
    def of(cls, definition: Mapping[str, Any]) -> Words:
        adjuster = definition.get("adjuster")
        if not adjuster:
            raise FlywheelError("usecase.yaml has no adjuster: block, so its brain cannot be trained")
        return cls(
            label=definition["task"].get("label") or "task",
            role=adjuster["role"],
            causes=list(adjuster.get("causes") or []),
            hidden=adjuster.get("hidden"),
            max_skills=(definition.get("brain") or {}).get("max_skills", 3),
        )


@dataclass
class Adjusted:
    updates: Brain  # the brain files changed or created; empty: no change
    hypothesis: str
    change: str
    metrics: dict[str, float] = field(default_factory=dict)


class Adjuster:
    def __init__(self, model: str, gateway_url: str, timeout_s: int, opencode: str = "opencode"):
        self.model = model
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout_s = timeout_s
        self.opencode = opencode

    def adjust(self, work: Path, best: Brain, failures: str, history: str, words: Words, step: int, base: int) -> Adjusted:
        """Adjust step *step* on brain v*base*; its logs go to work/logs."""
        ws, logs = work / "ws", work / "logs"
        self._workspace(ws, best, failures, history)
        logs.mkdir(parents=True)
        for name in REPORT_FILES:
            shutil.copy(ws / name, logs / name)
        task = task_text(words, step, base)
        updates, metrics, last = self._session(ws, task, logs, best, words)
        if not updates:
            first = logs / FIRST_SESSION
            first.mkdir()
            for path in [p for p in logs.iterdir() if p.name not in (*REPORT_FILES, FIRST_SESSION)]:
                shutil.move(path, first / path.name)
            updates, again, last = self._session(ws, task + RETRY, logs, best, words)
            metrics = {key: round(metrics.get(key, 0) + value, 6) for key, value in again.items()}
        metrics["adjuster/sessions"] = 1 if FIRST_SESSION not in os.listdir(logs) else 2
        if (ws / CHANGE_FILE).is_file():
            shutil.copy(ws / CHANGE_FILE, logs / CHANGE_FILE)
        hypothesis, change = read_change(ws / CHANGE_FILE, last)
        return Adjusted(updates, hypothesis, change, metrics)

    def _workspace(self, ws: Path, best: Brain, failures: str, history: str) -> None:
        agents = ws / ".opencode" / "agents"
        agents.mkdir(parents=True)
        shutil.copy(PROMPT, agents / "adjuster.md")
        (ws / "opencode.json").write_text(json.dumps(self._config(), indent=2))
        brains.write(best, ws / "brain").mkdir(parents=True, exist_ok=True)
        (ws / "failures.md").write_text(failures)
        (ws / "history.md").write_text(history)

    def _config(self) -> dict:
        model = {"name": self.model, "tool_call": True, "reasoning": True, "limit": {"context": 128000, "output": 16384}}
        return {
            "$schema": "https://opencode.ai/config.json",
            "default_agent": "adjuster",
            "provider": {
                PROVIDER: {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "The cluster's model gateway",
                    "options": {"baseURL": "{env:GATEWAY_URL}/v1", "apiKey": "{env:GATEWAY_KEY}"},
                    "models": {self.model: model},
                }
            },
        }

    def _session(self, ws: Path, task: str, logs: Path, best: Brain, words: Words) -> tuple[Brain, dict, str]:
        (logs / "task.md").write_text(task)
        self._run(ws, task, logs)
        metrics, last = transcript(logs / "events.jsonl", logs / "transcript.md")
        return take_adjusted(ws / "brain", best, words), metrics, last

    def _run(self, ws: Path, task: str, logs: Path) -> None:
        """OpenCode headless, isolated from any user config, on the gateway."""
        home = ws.parent / "opencode-home"
        env = {**os.environ, "GATEWAY_URL": self.gateway_url, "GATEWAY_KEY": GATEWAY_KEY}
        env["OPENCODE_DISABLE_CLAUDE_CODE"] = "1"
        for var, sub in (("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"), ("XDG_STATE_HOME", "state"), ("XDG_CACHE_HOME", "cache")):
            (home / sub).mkdir(parents=True, exist_ok=True)
            env[var] = str(home / sub)
        command = [
            *(self.opencode, "run", task, "--format", "json", "--dir", str(ws)),
            *("--model", f"{PROVIDER}/{self.model}", "--agent", "adjuster"),
            *("--pure", "--auto", "--print-logs", "--log-level", "WARN"),
        ]
        print(f"adjuster: opencode run --agent adjuster --model {PROVIDER}/{self.model} in {ws}", flush=True)
        with open(logs / "events.jsonl", "w") as out, open(logs / "opencode.stderr", "w") as err:
            try:
                result = subprocess.run(command, cwd=ws, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err, timeout=self.timeout_s)
            except subprocess.TimeoutExpired as exc:
                raise FlywheelError(f"the adjuster did not finish in {self.timeout_s} s") from exc
        if result.returncode != 0:
            tail = (logs / "opencode.stderr").read_text()[-800:]
            raise FlywheelError(f"opencode exited with {result.returncode}:\n{tail}")


RETRY = (
    "\nYour first session on this step ended without a change to any brain file, so it was lost. "
    "Do not describe the change in your answer: open the brain file with the edit or write tool "
    "and change it.\n"
)


def task_text(words: Words, step: int, base: int) -> str:
    """The adjuster's task: the step and what usecase.yaml says about the use case."""
    case = "" if words.label == "case" else f" A case is a {words.label} here."
    causes = f"Group the failures by cause: {', '.join(words.causes)}.\n\n" if words.causes else ""
    return (
        f"Adjust step {step}: improve {words.role}. `brain/` holds brain v{base}, the best brain so far.{case} "
        f"The brain is `brain/AGENTS.md` and up to {words.max_skills} skills.\n\n"
        + causes
        + (f"{words.hidden}\n\n" if words.hidden else "")
        + "Read `history.md` and `failures.md` in full, then follow your method. Use the edit or write "
        "tool to change at least one brain file: only what is in the files counts, so a step that "
        f"changes no brain file is lost. Then write `{CHANGE_FILE}`, and stop with one line that says "
        "what you changed.\n"
    )


def take_adjusted(folder: Path, before: Brain, words: Words) -> Brain:
    """The brain files the adjuster created or changed, checked and repaired.
    A deleted file stays as it was; a new skill beyond max_skills is dropped."""
    updates: Brain = {}
    skills = brains.skill_count(before)
    for key, text in brains.read(folder).items():
        if text == before.get(key):
            continue
        if not text.strip():
            raise FlywheelError(f"the adjuster left {key} empty")
        is_skill = brains.SKILL.fullmatch(key) is not None
        if is_skill and key not in before:
            if skills >= words.max_skills:
                print(f"adjuster: dropped the new skill {key}, the brain has {words.max_skills} skills already")
                continue
            skills += 1
        new = brains.repair_skill(key, text, words.label) if is_skill else text
        if new != before.get(key):
            updates[key] = new
    return updates


def transcript(events: Path, dest: Path) -> tuple[dict[str, float], str]:
    """A readable transcript of OpenCode's JSON events, its metrics, and its last message."""
    lines, texts = [], []
    steps = tools = tokens_in = tokens_out = 0
    cost = 0.0
    for event in _events(events):
        kind, part = event.get("type"), event.get("part") or {}
        if kind == "text" and (part.get("text") or "").strip():
            texts.append(part["text"])
            lines.append("ASSISTANT:\n" + part["text"].strip())
        elif kind == "tool_use":
            tools += 1
            lines.append(f"TOOL {part.get('tool')}: {json.dumps((part.get('state') or {}).get('input', {}))[:300]}")
        elif kind == "step_finish":
            steps += 1
            tokens = part.get("tokens") or {}
            tokens_in += (tokens.get("input") or 0) + ((tokens.get("cache") or {}).get("read") or 0)
            tokens_out += tokens.get("output") or 0
            cost += part.get("cost") or 0.0
        elif kind == "error":
            lines.append("ERROR: " + json.dumps(event)[:500])
    dest.write_text("\n\n".join(lines) + "\n")
    metrics = {
        "adjuster/steps": steps,
        "adjuster/tool_calls": tools,
        "adjuster/tokens_in": tokens_in,
        "adjuster/tokens_out": tokens_out,
        "adjuster/cost_usd": round(cost, 6),
    }
    return metrics, next((t for t in reversed(texts) if t.strip()), "")


def _events(path: Path) -> list[dict]:
    found = []
    for raw in path.read_text().splitlines():
        raw = raw.strip()
        if raw.startswith("{"):
            try:
                found.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    return found


def read_change(path: Path, last_message: str) -> tuple[str, str]:
    """The hypothesis and the change from change.md, else from the same lines
    in the last message (a small model writes them there)."""
    found = change_lines(path.read_text() if path.is_file() else "")
    for key, value in change_lines(last_message).items():
        found.setdefault(key, value)
    hypothesis = found.get("hypothesis", "not written")
    change = found.get("change") or last_message.strip() or "not written"
    return hypothesis[:TEXT_LIMIT], change[:TEXT_LIMIT]


def change_lines(text: str) -> dict[str, str]:
    """The first `Hypothesis:` and `Change:` of a text, markdown marks
    allowed; a value goes on over the list items or indented lines below it."""
    found: dict[str, list[str]] = {}
    key = None
    for line in text.splitlines():
        match = re.match(r"[\s*#-]*(hypothesis|change)\**\s*:\**\s*(.*)", line, re.I)
        if match:
            name = match.group(1).lower()
            key = None if name in found else name
            if key:
                found[key] = [match.group(2).strip()]
            continue
        more = re.match(r"\s*(?:[-*+]|\d+[.)])\s+(.+)|\s+(\S.*)", line) if key else None
        if more:
            found[key].append((more.group(1) or more.group(2)).strip())
        else:
            key = None
    return {k: " ".join(p for p in parts if p) for k, parts in found.items() if any(parts)}
