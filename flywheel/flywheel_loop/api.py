"""The flywheel API (services/flywheel-api/), as the loop uses it: a use case
version with its tasks, and evaluations that score one brain on one split."""

from __future__ import annotations

import time
import urllib.parse
from collections.abc import Callable
from typing import Any

from . import FlywheelError
from .http import Http

# EvalHub's final states, as the API passes them on.
FINAL_STATES = frozenset({"completed", "failed", "cancelled", "partially_failed"})


def _quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


class FlywheelAPI:
    def __init__(self, http: Http, sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic):
        self.http = http
        self.sleep = sleep
        self.clock = clock

    def version(self, usecase: str, number: int | None = None) -> dict:
        """The version's record, definition, judges and tasks; the current one when *number* is None."""
        if number is None:
            number = self.http.json("GET", f"/api/usecases/{_quote(usecase)}")["current"]
        return self.http.json("GET", f"/api/usecases/{_quote(usecase)}/versions/{number}")

    def start(self, usecase: str, **request: Any) -> dict:
        """One evaluation: version, split, agent, model, brain and training, each left out when None."""
        body = {key: value for key, value in request.items() if value is not None}
        return self.http.json("POST", f"/api/usecases/{_quote(usecase)}/evaluations", body=body)

    def evaluation(self, usecase: str, job_id: str) -> dict:
        return self.http.json("GET", f"/api/usecases/{_quote(usecase)}/evaluations/{_quote(job_id)}")

    def task(self, usecase: str, job_id: str, task_id: str) -> dict:
        path = f"/api/usecases/{_quote(usecase)}/evaluations/{_quote(job_id)}/tasks/{_quote(task_id)}"
        return self.http.json("GET", path)

    def wait(self, usecase: str, job_id: str, poll_s: float, timeout_s: float) -> dict:
        """The evaluation once it completed with every task's verdicts; a
        failed or stopped one, or one past *timeout_s*, ends the training run."""
        deadline = self.clock() + timeout_s
        while True:
            row = self.evaluation(usecase, job_id)
            state = row.get("state")
            if state in FINAL_STATES and state != "completed":
                raise FlywheelError(f"evaluation {job_id} ended {state}: {row.get('error') or row.get('message')}")
            if state == "completed" and row.get("tasks") is not None:
                return row
            if self.clock() > deadline:
                raise FlywheelError(f"evaluation {job_id} did not finish in {timeout_s:.0f} s (state {state})")
            self.sleep(poll_s)
