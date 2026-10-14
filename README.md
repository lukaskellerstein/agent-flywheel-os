# agent-flywheel-os

Agent Flywheel, integrated into OpenShift AI's own open-source pieces:
evaluate, benchmark and train CLI agents (OpenCode, Claude Code, Codex) with
agent-eval-harness, EvalHub and a module of the OpenShift AI dashboard, on
Open Data Hub. The changes to those projects are built on Lukas's forks and
sent upstream as PRs; this repo holds the glue.

Start with the active spec,
[`docs/my-specs/02-generalization.md`](docs/my-specs/02-generalization.md),
section 0. The first version, which this one
is built from, is `~/Projects/Github/lukaskellerstein/openshift-eval`.

| File | What it holds |
|:--|:--|
| [`docs/my-specs/01-initial-implementation.md`](docs/my-specs/01-initial-implementation.md) | Spec 01, closed 2026-10-14 (it was `PLAN.md`): decisions 1 to 9, architecture, phases with their Definition of Done and what is done, contributions C1 to C19 and C30 to C34, risks |
| [`docs/my-specs/02-generalization.md`](docs/my-specs/02-generalization.md) | Spec 02, the active plan: one flywheel for any use case, decisions 10 on, the registry of use cases, contributions C19 to C29, every open step of spec 01 |
| [`docs/research.md`](docs/research.md) | The evidence: what each upstream project does today, with file and line |
| [`docs/outreach.md`](docs/outreach.md) | The Slack post to Red Hat colleagues, its fact-check, the blog fixes |
| [`docs/pr-drafts.md`](docs/pr-drafts.md) | The PR texts for the fork branches, not posted, and the order they must land in |
| [`docs/archive/03-upstream-first.md`](docs/archive/03-upstream-first.md) | The first spec, kept as history |
| [`scripts/clone-forks.sh`](scripts/clone-forks.sh) | Clones the forks into `~/Projects/Github/lukaskellerstein/forks/`, `origin` the fork, `upstream` the original |
| [`scripts/enmaas/probe.py`](scripts/enmaas/probe.py) | Measures what EnMaaS serves: which model ids answer, in which API dialect, with tools and streaming, how fast, at what price. Run in the gateway pod, where the key is |
| [`scripts/enmaas/agent_shapes.py`](scripts/enmaas/agent_shapes.py) | Checks the gateway with requests shaped like Claude Code's, Codex's, OpenCode's and the judge's. Run in the gateway pod |
| [`scripts/enmaas/models.md`](scripts/enmaas/models.md) | Every model EnMaaS serves, measured: time to the first token, tokens per second, list price. Written by the probe's `speed` stage |
| [`scripts/agent-kubeconfig.sh`](scripts/agent-kubeconfig.sh) | Mints the agent's own cluster login: applies `deploy/agent-access`, writes `~/.config/agent-kube/agent-flywheel-os.yaml` |
| [`deploy/agent-access/`](deploy/agent-access/) | The agent's identity: ServiceAccount `claude-agent`, cluster-admin |
| [`deploy/platform/`](deploy/platform/) | Open Data Hub 3.6.0-ea.2: the operator, the DSC, the dashboard's flags, ODH's MLflow, the EvalHub server |
| [`deploy/gateway/`](deploy/gateway/) | The LiteLLM model gateway, ported from `openshift-eval`, with every model alias and price; every route on EnMaaS since 2026-10-14 |
