---
description: "Step 3: Implement — coding rules and this project's layout"
---

# Step 3: Implement

Write clean code from the start. Follow these rules during implementation:

- Every edit stays in the checkout assigned to this session. Claude Code uses
  `.worktrees/<name>`; Codex uses its active Local or managed Worktree checkout
  and Handoff. Never edit another checkout — [`worktree.md`](worktree.md)
- Do NOT commit via `git` unless explicitly instructed by the user
- When creating diagrams or graphs, use `mermaid`
- Write clean code from the start — don't plan to "clean it up later"
- Refactor continuously — improve code structure immediately when you see issues
- Remove dead code — delete unused functions, variables, imports, and commented code
- Before changing any signature, renaming, or deleting something shared, find
  every caller with `findReferences` where the `LSP` tool is available — grep
  misses the ones spelled differently and finds ones that are not calls.
  [`lsp.md`](lsp.md)
- After writing code: review comments, clean up imports, check for side effects

## Top level

- `PLAN.md` — the integrated plan and its status. Section 0 is the handover:
  keep it true. When a fact in it turns out wrong, fix it in the same turn and
  say so; when a phase's Definition of Done is checked, write the result into
  its status before the next phase starts (`PLAN.md` §0, §6). Section 2 holds
  Lukas's decisions — change one only when he does.
- `README.md` — the repo's front page and its file index: a file that lands
  at the top level or in `docs/` gets a row there.
- **This repo holds only the glue.** A change to agent-eval-harness, EvalHub,
  eval-hub-contrib, the TrustyAI operator or the dashboard is a contribution:
  it is made in that fork's clone, on its own branch, in that branch's git
  worktree `forks/.worktrees/<repo>/<branch>` — by the agent here or by a
  subagent it briefs (`PLAN.md` §5). Never vendor or copy upstream code in here to work
  around a gap — the gap goes into the catalogue (`PLAN.md` §7).
- **A new top-level folder needs a home in the plan.** The ones a phase
  already names are approved with that phase: `scripts/agent-kubeconfig.sh`
  and `deploy/agent-access/` (phase 0 step 4), `scripts/clone-forks.sh`
  (§5, the README). The rest of the phase 4 layout is agreed with Lukas
  before phase 4 starts (`PLAN.md` §6, phase 4). When a folder lands, add a
  section for it here: what belongs in it, and what must not.

## `docs/` — the evidence and the history, not the plan

- `research.md` — every fact read in upstream code and docs, with file and
  line; **V** verified, **I** inferred. `PLAN.md` is the plan, this is the
  evidence: a new fact goes here with its source, and the plan cites it.
- `outreach.md` — the Slack post drafts to Red Hat colleagues. Lukas decides
  where and when it is posted.
- `pr-drafts.md` — the PR texts for the fork branches, one section per
  branch with its head commit. Lukas opens each PR, in his own voice, after
  his go; a branch that changes gets its section rewritten.
- `archive/` — history, copied word for word. Never edit an archived file;
  `PLAN.md` wins where they differ.
- Not here: decisions or status. Those belong in `PLAN.md`.

## `scripts/` — what Lukas runs from his own terminal

- `clone-forks.sh` (the fork clones, `PLAN.md` §5) and `agent-kubeconfig.sh`
  (the agent's login, phase 0 step 4). Both reach past this repo: one runs
  git in the fork clones, the other applies `deploy/agent-access` with
  Lukas's cluster-admin login. Test them offline (a fake remote, a fake
  kubeconfig). A real run of `clone-forks.sh` is Lukas's or asked for
  first; `agent-kubeconfig.sh` the agent runs itself, unsandboxed — the one
  command `.claude/settings.json` allows that way (`CLAUDE.md` § Cluster).
- `enmaas/probe.py` (decision 9): measures which EnMaaS models answer, in
  which dialect. Python with the standard library only, so it runs in the
  gateway pod (`oc exec -i deploy/gateway -- python3 - < …`), where the key
  is, and the key never leaves the cluster. Every call to a model other
  than GLM 5.3 costs money: keep a stage's output tokens small, and print
  the tokens it spent. `enmaas/models.md` is the output of its `speed`
  stage, about 0.4 USD a run: run it again rather than edit the numbers.
  `enmaas/agent_shapes.py` checks the gateway with the agents' and the
  judge's request shapes, the same way, a few cents a run.
- Not here: code the loop or the API needs. That waits for the phase 4
  layout.

## `deploy/` — kustomize for the cluster

- `agent-access/` — the agent's identity, applied only by
  `agent-kubeconfig.sh`. A change here widens what every agent may do on the
  cluster: Lukas approves it before the next apply.
- `platform/` — Open Data Hub, phase 1: `operator/` (the Subscription),
  `dsc/` (DSCInitialization and DataScienceCluster), `dashboard/` (a partial
  OdhDashboardConfig, server-side apply only), `mlflow/` (ODH's MLflow),
  `evalhub/` (the EvalHub server). Applied in that order; each needs the one
  before it. Configuration of ODH's own objects, nothing of ours.
- `gateway/` — LiteLLM, phase 1 step 6, ported from `openshift-eval`; every
  route is EnMaaS since 2026-10-14 (`PLAN.md` decision 9). Every model
  alias and price lives in `config/`, never a key. A GPT or Claude alias
  must pass the hook untouched: `cerebras_hook.py` acts only on the
  prefixes in its `CHAT_ONLY`. After a change, run
  `scripts/enmaas/agent_shapes.py` against the gateway.
- Not here yet: the flywheel Jobs and the API. They land with phase 4.

## Repository structure

```text
agent-flywheel-os/
├── .claude/          agent instructions — CLAUDE.md, rules/, hooks/, settings.json
├── .mcp.json         the Playwright MCP server, playwright-agent-flywheel-os
├── PLAN.md           the integrated plan — read section 0 first
├── README.md         the front page and the file index
├── deploy/
│   ├── agent-access/ the agent's ServiceAccount and its RBAC
│   ├── platform/     Open Data Hub: operator, DSC, dashboard flags, MLflow, EvalHub
│   └── gateway/      LiteLLM, every model alias and price
├── docs/
│   ├── research.md   the evidence behind the plan
│   ├── outreach.md   the Slack post drafts
│   ├── pr-drafts.md  the PR texts for the fork branches
│   └── archive/      the first spec, as history
└── scripts/
    ├── agent-kubeconfig.sh  the agent's own cluster login
    ├── clone-forks.sh       the fork clones
    └── enmaas/
        ├── probe.py         what EnMaaS serves, measured
        ├── agent_shapes.py  the gateway, checked with the agents' requests
        └── models.md        its speed and price per model
```
