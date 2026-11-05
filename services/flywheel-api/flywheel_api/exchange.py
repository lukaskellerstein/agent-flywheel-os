"""One task of one run as the harness left it in the run folder, which C11
puts in the job's MLflow run under `run/`: `cases/<task>/` holds the agent's
outputs (eval.yaml's `outputs` paths), `run_result.json` (turns, tokens,
cost, duration) and `events.json`, the harness's trace of the agent in one
shape for every runner: system, assistant (its text and tool calls),
tool_result and result events.

A step here is a message or a tool call with a short form of its input; a
tool's output stays in MLflow, behind the page's link.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

# A task id as a folder name of the run: never a path of its own.
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
MAX_TEXT = 64 * 1024  # bytes of one answer file shown; the rest stays in MLflow
MAX_FILES = 20
MAX_INPUT = 400  # characters of one tool input
# The harness copies the runner's own logs into the outputs folder too.
RUNNER_LOGS = frozenset({"stdout.log", "stderr.log"})
# The keys of a tool input that say what it did, in the order shown:
# Bash's command, Read's and Write's file, Grep's pattern and path, a fetch's URL.
INPUT_KEYS = ("command", "file_path", "pattern", "path", "url", "query")
# Codex runs every command as `/usr/bin/bash -lc "<command>"`.
SHELL_WRAPPER = re.compile(r"^(?:/usr)?(?:/bin/)?(?:ba)?sh -lc (['\"])(?P<command>.*)\1$", re.DOTALL)
TOKEN_KEYS = ("input", "output", "cache_read", "cache_create")
RUN_KEYS = ("exit_code", "duration_s", "num_turns", "model", "cost_usd", "cost_source", "error_class")


def run_of(run_result: Mapping[str, Any]) -> dict:
    """What the task's run cost: run_result.json without its message ids."""
    tokens = run_result.get("token_usage") or {}
    return {**{key: run_result.get(key) for key in RUN_KEYS}, "tokens": {key: tokens.get(key) for key in TOKEN_KEYS}}


def steps_of(events: list, task_id: str) -> list[dict]:
    """The agent's messages and tool calls in order; a call whose result was an error says so."""
    steps: list[dict] = []
    calls: dict[Any, dict] = {}
    for event in events:
        if not isinstance(event, Mapping):
            continue
        if event.get("type") == "assistant":
            if text := str(event.get("text") or "").strip():
                steps.append({"kind": "message", "text": text})
            for tool in event.get("tools") or []:
                step = {"kind": "tool", "tool": tool.get("name"), "input": _input(tool.get("input"), task_id), "error": False}
                steps.append(step)
                calls[tool.get("id")] = step
        elif event.get("type") == "tool_result" and event.get("is_error") and event.get("tool_use_id") in calls:
            calls[event["tool_use_id"]]["error"] = True
    return steps


def answer_file(path: str, data: bytes) -> dict:
    """One output file: its text up to MAX_TEXT, or no text when it is not UTF-8."""
    shown = data[:MAX_TEXT]
    try:
        text = shown.decode("utf-8")
    except UnicodeDecodeError:
        text = None
    return {"path": path, "size": len(data), "text": text, "truncated": text is not None and len(data) > MAX_TEXT}


def output_paths(config: Mapping[str, Any]) -> list[str]:
    """eval.yaml's outputs paths: where the agent writes what the judges read."""
    paths = []
    for output in config.get("outputs") or []:
        path = output.get("path") if isinstance(output, Mapping) else None
        if isinstance(path, str) and path.strip("/") and ".." not in path.split("/"):
            paths.append(path.strip("/"))
    return paths


def _input(value: Any, task_id: str) -> str:
    if isinstance(value, Mapping):
        parts = [str(value[key]) for key in INPUT_KEYS if isinstance(value.get(key), str)]
        text = " ".join(parts) if parts else json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    text = _relative(text, task_id)
    if match := SHELL_WRAPPER.match(text):
        text = match.group("command")
    return text if len(text) <= MAX_INPUT else text[:MAX_INPUT] + "…"


def _relative(text: str, task_id: str) -> str:
    """Paths as the agent's workspace has them: it ran in cases/<task>/ of a
    temporary folder in the job's pod, which means nothing on the page. A
    path inside it loses that prefix; the folder itself becomes `.`."""
    workspace = r"/\S*?/cases/" + re.escape(task_id)
    text = re.sub(workspace + "/", "", text)
    return re.sub(workspace + r"(?![\w.-])", ".", text)
