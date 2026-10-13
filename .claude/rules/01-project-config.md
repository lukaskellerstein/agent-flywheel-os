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
     does not. -->

- **Project**: agent-flywheel-os — the glue for Agent Flywheel on Open Data
  Hub: evaluate, benchmark and train CLI agents (OpenCode, Claude Code, Codex)
  with agent-eval-harness, EvalHub and an OpenShift AI dashboard module
  (`README.md`, `PLAN.md` §0, §1)
- **Architecture**: planned, not built — `PLAN.md` §4 has the diagram and the
  table of which part lives in which repo. This repo will own the loop, the
  flywheel API, the dataset, the runner image and the gateway; the forks own
  everything else, and every gap goes upstream as a PR (§2, decision 1)
- **Structure**: `README.md`, `PLAN.md`. Nothing else yet. The phase 4 layout
  (`datasets/support/`, `images/runner/`, `flywheel/`,
  `services/flywheel-api/`, `deploy/`) is a proposal to agree with Lukas
  before phase 4 starts (`PLAN.md` §6, phase 4)
- **Build / run / test**: none yet. Until code lands, the Definition of Done of
  the current phase in `PLAN.md` §6 is the test, and its result is written
  into the plan's status before the next phase starts

## Related repos

Each one gets its own Claude session, started in its own folder. A session in
this repo's worktree cannot run git in any of them (`PLAN.md` §0, seen
2026-10-13) — read their files, never change them from here.

| Repo | Path | Role |
|:--|:--|:--|
| openshift-eval | `~/Projects/Github/lukaskellerstein/openshift-eval`, branch `main` | The first version and the inspiration; keeps working as it is (decision 7). Its `PLAN.md`, `CLUSTER.md` and `flywheel/README.md` are the measured facts behind this plan; `PLAN.md` §9 maps what is ported from it |
| Fork clones | `~/Projects/Github/lukaskellerstein/upstream/` `agent-eval-harness`, `eval-hub`, `eval-hub-contrib` | Where contributions C1–C13 are built, one branch each plus `flywheel-integration` (§5, §7). Upstream's contribution rules win there (§5) |
| Not cloned yet | `trustyai-service-operator`, `odh-dashboard` | Cloned from the forks by the commands in `PLAN.md` §5; the operator takes C14, `odh-dashboard` the `agent-flywheel` module (C15, phase 5) |
| Training Hub | `~/Projects/Github/lukaskellerstein/upstream/training_hub` | A plain clone, no fork: no change now (decision 8) |
| Reference checkouts | `~/Projects/Github/redhat/agent-eval-harness`, `~/Projects/Github/eval-hub/eval-hub` | Read-only, never branch there; the first is `openshift-eval`'s editable dependency |

## Cluster

- RHDP single node `cluster-vj7vb`, OpenShift 4.22, no GPU; namespace
  `agent-flywheel` (`PLAN.md` §0, phase 0). It did not answer on 2026-10-13
  and may be stopped or gone — a replacement gets a bigger disk (phase 0)
- Platform: Open Data Hub 3.6 with the dashboard and TrustyAI, the real stack
  (decision 5); installed in phase 1, not yet
- Agent access: the ServiceAccount `claude-agent`, admin in `agent-flywheel`
  only, through a kubeconfig outside the repo — ported from `openshift-eval`
  in phase 0 step 4, not built yet. Never `~/.kube/config`
