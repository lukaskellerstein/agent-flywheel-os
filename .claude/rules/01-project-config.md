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
  (`README.md`, spec 01 §0 and §1, spec 02 §1)
- **Architecture**: planned, not built — spec 01 §4 has the diagram and the
  table of which part lives in which repo; spec 02 §4 adds the registry of use
  cases and says where each of its parts lives. This repo will own the loop,
  the flywheel API with the registry, the runner image and the gateway; the
  forks own everything else, and every gap goes upstream as a PR (spec 01
  §2, decision 1)
- **Structure**: `README.md` (the file index), `docs/` (`my-specs/`, the
  plan: `01-initial-implementation.md` closed, `02-generalization.md`
  active; `research.md`, the evidence with file and line; `outreach.md`, the
  Slack post drafts; `pr-drafts.md`, the PR texts for the fork branches;
  `archive/`, the first spec as history), and the first code,
  `services/flywheel-api/` (the registry of use cases and its API, spec 02
  phase 3, 2026-10-16), deployed by `deploy/flywheel-api/` on the bucket of
  `deploy/bucket/`.
  Spec 01 phase 0 step 4 adds `scripts/agent-kubeconfig.sh` and `deploy/agent-access/`;
  the README names `scripts/clone-forks.sh`; decision 9 adds
  `scripts/enmaas/` (the probe, the gateway check, the measured models). The rest of the layout
  (`flywheel/`, `images/runner/`, `usecases/support/`, the rest of
  `deploy/`) is agreed (spec 02 decision 16) and lands with spec 02 phase 3
- **Build / run / test**: the flywheel API's pytest suite
  (`rules/06-testing.md`). For the rest, the Definition of Done of the
  current phase in spec 02 §6 is the test, and its result is written into
  that phase's status before the next phase starts

## Related repos

The fork clones are worked on from this repo's session (Lukas, 2026-10-14):
the sandbox opens `~/Projects/Github/lukaskellerstein/forks/`, and the agent
here orchestrates subagents there. No git worktrees: one checkout per repo,
the branch switched in the clone itself, never two subagents in one clone,
and nothing at the `forks/` level (Lukas, 2026-10-14; spec 01 §0, §5).
Between tasks a clone sits on its `flywheel-integration`, or on `main`
before it has one. `openshift-eval` and
the reference checkouts stay read-only — read their files, never change
them from here.

| Repo | Path | Role |
|:--|:--|:--|
| openshift-eval | `~/Projects/Github/lukaskellerstein/openshift-eval`, branch `main` | The first version and the inspiration; keeps working as it is (decision 7). Its `PLAN.md`, `CLUSTER.md` and `flywheel/README.md` are the measured facts behind the specs; spec 01 §9 maps what is ported from it, and its branch `generalization` is read for spec 02 (spec 02 §0) |
| Fork clones, where all work happens | `~/Projects/Github/lukaskellerstein/forks/` `agent-eval-harness`, `eval-hub`, `eval-hub-contrib`, `trustyai-service-operator`, `odh-dashboard` | `origin` = Lukas's fork, `upstream` = the original; upstream code is read from `upstream/main` there. Contributions (spec 01 §7, spec 02 §5) are built there, one branch each from `upstream/main` plus `flywheel-integration` (spec 01 §5). Upstream's contribution rules win there (spec 01 §5) |
| Reference checkouts | `~/Projects/Github/redhat/agent-eval-harness`, `~/Projects/Github/eval-hub/eval-hub` | Read-only, never branch there; the first is `openshift-eval`'s editable dependency |

The first clones in `~/Projects/Github/lukaskellerstein/upstream/` are
dropped; no separate upstream clones (spec 01 §0). Training Hub has no fork
and no change now (decision 8); a plain clone of it, if ever needed, goes
under `~/Projects/Github/redhat/` (spec 01 §5).

## Cluster

- RHDP single node `cluster-nm8mw`, OpenShift 4.22.16, 32 CPU, 126 GiB
  memory, one 100 GB disk, no GPU; namespace `agent-flywheel` (spec 01
  §0, phase 0 status). Larger sizes could not be ordered on 2026-10-13, so
  the node's disk stays the limit for builds and images
- Platform: Open Data Hub 3.6.0-ea.2 with the dashboard, TrustyAI and ODH's
  MLflow, the real stack (decision 5); installed 2026-10-13 from
  `deploy/platform/`. Dashboard `https://rh-ai.apps.cluster-nm8mw.dyn.redhatworkshops.io`,
  EvalHub `https://evalhub.agent-flywheel.svc:8443`, MLflow
  `https://mlflow.opendatahub.svc:8443/mlflow`, gateway
  `http://gateway.agent-flywheel.svc:4000` (spec 01 phase 1 status)
- Agent access: the ServiceAccount `claude-agent`, cluster-admin (Lukas,
  2026-10-13), through `~/.config/agent-kube/agent-flywheel-os.yaml`, which
  a SessionStart hook sets as `KUBECONFIG` — ported from `openshift-eval` in
  spec 01 phase 0 step 4. Never `~/.kube/config`
