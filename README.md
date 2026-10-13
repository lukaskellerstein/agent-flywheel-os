# agent-flywheel-os

Agent Flywheel, integrated into OpenShift AI's own open-source pieces:
evaluate, benchmark and train CLI agents (OpenCode, Claude Code, Codex) with
agent-eval-harness, EvalHub and a module of the OpenShift AI dashboard, on
Open Data Hub. The changes to those projects are built on Lukas's forks and
sent upstream as PRs; this repo holds the glue.

Start with [`PLAN.md`](PLAN.md), section 0. The first version, which this one
is built from, is `~/Projects/Github/lukaskellerstein/openshift-eval`.

| File | What it holds |
|:--|:--|
| [`PLAN.md`](PLAN.md) | The plan: decisions, architecture, phases with their Definition of Done, contributions, risks |
| [`docs/research.md`](docs/research.md) | The evidence: what each upstream project does today, with file and line |
| [`docs/outreach.md`](docs/outreach.md) | The Slack post to Red Hat colleagues, its fact-check, the blog fixes |
| [`docs/archive/03-upstream-first.md`](docs/archive/03-upstream-first.md) | The first spec, kept as history |
| [`scripts/clone-forks.sh`](scripts/clone-forks.sh) | Clones the forks into `~/Projects/Github/lukaskellerstein/forks/`, `origin` the fork, `upstream` the original |
