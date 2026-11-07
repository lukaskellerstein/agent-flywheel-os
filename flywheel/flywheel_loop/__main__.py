"""`python -m flywheel_loop`: one training run, configured by env.

Required: USECASE and TRAINING_ID. Optional: USECASE_VERSION (the current
one), ITERATIONS (3), PATIENCE (2), AGENT and MODEL (eval.yaml's),
ADJUSTER_MODEL (enmaas-glm-5-3, free), ADJUSTER_TIMEOUT_S (900),
FLYWHEEL_API_URL, MLFLOW_URL, FLYWHEEL_NAMESPACE (MLflow's workspace),
FLYWHEEL_CA_FILE, TOKEN_FILE (the pod's ServiceAccount token),
GATEWAY_URL, OPENCODE_BIN, POLL_S, EVALUATION_TIMEOUT_S.
"""

from __future__ import annotations

import os
import signal
import sys
from collections.abc import Mapping
from pathlib import Path

from . import FlywheelError
from .adjust import Adjuster
from .api import FlywheelAPI
from .controller import Plan, Training
from .http import Http, HttpError
from .mlflow import MLflow

SA_TOKEN = "/var/run/secrets/kubernetes.io/serviceaccount/token"


def _int(env: Mapping[str, str], key: str, default: int) -> int:
    value = env.get(key) or str(default)
    if not value.isdigit():
        raise FlywheelError(f"{key} must be a whole number, got {value!r}")
    return int(value)


def plan_from(env: Mapping[str, str]) -> Plan:
    missing = [key for key in ("USECASE", "TRAINING_ID") if not env.get(key)]
    if missing:
        raise FlywheelError(f"set {', '.join(missing)}")
    version = env.get("USECASE_VERSION")
    return Plan(
        usecase=env["USECASE"],
        training=env["TRAINING_ID"],
        version=_int(env, "USECASE_VERSION", 0) if version else None,
        iterations=_int(env, "ITERATIONS", 3),
        patience=_int(env, "PATIENCE", 2),
        agent=env.get("AGENT") or None,
        model=env.get("MODEL") or None,
        poll_s=_int(env, "POLL_S", 15),
        evaluation_timeout_s=_int(env, "EVALUATION_TIMEOUT_S", 5400),
    )


def training_from(env: Mapping[str, str]) -> Training:
    namespace = env.get("FLYWHEEL_NAMESPACE", "agent-flywheel")
    token = Path(env.get("TOKEN_FILE", SA_TOKEN))
    ca = env.get("FLYWHEEL_CA_FILE") or None
    api_url = env.get("FLYWHEEL_API_URL", f"http://flywheel-api.{namespace}.svc:8080")
    mlflow_url = env.get("MLFLOW_URL", "https://mlflow.opendatahub.svc:8443/mlflow")
    api = FlywheelAPI(Http("flywheel API", api_url, token))
    mlflow = MLflow(Http("MLflow", mlflow_url, token, ca, {"X-MLflow-Workspace": namespace}))
    adjuster = Adjuster(
        model=env.get("ADJUSTER_MODEL", "enmaas-glm-5-3"),
        gateway_url=env.get("GATEWAY_URL", f"http://gateway.{namespace}.svc:4000"),
        timeout_s=_int(env, "ADJUSTER_TIMEOUT_S", 900),
        opencode=env.get("OPENCODE_BIN", "opencode"),
    )
    return Training(plan_from(env), api, mlflow, adjuster)


def _stop(signum: int, _frame) -> None:
    raise SystemExit(128 + signum)  # a deleted Job's pod: end the MLflow run as failed


def main() -> int:
    signal.signal(signal.SIGTERM, _stop)
    try:
        training_from(os.environ).run()
    except (FlywheelError, HttpError) as exc:
        print(f"training failed: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
