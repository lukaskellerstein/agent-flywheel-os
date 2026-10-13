<!--
Archived 2026-10-13. Copied word for word from
~/Projects/Github/lukaskellerstein/openshift-eval, branch
redesign-redhat-upstream, docs/my-specs/03-upstream-first.md. That branch
was discarded and the file was never committed there.

Read it as history. ../../PLAN.md supersedes it wherever the two differ.
Relative paths below (PLAN.md, flywheel/, deploy/, ui/, docs/my-specs/)
are paths in openshift-eval, not in this repo. Superseded since it was
written: section 5's last bullet (the cluster now gets Open Data Hub 3.6,
not the upstream TrustyAI operator) and section 8's "Not decided yet"
(answered by PLAN.md phase 5 and docs/research.md section 7).
-->

# Upstream first: contribute the gaps, keep a thin flywheel

Status: decided 2026-10-13, not built. Lukas: `ok` to the 8-step plan and to
clones apart from the reference checkouts; the same day `yes` to building
and proving every change on his forks before any PR (section 5), to five
forks, to pushes to them, and to the flywheel's UI as a module of the
OpenShift AI dashboard from the start (section 8); then route A, Open Data
Hub 3.6 with the dashboard and TrustyAI, and the move of the whole
integration to `~/Projects/Github/lukaskellerstein/agent-flywheel-os`, whose
`PLAN.md` is now the plan to build from. This repo is its inspiration and
stays as it is. `PLAN.md` section 2, row
"Upstream first", points here. The facts below were read on 2026-10-13 in
the upstream code (`gh`, the clones and the reference checkouts); each one
names its source.

## 1. The decision

The flywheel stops growing its own copies of what Red Hat's projects own.
Each gap we filled for ourselves goes upstream, into the project that owns
the topic. The flywheel keeps only what no project covers:

- the loop: score, adjust, keep or revert on the train score, a held-out
  validation set, versioned brains (`flywheel/controller.py`,
  `flywheel/adjust.py`, the Adjust backends);
- the agent × model × brain benchmark with exact reuse
  (`flywheel/benchmark.py`), until the harness covers it (section 4, item 12);
- the UI, which moves from the console (`ui/`) into a module of the OpenShift
  AI dashboard (section 8), and the OpenShift wiring (Jobs, ConfigMaps, the
  gateway).

Why: EvalHub is GA in Red Hat AI 3.5 and evaluates a model endpoint or
recorded agent traces. agent-eval-harness evaluates agents and skills, but it
is an upstream project, not a product. Training Hub lists GEPA prompt
optimization. None of them puts a CLI agent harness (OpenCode, Claude Code,
Codex) with its instructions and skills under test in a loop. The flywheel
is the agent layer above them, and it should make them better, not compete
with them.

## 2. The lineup on 2026-10-13

| Project | Status | Latest | Ours |
|:--|:--|:--|:--|
| EvalHub (`eval-hub/eval-hub`) | GA in Red Hat AI 3.5 (press release, 3.5 release notes); in the RHOAI operator branches `rhoai-3.4` and later; no upstream TrustyAI operator release has it (last release v1.38.0, 2025-06) | server 1.0.2 (2026-09-18), SDK 1.0.6 (2026-10-13) | server 1.0.2, SDK 1.0.5 |
| agent-eval-harness (`opendatahub-io/agent-eval-harness`) | Upstream only, a Claude Code plugin; no Red Hat product page names it | v1.56.1 (2026-10-12) | v1.53.0 in the image (`HARNESS_REF`), 1.53.3 on the laptop (the editable checkout) |
| Training Hub (`Red-Hat-AI-Innovation-Team/training_hub`) | 3.5 release notes: "Automated prompt optimization for agentic systems … by using Training Hub" (GA list); the 3.5 images pin 0.9.2 without the `[gepa]` extra | 0.11.0 (2026-10-12) | not used; `adjust_gepa.py` calls `gepa` 0.1.4 |
| MLflow | Managed component of OpenShift AI since 3.4 | — | 3.16.1 |

v1.56.1 of the harness fences the LLM judge's prompt (`score.py`), so our
scores can move on an upgrade, and every earlier run stops counting for a
benchmark reuse. Move the image and the laptop to one version on purpose.

## 3. Gap map

One row per piece we built ourselves. "Why" quotes our reason; "Upstream
today" is what the upstream code does now.

| Our piece | Why we built it | Upstream today | Contribution | Deletes here |
|:--|:--|:--|:--|:--|
| `stop_with_parent` in `eval/support/scripts/lib.sh` | A stop left the agents in flight running (`PLAN.md` section 0, the stop fix) | The harness's `cli` and Codex runners kill their process group only on a timeout (`cli_runner.py:152-163`, `codex.py:210-262`); `execute.py` has no SIGTERM handler; the Claude Code runner kills the CLI but not its children (`claude_code.py:412`) | SIGTERM handler, group kill on every exit, an optional parent-death watchdog for SIGKILL | `stop_with_parent` (the recipe hash moves) |
| `prices.sh` and the cost code in our runners | Gateway aliases have no price | Claude Code prices every token as Claude (`claude_code.py:948-956`); Codex looks the name up in `litellm.model_cost` and gets `None` for an alias (`codex.py:571-592`) | A price override per runner | `prices.sh`, the cost code |
| `run-claude-code.sh`, `run-codex.sh` | The gateway route; a fresh folder out of reach of `input.yaml` | The gateway works by env today (`ANTHROPIC_BASE_URL`, `OPENAI_BASE_URL`, `runner.settings`); the agent always runs in the case folder next to `input.yaml` (issues #150, #151) | Documented and tested gateway recipes; a workspace option without `input.yaml` | Both scripts |
| `run-opencode.sh` | No OpenCode runner | Draft PR #90 (astefanutti, last update 2026-06-10, 580 commits behind): copies all of `os.environ`, runs `--dangerously-skip-permissions`, writes `opencode.json` next to `input.yaml`, no process group; `events.py` parses no OpenCode events | A runner rebased from #90 without its OTel part, fixed on those points, with OpenCode in `events.py`; only after astefanutti agrees | `run-opencode.sh` (the quota retry may stay) |
| Trace building in `flywheel/run_eval.py` (`opencode_steps`, `claude_code_steps`, `codex_steps`, lines 760-914) | One trace per ticket for every agent | `/eval-mlflow` builds traces from Claude Code stream-json and Harbor trajectories only (`log_results.py:514-540`) | Per-format adapters in front of `build_trace` | The trace code |
| Our EvalHub provider (`flywheel/backends/score_evalhub.py`, lines 335-441) | The harness adapter "returns the judge means without the reasons" and "drops our runners" (`01-new-design.md` section 4.3) | The harness adapter returns per-judge means only, runs the cases one at a time, swallows a judge error, pins `eval-hub-sdk<1.0`; its image `quay.io/rhoai/agent-eval-hub` is not public | An `agent-eval-harness` adapter in `eval-hub-contrib` on the template of the ATIF adapter (PR #152, merged 2026-10-13), the provider YAML in `eval-hub` (an issue labelled `kind/architecture` first), the operator ConfigMap | The provider half of `score_evalhub.py` and its `provider.yaml`; the client stays |
| `deploy/evalhub/provider/` and `find_provider` | No API to register our provider with its resources | `K8sRuntime` in `pkg/api/providers.go:115-127` has no json tags, so the API drops the four resource fields that the OpenAPI schema names | Add the json tags | The provider ConfigMap, the `spec.providers` entry, `find_provider` |
| `export_run_folder` and the `flywheel.export` artifact | The run folder back through MLflow | SDK 1.0.6 streams MLflow file artifacts (`MlflowFileArtifact`), but the server injects `MLFLOW_WORKSPACE` into every job pod (`job_config.go:149-157`) and MLflow 3.16.1 refuses the header | Inject it only when the server's probe says workspaces are on | `export_run_folder`, the `mlflow_tracking_uri` parameter |
| `benchmark.py` | The agent × model × brain grid with reuse | `/eval-anova`: `runner.type` is fixed for the whole matrix, a factor named `agent` is shadowed by the `{agent}` placeholder, no reuse (`matrix-schema.md:31-39`, `orchestrate.py:111-123`) | `runner` as a factor; skip a cell whose recipe hash has a run | Most of `benchmark.py`; the console's Benchmark pages stay |
| Workarounds in `adjust_eval_optimize.py` | The skill must not start its own eval | `/eval-optimize` always re-runs `/eval-run` | An `--artifact` / no-verify mode | The hint and the narrowed `allowed-tools` |
| `decide()` in `controller.py:262` | Keep or revert in code, on the train score; validation never decides | `/eval-optimize`: the LLM decides a "major" revert, no held-out set; PR #73 (astefanutti, stalled since 2026-06-07) proposes a 40:20:40 split with a gate the LLM enforces | No PR; a comment on #73 with our data | Nothing; it stays |
| `adjust_gepa.py` | One GEPA proposal per Adjust step | Training Hub runs GEPA's whole search only, no single proposal; `import training_hub` loads torch; `[gepa]` resolves to 173 packages with CUDA; the adapter route asserts on `task_lm` (`gepa.py:385`, gepa `api.py:210-213`) | None now. Later, if we want GEPA as the whole engine: `task_lm` optional with an adapter, and lazy imports in `__init__.py` | Nothing; keep the direct `gepa` call |
| `TrialPod` in `score_harbor.py` | Harbor trials as pods on OpenShift, cleaned up with the Score Job | EvalHub ADR 0001, draft PR #1059 (julpayne, 2026-10-01, no review): a namespace per evaluation, a broker, then OpenShell (P1) and Kata (P2); it rejects cleanup in the tenant namespace for lack of deterministic cleanup | A comment with our data (section 6) | Nothing yet |
| `docs/my-specs/XX-sandboxing.md` | Kata and OpenShell for the agent under test | The same plan as ADR 0001's P1 and P2 | Help on the ADR instead of a second design | The proposal, once the ADR is accepted |

## 4. Order of work

Smallest and safest first. Each item is its own branch in its fork, from
upstream `main`, tested with that repo's own tests. No item becomes a PR
before the flywheel runs green on all of them together (section 5); the
three comments of section 6 are discussion, not PRs, and go out first.

1. Post the three comments of section 6.
2. Harness: stop on SIGTERM (a bug fix).
3. EvalHub: the json tags on `K8sRuntime` (a bug fix).
4. Harness: move the SDK pin to `>=1.0.6,<2`.
5. EvalHub: the local runtime fails a benchmark when the provider exits
   without a report (`local_runtime.go:414`).
6. Harness: a price override per runner.
7. Harness: the gateway recipes and the workspace option (#150, #151).
8. Harness: the OpenCode runner, after astefanutti answers on #90.
9. Harness: trace adapters for OpenCode, Codex and `cli`.
10. EvalHub: `MLFLOW_WORKSPACE` only when probed; then SDK 1.0.6 artifacts
    in our provider.
11. `eval-hub-contrib`: the `agent-eval-harness` adapter, the provider YAML
    in `eval-hub`, the operator ConfigMap.
12. Harness: `runner` as an `/eval-anova` factor with reuse; the
    `/eval-optimize` no-verify mode.
13. TrustyAI operator: the failure watcher posts `failed` when an adapter
    exits non-zero and the benchmark is not terminal.

Also: move our operator pin past #985 (`639411f`, the NetworkPolicy RBAC)
and drop `deploy/evalhub/provider/rbac.yaml`. Re-test first: our live note
says OpenShift needs `delete` for the ownerReference update that `main`
still makes (`k8s_runtime.go:396-403`), and #985's policy forbids `delete`.

## 5. How we work

- Clones: `~/Projects/Github/lukaskellerstein/upstream/` holds
  `agent-eval-harness`, `eval-hub`, `eval-hub-contrib` and `training_hub`
  (Lukas cloned them on 2026-10-13). The reference checkouts stay read-only.
- One Claude session per clone, started in that clone. This repo's worktree
  guard refuses git outside its own worktree, `!` commands included.
- The rules of each repo:
  - harness: no CONTRIBUTING file; conventional commits (semantic-release);
    spec-driven work in `specs/NNN`; `make test` (pytest) and the `skillsaw`
    lint in CI; astefanutti merges most PRs.
  - EvalHub: an issue first for a new framework or an API change
    (`kind/architecture` and `status/accepted`); conventional commits
    (commitlint); `git commit -s`; an `Assisted-by` line; `make clean
    test-all` and `pre-commit run --all-files`; review by
    `@eval-hub/maintainers`.
  - `eval-hub-contrib`: commitlint; `make test-<name>`; a `provider.yaml`
    per adapter; the images are published by its CI.
  - Training Hub: Google Python style, tests and docs (`docs/DEVELOPING.md`);
    a fork's PR needs a maintainer's `ok-to-test` label.
- Forks, made 2026-10-13: `github.com/lukaskellerstein/` `agent-eval-harness`,
  `eval-hub`, `eval-hub-contrib`, `trustyai-service-operator` and
  `odh-dashboard`. Training Hub has no fork: nothing changes there. In each
  clone `origin` is the fork and `upstream` the original.
- Branches: one per contribution, from upstream `main`, named after it
  (`fix/stop-on-sigterm`); and per repo one `flywheel-integration` branch
  that merges all of that repo's contribution branches. The integration
  branch is only for us and never a PR. A reviewer's change goes into the
  contribution branch, is merged into `flywheel-integration` again, and the
  proof runs again.
- Pushes go to the forks only, never to `upstream`, never to `main`, never
  `--force` (Lukas, 2026-10-13). A commit, a PR and a public comment still
  need his explicit go.
- The upstream edition: a branch of this repo that runs on the
  `flywheel-integration` branches. On the laptop `pyproject.toml` points at
  the clones; on the cluster `HARNESS_REF` in `deploy/build/Containerfile`
  names the fork's branch, and the EvalHub server, the contrib adapter and
  the dashboard are built on the cluster from the forks (EvalHub's image is
  the `evalHubImage` key in `deploy/evalhub/operator/kustomization.yaml`).
  When an upstream PR merges, the dependency goes back to a release.
- The proof, in this order: the phase tests' `compare.py` (the same MLflow
  records as before), one free loop on the local Gemma with the local judge,
  one paid smoke run on Qwen of about 0.2 USD (asked for first), then the
  same on the cluster. Only then step 7: one PR per contribution branch,
  rebased on upstream `main`.
- The cluster runs the upstream TrustyAI operator, not OpenShift AI. A green
  run there proves the code; the product check needs a cluster with
  OpenShift AI 3.5.

## 6. Opening comments (drafts, not posted)

### agent-eval-harness PR #90, to astefanutti

> Hi @astefanutti, I run agent-eval-harness with OpenCode as the agent under
> test, today through the `cli` runner and my own wrapper script. It is a
> project that evaluates, benchmarks and trains agents on OpenShift (OpenCode,
> Claude Code and Codex through a LiteLLM gateway). I would like to help get a
> native OpenCode runner into `main`.
>
> Would you be OK if I rebased this PR's runner onto current `main`, without
> the OTel receiver, as a fresh PR? From what I hit in practice, I would
> change these points:
>
> - an env allowlist like the other runners, instead of a copy of `os.environ`
> - OpenCode's permissions from its config, instead of
>   `--dangerously-skip-permissions`
> - the agent's config in its own folder, not in the case workspace next to
>   `input.yaml`
> - its own process group, killed on any exit
> - `execute()` instead of `run_skill`, the cost from `step_finish`, and the
>   OpenCode events in `events.py`
>
> If you would rather finish it yourself, I am happy to review it and test it
> against my setup instead.

### agent-eval-harness PR #73, to astefanutti and rhuss

> Hi @astefanutti, @rhuss, some data that may help with the question whether
> this ran end to end. I run an optimize loop around the harness: score on a
> train set and a held-out validation set, edit the agent's AGENTS.md and
> skills, score again, then keep or revert. The rule is code, not the LLM:
> keep if the train score is at least the best so far, revert otherwise. The
> validation set never decides, so it stays a clean held-out number, and the
> editor never judges its own edit.
>
> On 30 support tickets (20 train, 10 validation), Claude Code on Qwen 3.8 27B
> went from 0.649 to 0.910 on validation in 5 steps, with one candidate
> reverted. One caution for the gate: with sets this small, one run is not a
> measurement. In my benchmark, 5 repeated runs of one cell spread by about
> 0.05 (median).
>
> I would be glad to test this PR, or a smaller first tier (a held-out split
> and a score-based gate), against my setup.

### EvalHub PR #1059 (ADR 0001), to julpayne

> Hi @julpayne, a few data points from running Harbor trials as pods on
> OpenShift (single-node OCP 4.22, restricted-v2), in case they help the ADR:
>
> 1. Cleanup in the tenant namespace can be deterministic. Every trial pod
>    gets an ownerReference to the pod of the Job that started it, so a
>    suspended or deleted Job takes its trial pods with it. In my stop test
>    they were gone 36 s after the suspend, and a full run left no pod. That
>    may be worth a line next to the rejected tenant-namespace alternative.
> 2. Harbor's own cleanup is not enough. With Harbor 0.24 on Podman, a SIGINT
>    left 3 of 4 trial containers stopped but not removed. A reaper owned by
>    the broker or the operator looks right.
> 3. The verbs my trial pods needed: pods create, get, delete and pods/exec
>    create, get; no ServiceAccount token in the trial pod.
> 4. On OpenShift the SCC decides, not only PSA. Terminal-Bench style tasks
>    need root and the internet, so P0 will need an SCC story. I expect this
>    from the task images; I have not run it yet.
>
> I have a written design for the OpenShell (P1) and Kata (P2) layers, and I
> would be happy to help with either.

## 7. Not decided

- Where the loop lives after the contributions: the harness's
  `/eval-optimize` (a loop in code with a held-out set, near PR #73),
  Training Hub (an agent-optimization algorithm next to GEPA, EvalHub as the
  evaluator), or a controller behind the dashboard module. The maintainers'
  answers decide it. The demo (the dataset, the judges, the manifests) stays
  ours, as a Red Hat AI quickstart (`github.com/rh-ai-quickstart`) or in
  this repo. On 2026-10-13 the pieces with an upstream home were
  about 1,300 lines (the runners 703, the provider 445, the GEPA call 190)
  plus part of `run_eval.py`; the loop was 1,838 lines and the console about
  13,600.
- `02-harbor-benchmark.md` (decided, not built) runs Harbor's agents on a
  public task set. Before it is built here, check it against EvalHub's ATIF
  adapter (`eval-hub-contrib` PR #152) and ADR 0001, which both name Harbor.

## 8. The UI in the OpenShift AI dashboard

Lukas, 2026-10-13: the flywheel's UI is a module of the OpenShift AI
dashboard from the start, built in his fork of `opendatahub-io/odh-dashboard`
and deployed to his cluster, not the console of `ui/` first. Training Hub
has no UI (a Python library and the `thub` CLI); the OpenShift AI UI is the
dashboard, a monorepo of modules under `packages/`, each a frontend and a Go
backend, joined by Module Federation, with `packages/plugin-template` as the
scaffold. The modules that touch this work: `eval-hub` (the evaluation UI on
EvalHub), `agent-ops` (agent runtimes, capabilities and skills; changed
2026-10-08), `model-training` (Kubeflow TrainJobs), `mlflow`, `gen-ai`.

Not decided yet: how the fork is built and deployed on a cluster without
OpenShift AI (the ODH operator with only the dashboard, or the dashboard's
manifests applied by hand), how the new module is registered and switched
on, and the day-to-day dev loop. The next plan answers these, and every new
screen goes on the Design canvas for Lukas's review before it is built.
`ui/` stays as it is until the module can do what it does.
