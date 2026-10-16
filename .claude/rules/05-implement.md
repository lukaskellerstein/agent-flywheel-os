---
description: "Step 3: Implement — coding rules and this project's layout"
---

# Step 3: Implement

Write clean code from the start. Follow these rules during implementation:

- Every edit in this repo stays in the checkout assigned to this session.
  Claude Code uses `.worktrees/<name>`; Codex uses its active Local or
  managed Worktree checkout and Handoff. Never edit another checkout of
  this repo — [`worktree.md`](worktree.md). The fork clones are the
  exception, worked on in place (below and `CLAUDE.md`).
- Do NOT commit in this repo unless the user asks for that commit. In the
  fork clones, commits on the contribution branches and on
  `flywheel-integration` are pre-approved (`CLAUDE.md`), never on `main`
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

- `README.md` — the repo's front page and its file index: a file that lands
  at the top level or in `docs/` gets a row there.
- **This repo holds only the glue.** A change to agent-eval-harness, EvalHub,
  eval-hub-contrib, the TrustyAI operator or the dashboard is a contribution:
  it is made in that fork's clone `forks/<repo>`, on its own branch,
  switched in the clone itself — no worktrees, one subagent per clone at a
  time — by the agent here or by a subagent it briefs (spec 01 §5). Never vendor or copy upstream code in here to work
  around a gap — the gap goes into the catalogue (spec 01 §7, spec 02 §5).
- **A new top-level folder needs a home in a spec.** The ones a phase
  already names are approved with that phase: `scripts/agent-kubeconfig.sh`
  and `deploy/agent-access/` (spec 01 phase 0 step 4), `scripts/clone-forks.sh`
  (spec 01 §5, the README), `deploy/builds/` (spec 02 phase 2). The rest
  of the layout (`services/flywheel-api/`, `flywheel/`, `images/runner/`,
  `usecases/support/`, the rest of `deploy/`) is agreed for spec 02 phase
  3 (spec 02 decision 16); any other folder is asked first. When a folder lands, add a
  section for it here: what belongs in it, and what must not.

## `docs/` — the plan, the evidence and the history

- `my-specs/` — the plan, one spec per stage, numbered:
  `01-initial-implementation.md` (closed 2026-10-14, it was `PLAN.md`) and
  `02-generalization.md` (active). The active spec's section 0 is the
  handover: keep it true. When a fact in a spec turns out wrong, fix it in
  the same turn and say so; when a phase's Definition of Done is checked,
  write the result into its status before the next phase starts (spec 01
  §0, §6). Decisions keep one numbering across the specs (1 to 9 in spec 01
  §2, 10 on in spec 02 §2) and are Lukas's — change one only when he does.
- `research.md` — every fact read in upstream code and docs, with file and
  line; **V** verified, **I** inferred. The specs are the plan, this is the
  evidence: a new fact goes here with its source, and the spec cites it.
- `outreach.md` — the Slack post drafts to Red Hat colleagues. Lukas decides
  where and when it is posted.
- `pr-drafts.md` — the PR texts for the fork branches of every repo, one
  section per branch with its repo and head commit. Lukas opens each PR, in his own voice, after
  his go; a branch that changes gets its section rewritten.
- `archive/` — history, copied word for word. Never edit an archived file;
  the specs win where they differ.
- Decisions and status belong in the specs, not in the other files here.

## `scripts/` — what Lukas runs from his own terminal

- `clone-forks.sh` (the fork clones, spec 01 §5) and `agent-kubeconfig.sh`
  (the agent's login, spec 01 phase 0 step 4). Both reach past this repo: one runs
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
- Not here: code the loop or the API needs. That waits for the layout of
  spec 02 phase 3.

## `services/` — our own services

- `flywheel-api/` — spec 02 phase 3 step 2: the registry of use cases
  (decision 11) and its API (decision 16 question 2), FastAPI on S3. One
  Python project with its own `pyproject.toml`, `uv.lock` and
  `Containerfile`; the code in `flywheel_api/`, small modules (the task
  format and its checks, the use case's files, versions and their diff,
  the store, the import sources, the routes); the offline tests in
  `tests/`. It joins S3, EvalHub and MLflow, which is why it is ours
  (spec 02 section 4.5); a check the harness can hold goes upstream
  instead (C26). One replica: the writes to a use case are serialised in
  its process.
- Not here: code an upstream project can hold, and any key. The bucket's
  key reaches the pod as env from the claim's Secret, and git runs with
  an environment that leaves it out.

## `usecases/` — use cases in the task format

- `smoke/` (spec 02 decision 19): three product questions, one
  deterministic judge as the reward, Codex through the cluster's gateway;
  the first EvalHub job's test data. `support/` follows (phase 3 step 5).
  A use case reaches the cluster only through the flywheel API's import,
  which makes it a fixed version in the bucket. Check one offline first
  with the harness's `validate_eval.py config` and `workspace.py`.
- Not here: the API's test fixtures (`services/flywheel-api/tests/`), and
  any key: a model key never enters `eval.yaml`.

## `deploy/` — kustomize for the cluster

- `agent-access/` — the agent's identity, applied only by
  `agent-kubeconfig.sh`. A change here widens what every agent may do on the
  cluster: Lukas approves it before the next apply.
- `platform/` — Open Data Hub, spec 01 phase 1: `operator/` (the Subscription),
  `dsc/` (DSCInitialization and DataScienceCluster), `dashboard/` (a partial
  OdhDashboardConfig, server-side apply only), `mlflow/` (ODH's MLflow),
  `evalhub/` (the EvalHub server). Applied in that order; each needs the one
  before it. Configuration of ODH's own objects; from spec 02 phase 2 the
  Subscription also points ODH at our operator and EvalHub images.
- `gateway/` — LiteLLM, spec 01 phase 1 step 6, ported from `openshift-eval`;
  every route is EnMaaS since 2026-10-14 (decision 9). Every model
  alias and price lives in `config/`, never a key. A GPT or Claude alias
  must pass the hook untouched: `cerebras_hook.py` acts only on the
  prefixes in its `CHAT_ONLY`. After a change, run
  `scripts/enmaas/agent_shapes.py` against the gateway.
- `builds/` — spec 02 phase 2 step 1: ImageStreams and binary
  BuildConfigs for the fork clones (the TrustyAI operator, the EvalHub
  server, the harness's base image and the EvalHub adapter on top of it,
  from each `flywheel-integration`; our dashboard module and our
  dashboard-operator from odh-dashboard's `feat/agent-flywheel-module`,
  phase 5), and the pull right ODH's `opendatahub` namespace needs for
  them. A build that a binary upload cannot give its args to sets them in
  the BuildConfig (`dockerStrategy.from` for the adapter's base). A build uploads one commit with
  `oc start-build <bc> --from-repo=<clone> --commit=<sha>`, never a
  working tree with changes nobody committed. No push to any registry
  outside the cluster.
- `bucket/` — spec 02 phase 3 step 1 (decision 17): the ObjectBucketClaim
  `flywheel-usecases` on the cluster's NooBaa. NooBaa answers it with a
  ConfigMap and a Secret of the same name; pods take them with `envFrom`,
  and nothing here holds or copies a key. Deleting the claim deletes the
  bucket and every use case version in it.
- `flywheel-api/` — the API of `services/flywheel-api/` on the cluster:
  an ImageStream and a binary BuildConfig whose context is that folder
  (`oc start-build flywheel-api --from-repo=<this repo> --commit=<sha>`),
  a Deployment with an image trigger that takes the bucket claim's
  ConfigMap and Secret with `envFrom`, and a ClusterIP Service on 8080. No
  Route: the dashboard module's BFF calls it inside the cluster.
- Not here yet: the flywheel Jobs. They land with spec 02 phase 3.

## Repository structure

```text
agent-flywheel-os/
├── .claude/          agent instructions — CLAUDE.md, rules/, hooks/, settings.json
├── .mcp.json         the Playwright MCP server, playwright-agent-flywheel-os
├── README.md         the front page and the file index
├── deploy/
│   ├── agent-access/ the agent's ServiceAccount and its RBAC
│   ├── platform/     Open Data Hub: operator, DSC, dashboard flags, MLflow, EvalHub
│   ├── builds/       our images of the forks, built on the cluster
│   ├── bucket/       the registry's S3 bucket claim
│   ├── flywheel-api/ the API's build, Deployment and Service
│   └── gateway/      LiteLLM, every model alias and price
├── docs/
│   ├── my-specs/     the plan: 01 closed, 02 active — read its section 0 first
│   ├── research.md   the evidence behind the specs
│   ├── outreach.md   the Slack post drafts
│   ├── pr-drafts.md  the PR texts for the fork branches
│   └── archive/      the first spec, as history
├── services/
│   └── flywheel-api/ the registry of use cases and its API (FastAPI, S3)
└── scripts/
    ├── agent-kubeconfig.sh  the agent's own cluster login
    ├── clone-forks.sh       the fork clones
    └── enmaas/
        ├── probe.py         what EnMaaS serves, measured
        ├── agent_shapes.py  the gateway, checked with the agents' requests
        └── models.md        its speed and price per model
```
