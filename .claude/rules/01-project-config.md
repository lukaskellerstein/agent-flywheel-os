---
description: Project configuration — architecture, paths, dev environment
---

# Project Config

<!-- Filled from what the repo actually contains. Every line must be verifiable
     by reading a file in the repo — never write an aspiration here. Delete any
     bullet that does not apply rather than leaving a placeholder.
     Machine paths are written `~/Projects/...`, never `/Users/<name>/...`: the
     username is wrong on every other machine and wrong here too if it was
     guessed. A path outside this repo is verified with `ls` before it is
     written — including its capitalisation, which macOS forgives and Linux
     does not.
     No plan, phase, status or date here: those live in `docs/my-specs/`. -->

- **Project**: agent-flywheel-os — the glue for Agent Flywheel on Open Data
  Hub: evaluate, benchmark and train CLI agents (OpenCode, Claude Code, Codex)
  with agent-eval-harness, EvalHub and an OpenShift AI dashboard module
  (`README.md`)
- **Architecture**: this repo owns the training loop, the flywheel API with
  the registry of use cases, the runner image and the gateway; the forks own
  everything else, and every gap goes upstream as a PR
- **Structure**: the folders and what belongs in each are in
  [`05-implement.md`](05-implement.md); `README.md` indexes every file
- **Build / run / test**: the offline pytest suites of the flywheel API and
  the loop ([`06-testing.md`](06-testing.md)); manifests reach the cluster
  with `oc apply -k`

## Related repos

The fork clones are worked on from this repo's session: the sandbox opens
`~/Projects/Github/lukaskellerstein/forks/`, and the agent here orchestrates
subagents there. No git worktrees: one checkout per repo, the branch
switched in the clone itself, never two subagents in one clone, and nothing
at the `forks/` level. Between tasks a clone sits on its
`flywheel-integration`, or on `main` before it has one. The reference
checkouts stay read-only — read their files, never change them from here.

| Repo | Path | Role |
|:--|:--|:--|
| Fork clones, where all work happens | `~/Projects/Github/lukaskellerstein/forks/` `agent-eval-harness`, `eval-hub`, `eval-hub-contrib`, `trustyai-service-operator`, `odh-dashboard` | `origin` = Lukas's fork, `upstream` = the original; upstream code is read from `upstream/main` there. Each contribution is built there on its own branch from `upstream/main`, and merged into `flywheel-integration`. Upstream's contribution rules win there |
| Reference checkouts | `~/Projects/Github/redhat/agent-eval-harness`, `~/Projects/Github/eval-hub/eval-hub` | Read-only, never branch there |

No separate upstream clones. Training Hub has no fork; a plain clone of it,
if ever needed, goes under `~/Projects/Github/redhat/`.

## Cluster

- RHDP single node `cluster-nm8mw`, OpenShift 4.22.16, 32 CPU, 126 GiB
  memory, one 100 GB disk, no GPU; namespace `agent-flywheel`. The node's
  disk is the limit for builds and images
- Platform: Open Data Hub 3.6.0-ea.2 with the dashboard, TrustyAI and ODH's
  MLflow, from `deploy/platform/`. Dashboard
  `https://rh-ai.apps.cluster-nm8mw.dyn.redhatworkshops.io`, EvalHub
  `https://evalhub.agent-flywheel.svc:8443`, MLflow
  `https://mlflow.opendatahub.svc:8443/mlflow`, gateway
  `http://gateway.agent-flywheel.svc:4000`
- Agent access: the ServiceAccount `claude-agent`, cluster-admin, through
  `~/.config/agent-kube/agent-flywheel-os.yaml`, which a SessionStart hook
  sets as `KUBECONFIG`. Never `~/.kube/config`
