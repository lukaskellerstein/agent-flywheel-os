---
description: "Reference: Technology stack — the flywheel API (Python 3.12, FastAPI, boto3) is built; the rest planned: Python glue, kustomize + BuildConfigs on OpenShift 4.22 with Open Data Hub 3.6"
---

# Reference: Technology Stack

<!-- Read from manifests (package.json, pyproject.toml, go.mod, Chart.yaml),
     never guessed. Pin the versions that actually constrain choices; omit the
     ones that do not. Delete sections that do not apply. -->

The flywheel API is built (2026-10-16); its versions below are read from
`services/flywheel-api/pyproject.toml`. Every other line is still the plan
(the specs in `docs/my-specs/`), not a manifest. Section, phase and
decision numbers are spec 01's unless spec 02 is named. Pin each part's
real versions here when it lands, and drop the word "planned".

## Backend

- **The flywheel API** (`services/flywheel-api/`, spec 02 phase 3): Python
  3.12, FastAPI 0.142.2, uvicorn 0.54.0, pydantic 2.13.5, PyYAML 6.0.3,
  boto3 1.43.106, python-multipart 0.0.32; tests with pytest 9.1.1, moto
  5.2.3 and httpx2 2.13.1 (pydantic's, for Starlette's test client). uv
  with `uv.lock`; `exclude-newer` keeps every locked release at least two
  weeks old. The image is UBI 9 Python 3.12, pinned by digest. API only,
  no static app; `openshift-eval`'s `ui/server/` was its reference
- **Language** (planned): Python for the loop and the Adjust backends,
  ported from `openshift-eval` (spec 01 §4, §9; spec 02 phase 3)
- **Eval**: agent-eval-harness from the fork's `flywheel-integration` branch,
  pip-installed inside the runner image (§4); one Score backend, EvalHub with
  the contrib adapter (C11). EvalHub server 1.0.2, SDK `eval-hub-sdk` 1.0.6 (§3)
- **Training**: `gepa` 0.1.4 called directly, not through Training Hub
  (decision 8)
- **Data**: MLflow — ODH's `mlflowoperator` first, `openshift-eval`'s own
  MLflow 3.16.1 only if that does not fit (phase 1 step 5)
- **Model gateway**: LiteLLM, ported from `openshift-eval` `deploy/gateway/`;
  every model alias and price lives in its `config/` (phase 1 step 6)

## Infrastructure (planned)

- **Deploy**: kustomize in this repo; images built on the cluster with
  BuildConfigs (§4). Build on the cluster, never on the Mac: it is arm64, the
  node is x86_64 (phase 5 step 5)
- **Runtime**: OpenShift 4.22.16, single node, no GPU; Open Data Hub
  3.6.0-ea.2, operator-managed, with the dashboard, TrustyAI (EvalHub) and
  MLflow `Managed` — installed 2026-10-13 (`deploy/platform/`, §3,
  decision 5, phase 1)

## Not in this repo

- **The UI** is the `agent-flywheel` module of the `odh-dashboard` fork,
  `packages/agent-flywheel`: a PatternFly frontend and a Go BFF in one image,
  shaped like `packages/eval-hub` (phase 5). That repo's toolchain is Node 22,
  pnpm 11.22.0, Go 1.26 (§3). Its BFF forwards to this repo's flywheel API
  (decision 6).

## Scripting & Automation

- Default: Python for scripts, consistent with the rest of the stack
- Shell scripts only for trivial one-liners

## Conventions this machine imposes

- **One formatter per filetype.** Biome owns the JS/TS family; prettier and
  eslint are not installed. Python formats with the ruff CLI chain.
- Tools run only where the repo carries their config file — see
  `rules/09-code-quality.md`.
