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
  time — by the agent here or by a subagent it briefs. Never vendor or copy
  upstream code in here to work around a gap — the gap goes into the plan's
  contribution catalogue.
- **The layout below is agreed.** A new top-level folder is asked first.
  When a folder lands, add a section for it here: what belongs in it, and
  what must not.

## `docs/` — the plan, the evidence and the history

- `my-specs/` — the plan, one spec per stage, numbered. The active spec's
  section 0 is the handover: keep it true. When a fact in a spec turns out
  wrong, fix it in the same turn and say so; when a phase's Definition of
  Done is checked, write the result into its status before the next phase
  starts. Decisions keep one numbering across the specs and are Lukas's —
  change one only when he does.
- `research.md` — every fact read in upstream code and docs, with file and
  line; **V** verified, **I** inferred. The specs are the plan, this is the
  evidence: a new fact goes here with its source, and the spec cites it.
- `outreach.md` — the Slack post drafts to Red Hat colleagues. Lukas decides
  where and when it is posted.
- `pr-drafts.md` — the PR texts for the fork branches of every repo, one
  section per branch with its repo and head commit. Lukas opens each PR, in his own voice, after
  his go; a branch that changes gets its section rewritten.
- Decisions and status belong in the specs, not in the other files here.

## `specs/` — spex specs, one folder per step

- `NNN-slug/` holds one step's `spec.md` and, as it moves on, its
  `requirements.yaml`, `tasks.yaml` and `tests.yaml`. The spex commands
  create and change these files (`/spex:new` and the stages after it);
  `.spex/config.yaml` is their configuration. A roadmap links its steps
  through `roadmap`, `step` and `depends_on` in each `spec.md`.
- No task writes here (`protected` in `.spex/config.yaml`). The design a
  step is cut from stays in `docs/my-specs/`; a step names it as its
  `source`.

## `scripts/` — what Lukas runs from his own terminal

- `clone-forks.sh` (the fork clones) and `agent-kubeconfig.sh`
  (the agent's login). Both reach past this repo: one runs
  git in the fork clones, the other applies `deploy/agent-access` with
  Lukas's cluster-admin login. Test them offline (a fake remote, a fake
  kubeconfig). A real run of `clone-forks.sh` is Lukas's or asked for
  first; `agent-kubeconfig.sh` the agent runs itself, unsandboxed — the one
  command `.claude/settings.json` allows that way (`CLAUDE.md` § Cluster).
- `enmaas/probe.py`: measures which EnMaaS models answer, in
  which dialect. Python with the standard library only, so it runs in the
  gateway pod (`oc exec -i deploy/gateway -- python3 - < …`), where the key
  is, and the key never leaves the cluster. Every call to a model other
  than GLM 5.3 costs money: keep a stage's output tokens small, and print
  the tokens it spent. `enmaas/models.md` is the output of its `speed`
  stage, about 0.4 USD a run: run it again rather than edit the numbers.
  `enmaas/agent_shapes.py` checks the gateway with the agents' and the
  judge's request shapes, the same way, a few cents a run.
- Not here: code the loop or the API needs (`flywheel/`, `services/`).

## `services/` — our own services

- `flywheel-api/` — the registry of use cases and its API, FastAPI on S3. One
  Python project with its own `pyproject.toml`, `uv.lock` and
  `Containerfile`; the code in `flywheel_api/`, small modules (the task
  format and its checks, the use case's files, versions and their diff,
  the store, the import sources, the evaluations, their results as the
  module reads them, the agents of AI hub and the gateway's models, the
  client for EvalHub and MLflow, the routes); the
  offline tests in `tests/`, with EvalHub
  and MLflow faked in their real shapes. It joins S3, EvalHub and MLflow,
  which is why it is ours; a check the harness can hold goes upstream
  instead. One replica: the writes to a use case
  are serialised in its process.
- Not here: code an upstream project can hold, and any key. The bucket's
  key reaches the pod as env from the claim's Secret, and git runs with
  an environment that leaves it out. No identity of its own for EvalHub,
  MLflow or Jobs: an evaluation call and a training start carry their
  caller's token, and their records stay in EvalHub, MLflow and the
  training Job, not in the bucket.

## `usecases/` — use cases in the task format

- `smoke/`: three product questions, one deterministic judge as the
  reward, Codex through the cluster's gateway.
  A use case reaches the cluster only through the flywheel API's import,
  which makes it a fixed version in the bucket. Check one offline first
  with the harness's `validate_eval.py config` and `workspace.py`.
- `support/`: 30 tickets, the knowledge base in `resources/`, the policy
  in `hidden/`, deterministic judges and the adjuster's slots in
  `usecase.yaml`; this folder is its source.
- Not here: the API's test fixtures (`services/flywheel-api/tests/`), and
  any key: a model key never enters `eval.yaml`.

## `flywheel/` — the training loop

- One Python project, as `services/flywheel-api/`: `pyproject.toml`,
  `uv.lock`, the code in `flywheel_loop/` (HTTP, the API client, MLflow,
  the brain, the adjuster's reports, the adjuster, the controller), the
  adjuster's agent prompt `flywheel_loop/adjuster.md`, the offline tests
  in `tests/` with the API, MLflow and OpenCode faked.
- It scores nothing itself: every score is an evaluation of the flywheel
  API with the brain as the EvalHub adapter's `parameters.brain`. Keep or revert stays in
  code, on the train score only.
- Not here: a judge, a Score backend of its own, any key. The adjuster
  reaches its model through the gateway.

## `images/` — our own images

- `runner/`: the loop and OpenCode on our harness base image, built from
  this repo's root by `deploy/flywheel/build.yaml`.
- Not here: the images of the forks (`deploy/builds/`).

## `deploy/` — kustomize for the cluster

- `agent-access/` — the agent's identity, applied only by
  `agent-kubeconfig.sh`. A change here widens what every agent may do on the
  cluster: Lukas approves it before the next apply.
- `platform/` — Open Data Hub: `operator/` (the Subscription),
  `dsc/` (DSCInitialization and DataScienceCluster), `dashboard/` (a partial
  OdhDashboardConfig, server-side apply only), `mlflow/` (ODH's MLflow),
  `evalhub/` (the EvalHub server, its PostgreSQL with the claim that
  holds every job, and the adapter's provider as a tenant ConfigMap that its
  `spec.providers` names, with our adapter image by digest: a new
  adapter build changes that digest; the database's Secret `evalhub-db`
  is made on the cluster, never here). Applied in that order;
  each needs the one before it. Configuration of ODH's own objects; the
  Subscription also points ODH at our operator and EvalHub images.
- `gateway/` — LiteLLM; every route is EnMaaS. Every model
  alias and price lives in `config/`, never a key. `litellm.yaml` also
  goes out as the ConfigMap `gateway-models`, with no hash, for the
  flywheel API's AI hub › Models: an alias added here is a model an agent
  may use after the next apply. A GPT or Claude alias
  must pass the hook untouched: `cerebras_hook.py` acts only on the
  prefixes in its `CHAT_ONLY`. After a change, run
  `scripts/enmaas/agent_shapes.py` against the gateway.
- `builds/` — ImageStreams and binary
  BuildConfigs for the fork clones (the TrustyAI operator, the EvalHub
  server, the harness's base image and the EvalHub adapter on top of it,
  from each `flywheel-integration`; our dashboard module and our
  dashboard-operator from odh-dashboard's `feat/agent-flywheel-module`),
  and the pull right ODH's `opendatahub` namespace needs for
  them. A build that a binary upload cannot give its args to sets them in
  the BuildConfig (`dockerStrategy.from` for the adapter's base). A build uploads one commit with
  `oc start-build <bc> --from-repo=<clone> --commit=<sha>`, never a
  working tree with changes nobody committed. No push to any registry
  outside the cluster.
- `bucket/` — the ObjectBucketClaim
  `flywheel-usecases` on the cluster's NooBaa. NooBaa answers it with a
  ConfigMap and a Secret of the same name; pods take them with `envFrom`,
  and nothing here holds or copies a key. Deleting the claim deletes the
  bucket and every use case version in it.
- `flywheel-api/` — the API of `services/flywheel-api/` on the cluster:
  an ImageStream and a binary BuildConfig whose context is that folder
  (`oc start-build flywheel-api --from-repo=<this repo> --commit=<sha>`),
  a Deployment with an image trigger that takes the bucket claim's
  ConfigMap and Secret with `envFrom`, and a ClusterIP Service on 8080. No
  Route: the dashboard module's BFF calls it inside the cluster. For
  evaluations: the service CA (both EvalHub and MLflow serve with it) and
  a NetworkPolicy that adds the API pod to those EvalHub admits.
  `agents/` holds the AI hub › Agents records the cluster starts with,
  one JSON per agent, posted to `POST /api/agents` (kustomize does not
  apply them); an agent is never changed, so a new wiring is a new
  name. A value for a variable that names a key is the gateway's
  placeholder, never a key.
- `flywheel/` — the training loop on the cluster: the runner image's
  binary BuildConfig (context: this repo's root), the ServiceAccount
  `flywheel-loop` with only the rights EvalHub and MLflow check, and
  `training-job.yaml`, one training run. Kustomize applies it only as
  the ConfigMap `flywheel-training-job`, the template the flywheel API's
  Start training creates the Job from, as the caller (a change needs a
  restart of the API); by hand, `oc create -f`. A paid training run is
  asked for first, with its cost: a run whose agent and adjuster models
  are free on the gateway (GLM 5.3) costs nothing.

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
│   ├── flywheel/     the runner image's build, the loop's identity, a training Job
│   └── gateway/      LiteLLM, every model alias and price
├── docs/
│   ├── my-specs/     the plan — read the active spec's section 0 first
│   ├── research.md   the evidence behind the specs
│   ├── outreach.md   the Slack post drafts
│   └── pr-drafts.md  the PR texts for the fork branches
├── flywheel/         the training loop
├── specs/            spex specs, one folder per step
├── images/
│   └── runner/       the loop and OpenCode on our harness image
├── usecases/
│   ├── smoke/        three product questions
│   └── support/      30 support tickets
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
