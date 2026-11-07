"""The agents the flywheel may run (the module's AI hub › Agents), one JSON
file each in the registry's store, `agents/<name>.json`.

An agent is a harness runner with its own wiring to the gateway (`runner`,
which an evaluation lays over the version's eval.yaml runner block), where
its brain lives (`brain`), and the gateway models it may use (`models`).
Nothing here is a secret: the gateway takes no key inside the cluster, so a
variable that names a key holds the placeholder, and any other value is
refused. An agent is added, never changed or deleted, so a run's agent stays
readable.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .gateway import Gateway
from .problems import Conflict, Invalid, NotFound
from .registry import NAME, check_name
from .store import Store

ROOT = "agents/"
# The harness runners an evaluation can name (agent-eval-harness RUNNERS);
# the pod's image carries the Claude Code and Codex CLIs, OpenCode comes with
# the runner image of spec 02 phase 3.
RUNNERS = ("claude-code", "codex", "opencode")
PLACEHOLDER = "gateway-takes-no-key"
SECRET_NAME = re.compile(r"KEY|TOKEN|SECRET|PASSWORD", re.IGNORECASE)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EnvVar(_Strict):
    """A variable the agent reads, for its page; the values are runner.env's."""

    name: str = Field(min_length=1)
    required: bool = False
    description: str = ""


class Runner(_Strict):
    """The harness's runner block for this agent (agent-eval-harness runner.md)."""

    type: Literal[RUNNERS]  # type: ignore[valid-type]
    permission_mode: str | None = None
    settings: dict = {}
    env: dict[str, str] = {}

    @field_validator("env")
    @classmethod
    def no_secret(cls, env: dict[str, str]) -> dict[str, str]:
        for name, value in env.items():
            if SECRET_NAME.search(name) and value != PLACEHOLDER:
                raise ValueError(f"{name} names a key: the gateway takes none, so its value is {PLACEHOLDER!r}")
        return env


class Brain(_Strict):
    instructions_file: str = Field(min_length=1)  # e.g. AGENTS.md, CLAUDE.md
    skills_folder: str | None = None  # e.g. .agents/skills/, .claude/skills/
    trainable: bool = True  # a training run may change it


class Agent(_Strict):
    name: str
    title: str = Field(min_length=1)
    description: str = ""
    framework: str = ""
    version: str = ""
    image: str = ""
    repository: str = ""
    environment: list[EnvVar] = []
    runner: Runner
    brain: Brain
    models: list[str] = Field(min_length=1)
    default_model: str

    @field_validator("name")
    @classmethod
    def dns_label(cls, name: str) -> str:
        if not NAME.fullmatch(name):
            raise ValueError(f"an agent name is a DNS label ({NAME.pattern})")
        return name

    @model_validator(mode="after")
    def default_is_listed(self) -> Agent:
        if len(set(self.models)) != len(self.models):
            raise ValueError("models lists a model twice")
        if self.default_model not in self.models:
            raise ValueError(f"default_model {self.default_model!r} is not in models")
        return self


class Agents:
    def __init__(self, store: Store, gateway: Gateway):
        self.store = store
        self.gateway = gateway
        self._lock = threading.Lock()

    def list(self) -> list[dict]:
        records = (self._read(key) for key in self.store.keys(ROOT) if key.endswith(".json"))
        return sorted(records, key=lambda agent: agent["title"].lower())

    def get(self, name: str) -> dict:
        data = self.store.get(_key(name)) if NAME.fullmatch(name) else None
        if data is None:
            raise NotFound(f"no agent {name!r} in AI hub › Agents")
        return json.loads(data)

    def add(self, body: dict) -> dict:
        """Check the agent, its models against the gateway's routes, then store it."""
        try:
            agent = Agent.model_validate(body)
        except ValidationError as exc:
            raise Invalid(_problems(exc)) from exc
        routed = set(self.gateway.names())
        unknown = [model for model in agent.models if model not in routed]
        if unknown:
            raise Invalid(f"the gateway routes no {', '.join(unknown)}; its models: {', '.join(sorted(routed))}")
        check_name(agent.name)
        record = {**agent.model_dump(), "created": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")}
        with self._lock:
            if self.store.get(_key(agent.name)) is not None:
                raise Conflict(f"agent {agent.name!r} exists; an agent is never changed")
            self.store.put(_key(agent.name), json.dumps(record, indent=2, ensure_ascii=False).encode() + b"\n")
        return record

    def _read(self, key: str) -> dict:
        data = self.store.get(key)
        if data is None:
            raise RuntimeError(f"{key} was listed but cannot be read")
        return json.loads(data)


def runner_block(agent: dict) -> dict:
    """The agent's runner block as the harness reads it, without empty fields."""
    return {key: value for key, value in agent["runner"].items() if value not in (None, {}, [])}


def _key(name: str) -> str:
    return f"{ROOT}{name}.json"


def _problems(exc: ValidationError) -> str:
    return "; ".join(f"{'.'.join(str(part) for part in error['loc']) or 'body'}: {error['msg']}" for error in exc.errors())
