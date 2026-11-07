---
description: "Reference: Technology stack — Python 3.12 (FastAPI API, the training loop), kustomize + BuildConfigs on OpenShift 4.22 with Open Data Hub 3.6"
---

# Reference: Technology Stack

<!-- Read from manifests (package.json, pyproject.toml, go.mod, Chart.yaml),
     never guessed. Pin the versions that actually constrain choices; omit the
     ones that do not. Delete sections that do not apply.
     Only what is in the repo: no plan, phase, status or date. -->

The versions below are read from each project's `pyproject.toml`.

## Backend

- **The flywheel API** (`services/flywheel-api/`): Python
  3.12, FastAPI 0.142.2, uvicorn 0.54.0, pydantic 2.13.5, PyYAML 6.0.3,
  boto3 1.43.106, python-multipart 0.0.32; tests with pytest 9.1.1, moto
  5.2.3 and httpx2 2.13.1 (pydantic's, for Starlette's test client). uv
  with `uv.lock`; `exclude-newer` keeps every locked release at least two
  weeks old. The image is UBI 9 Python 3.12, pinned by digest. API only,
  no static app
- **The training loop** (`flywheel/`): Python 3.12, PyYAML 6.0.3 and the
  standard library (HTTP with `urllib`); tests with pytest 9.1.1. uv with
  `uv.lock` and the API's `exclude-newer`. The adjuster is OpenCode
  1.18.30 on the gateway. Its image (`images/runner/`) is our harness base
  image plus OpenCode; in it, the base image's unpinned PyYAML is the one
  that runs
- **Eval**: agent-eval-harness from the fork's `flywheel-integration`
  branch, in our harness base image; one Score backend, EvalHub with the
  contrib adapter. EvalHub server 1.0.2, SDK `eval-hub-sdk` 1.0.6
- **Data**: MLflow — ODH's `mlflowoperator`
- **Model gateway**: LiteLLM in `deploy/gateway/`; every model alias and
  price lives in its `config/`

## Infrastructure

- **Deploy**: kustomize in this repo; images built on the cluster with
  BuildConfigs. Build on the cluster, never on the Mac: it is arm64, the
  node is x86_64
- **Runtime**: OpenShift 4.22.16, single node, no GPU; Open Data Hub
  3.6.0-ea.2, operator-managed, with the dashboard, TrustyAI (EvalHub) and
  MLflow `Managed` (`deploy/platform/`)

## Not in this repo

- **The UI** is the `agent-flywheel` module of the `odh-dashboard` fork,
  `packages/agent-flywheel`: a PatternFly frontend and a Go BFF in one image,
  shaped like `packages/eval-hub`. That repo's toolchain is Node 22,
  pnpm 11.22.0, Go 1.26. Its BFF forwards to this repo's flywheel API.

## Scripting & Automation

- Default: Python for scripts, consistent with the rest of the stack
- Shell scripts only for trivial one-liners

## Conventions this machine imposes

- **One formatter per filetype.** Biome owns the JS/TS family; prettier and
  eslint are not installed. Python formats with the ruff CLI chain.
- Tools run only where the repo carries their config file — see
  `rules/09-code-quality.md`.
