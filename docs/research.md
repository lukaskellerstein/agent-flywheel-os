# Research behind the plan

Gathered on 2026-10-13 by a Claude session in
`~/Projects/Github/lukaskellerstein/openshift-eval` (branch
`redesign-redhat-upstream`, discarded afterwards: everything it found is
here), with nine research agents reading upstream code through `gh` and the
local clones, and direct checks. **V** = verified in code, an API or a doc;
**I** = inferred, not run. Line numbers are of upstream `main` on that day
unless a version is named. The specs in `docs/my-specs/` are the plan; this file is the evidence.

## 1. Positioning: contribute, do not compete

**What OpenShift AI already has (V):**

- Evaluates models (TrustyAI LM-Eval) and, with EvalHub, agents: EvalHub is
  GA in Red Hat AI 3.5 for "custom models, RAG and agents" (press release);
  agents are judged from recorded traces (IBM CLEAR on MLflow traces,
  developers.redhat.com, 2026-09-03, needs OpenShift AI 3.4 or later).
- Fine-tunes models: Kubeflow Trainer and Training Hub (SFT, OSFT, LoRA,
  GRPO; fine-tuning pipelines since 3.3).
- MLflow as a managed component since 3.4; "MLflow visual agentic tracing"
  in 3.5.
- 3.5 also: agent templates (code review, document processing, research),
  the Responses API GA with built-in RAG, NeMo Guardrails on tool calls,
  models validated for tool calling, Garak scores in the catalog.
- Dashboard modules `eval-hub`, `agent-ops`, `model-training`, `mlflow`,
  `gen-ai`, `autorag`, `automl` (section 7).

**What we did not find (searched, not proven absent):** a feature that puts
a CLI agent harness (OpenCode, Claude Code, Codex) with its instructions and
skills under test, compares harnesses × models, or trains an agent's brain
in a closed loop with a held-out set. Training Hub's GEPA optimizes prompts
in one process; the harness's `/eval-optimize` lets the LLM judge its own
revert; EvalHub has no optimization. Someone inside Red Hat may have work
that is not public, and that is a good answer to get.

**Options weighed:** A, contribute every gap and keep a thin layer on top
(picked); B, a separate product on top (reads as a duplicate of EvalHub); C,
merge everything and keep nothing (the loop and the grid have no home).

**What stays ours, measured in `openshift-eval` on 2026-10-13:** with an
upstream home: the runner scripts `eval/support/scripts/*.sh` 703 lines, our
EvalHub provider `flywheel/backends/score_evalhub.py` 445, the GEPA call
`adjust_gepa.py` 190, plus part of `run_eval.py` (1,271). Staying: the loop
`controller.py` 676, `adjust.py` 654, `benchmark.py` 508 (1,838 together),
the other backends (`__init__.py` 233, `adjust_adjuster.py` 129,
`adjust_eval_optimize.py` 299, `score_harbor.py` 339, `score_harness.py`
75), the console `ui/server` 3,373 and `ui/web/src` 10,253, the gateway
config 404. If Training Hub or EvalHub later add an agent loop, the
flywheel shrinks to a UI and a quickstart; that still puts the work in the
product.

## 2. OpenShift AI product facts

- **EvalHub.** Introduced in 3.4 (SDK, CLI and the Evaluation Stack UI as
  Technology Preview). 3.5 "new features": "EvalHub is generally available
  (GA). This release includes a documented API versioning scheme, an
  established breaking change policy, and full Red Hat support", covering
  models, AI applications, agents and tools. Still Technology Preview in
  3.5: run comparison (it names agentic AI systems), thresholds, the MCP
  server, Kueue routing, OTLP metrics export. Shipped by the TrustyAI Service
  Operator (`EvalHub` resource). Known issue RHOAIENG-66068: the dashboard
  finds an EvalHub multi-tenant instance only in `redhat-ods-applications`.
- **MLflow.** The MLflow Operator is a managed component of the
  `DataScienceCluster` since 3.4; the SDK is preinstalled in the datascience,
  tensorflow, pytorch and codeserver images; 3.5 Technology Preview embeds
  the MLflow trace UI in Gen AI Studio. "MLflow on OpenShift AI uses
  workspaces for multitenant isolation" (the CLEAR article).
- **Training Hub.** Preinstalled in the Ray CUDA runtime image from 3.5 with
  SFT, OSFT, LoRA and GRPO (developers.redhat.com, 2026-08-26). The 3.5
  release notes list "Automated prompt optimization for agentic systems … by
  using Training Hub" among the GA features, without naming GEPA and without
  a Technology Preview label. The 3.5 training images pin
  `training_hub[lora,cuda]==0.9.2` and `training_hub==0.9.2`, without
  `[gepa]` (`red-hat-data-services/distributed-workloads`); the ODH Ray image
  pins 0.8.1, older than GEPA; `opendatahub-io/architecture-context`
  `architecture/rhoai-3.5/training-hub.md` lists v0.9.2 with GEPA as an
  optional extra.
- **OpenCode.** The 3.5 Technology Preview notes list OpenCode as a
  validated coding agent with MLflow tracing (I: read through a summarized
  fetch, verify).
- **Release date.** Red Hat AI 3.5 shipped on 2026-09-09 (a secondary
  source).
- **Fetching docs.** `docs.redhat.com` answered 503 to fetch tools on
  2026-10-13; the facts above came from the press release, developer
  articles and search summaries of the release notes.

## 3. Gap map: what `openshift-eval` built itself, and why

Paths are in `openshift-eval`. "Why" is that repo's reason (its `PLAN.md`
and `docs/my-specs/01-new-design.md`).

| Our piece | Why we built it | Upstream today | Contribution (spec 01 section 7) |
|:--|:--|:--|:--|
| `stop_with_parent` in `eval/support/scripts/lib.sh:53` | A stop left the agents in flight running | `cli` and Codex runners kill their group only on a timeout; no SIGTERM handler; Claude Code kills the CLI only | C1 |
| `prices.sh` and the runners' cost code | Gateway aliases have no price | Claude Code prices as Claude; Codex gets `None` for an alias | C2 |
| `run-claude-code.sh`, `run-codex.sh` | The gateway route; a fresh folder out of reach of `input.yaml` | The gateway works by env; the agent runs next to `input.yaml` | C3 |
| `run-opencode.sh` | No OpenCode runner | Draft PR #90, stale, with security problems | C5 |
| Trace building in `flywheel/run_eval.py:760-914` | One trace per ticket for every agent | Traces from Claude Code and Harbor only | C6 |
| Our EvalHub provider, `score_evalhub.py:335-441` | The harness adapter "returns the judge means without the reasons", "drops our runners (no quota retry, no fresh folder per ticket)", its client "creates ConfigMaps on the kubeconfig's cluster even for a server on the laptop", and it "needed a wrapper image" because its pod ships no OpenCode | Means only, one case at a time, judge errors swallowed, SDK below 1.0 | C7, C11 |
| `deploy/evalhub/provider/` and `find_provider` | No API to register a provider with its resources | `K8sRuntime` has no json tags | C10 |
| `export_run_folder` | The run folder back through MLflow | `MLFLOW_WORKSPACE` injected into every job pod | C13 |
| `benchmark.py` | The grid with reuse | `/eval-anova` has no runner factor and no reuse | C8 |
| Workarounds in `adjust_eval_optimize.py` | The skill must not start its own eval | `/eval-optimize` always re-runs `/eval-run` | C9 |
| `decide()` in `controller.py:262` | Keep or revert in code, on the train score; validation never decides | The LLM decides; PR #73 proposes an LLM-enforced gate | A comment, no PR |
| `adjust_gepa.py` | One GEPA proposal per Adjust step | Training Hub runs GEPA's whole search only | None now (section 6) |
| `TrialPod` in `score_harbor.py` | Harbor trials as pods, cleaned up with the Score Job | EvalHub ADR 0001 (PR #1059) | A comment |
| `docs/my-specs/XX-sandboxing.md` | Kata and OpenShell for the agent under test | ADR 0001's P1 and P2 | Help on the ADR |

## 4. agent-eval-harness

**Versions (V).** Upstream latest release v1.56.1 (2026-10-12); `main` at
`175eed5` (2026-10-13). The reference checkout
`~/Projects/Github/redhat/agent-eval-harness` was at v1.53.3 (`7ec9078`,
2026-10-02), 40 commits behind. `openshift-eval`'s image pins
`HARNESS_REF=v1.53.0` (`deploy/build/Containerfile:34`) while its laptop
runs the editable checkout, 1.53.3: the two ran different versions.
Changes v1.53.0 → v1.56.1: Claude Code permission and credential fixes
(1.53.1–1.53.3); `eval-compare` reports wall clock and stops rounding
per-turn costs (1.53.4); ANOVA statistics (1.54–1.56); judge fencing in
`score.py` and ties in the comparison judge (1.56.1). The fencing changes
the LLM judge's prompt, so scores move after an upgrade (I).
`skills/eval-optimize/SKILL.md` did not change from v1.53.0 to `main`.

**What it does (V).** Skills: `eval-setup`, `-analyze`, `-dataset`, `-run`,
`-review`, `-mlflow`, `-optimize`, `-compare`, `-anova`, `-check`. Runners:
`claude-code`, `codex`, `cursor`, `cli`, `responses-api`
(`agent_eval/agent/__init__.py`). Judges: inline `check`, `llm`, `code`,
`builtin`, a tool-using `agent` judge, pairwise; thresholds exit 1 on a
miss. Datasets: synthetic or from traces; no train or validation split
anywhere. Harbor: a Podman environment, a Kubernetes environment tested on
OpenShift, a reward bridge. MLflow: experiments, datasets, traces,
feedback. EvalHub: its own `FrameworkAdapter`
(`agent_eval/evalhub/adapter.py`, image `quay.io/rhoai/agent-eval-hub`).
`/eval-anova` runs a `matrix:` of factors × replications with ANOVA, a
Pareto frontier and an `/eval-compare` HTML report. `/eval-train`
(reinforcement learning on weights) is only a plan
(`docs/eval-train-harbor-nemo-skyrl.md`).

**`/eval-optimize` (V).** One Claude Code session edits `SKILL.md` (or, in
prompt mode, the artifact under test such as `CLAUDE.md`); 3 iterations by
default; re-runs `/eval-run` with `--baseline`; keep or revert is the LLM's
own judgment ("if major — revert"); no held-out set, no GEPA; autonomous,
but `AskUserQuestion` is among its tools.

**Agents (V).** It calls itself agent-agnostic but is built around Claude
Code (a Claude plugin, default runner `claude-code`). OpenCode runs only
through the `cli` runner plus a wrapper (`eval/opencode-smoke`, PR #145 by
jeremyeder; cookbook `cross-runner-opencode.md`) or as Harbor's
`--agent opencode`. Codex is a native runner, also on Harbor (#183).
Constitution principle II names OpenCode as an intended runner.

**The gaps in detail (V unless marked).**

- Stop: `cli_runner.py:152-163` starts the command with
  `start_new_session=True` and calls `killpg` only on `TimeoutExpired`;
  `codex.py:210-262` kills its group only on a timeout or
  `KeyboardInterrupt`; `execute.py` installs only `atexit`, no SIGTERM
  handler; `harbor/run.py:851` is the only place that forwards SIGTERM;
  `claude_code.py:412` starts no new session and its timeout calls
  `proc.kill()` on the CLI only. Python's default SIGTERM skips every
  `except` block, so a SIGTERM orphans the `cli` and Codex children (I);
  EvalHub's SIGKILL can never be caught, so only a parent-death watchdog
  like `stop_with_parent` covers it (I).
- Gateway: `claude_code.py:802-826` forwards `ANTHROPIC_BASE_URL`,
  `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_DEFAULT_*`; `:864-872` passes every
  `runner.env` key; `codex.py:38-44` forwards `OPENAI_BASE_URL`; `:191`
  turns `runner.settings` into `-c` overrides (covers `model_provider` and
  `model_providers.*`, I). Spec 014 has one provider kind, `openrouter`
  (`providers/base.py:30-33`); a generic OpenAI-compatible kind and `cli`
  placeholders such as `{base_url}` are "PR-9 (future)"
  (`specs/014-openrouter-provider/spec.md:2488-2512, 3213`).
- Prices: Claude Code labels cost `runner:estimate` but prices tokens as
  Claude (`:948-956`); Codex looks the model up in `litellm.model_cost`, so
  a gateway alias gives `None` (`:571-592`).
- PR #90 (OpenCode runner): draft by astefanutti, opened 2026-06-01, last
  update 2026-06-10, +2751/−301 across 23 files, bundled with an OTel
  receiver, 580 commits behind `main`; CodeRabbit nits; stbenjam fixed one
  bug (#120); the author still has to fix "permission issues for
  sub-agents"; no maintainer review. Its runner copies all of `os.environ`,
  runs `--dangerously-skip-permissions`, writes `opencode.json` into the
  case workspace next to `input.yaml`, starts no process group, implements
  the old `run_skill` instead of `execute()`, and takes cost from
  `part.cost`. Neither `events.py` nor `trace_builder.py` on `main` parses
  OpenCode events. What `openshift-eval`'s runner adds: a fresh folder
  outside the git workspace, isolated config dirs, a retry on
  `token_quota_exceeded`, `_ts_ms` event stamping, gateway routing, the stop
  watchdog.
- PR #73 (optimize strategies): open, by astefanutti, 2026-05-27 to
  2026-06-07, +943/−56: `--strategy lite|skillopt|auto`, a 40:20:40
  train/selection/test split, a strict validation gate on the selection split
  (ties rejected), a rejected-edit buffer. rhuss (maintainer) asked whether
  it ever ran end to end and whether it could ship in 2 tiers; no reply
  since. Compare: `openshift-eval`'s `decide()` keeps on the train score in
  code, ties keep, validation never decides.
- EvalHub adapter: runs in-process in the job pod (`adapter.py:1-19`) with
  `runner.type` claude-code, codex or cli (Cursor refused); cases one after
  another with `workspace=case_dir`, the folder holding `input.yaml`
  (`:348-394`); returns only aggregated scores, a judge error comes back as
  `{}` (`:107-120`); per judge `mean` and `pass_rate`
  (`results_mapper.py`); no per-case results, reasons or run folder; skips
  the workspace prep (`export.py:3-6`); pins
  `eval-hub-sdk[adapter]>=0.1.7,<1.0` (`pyproject.toml:25,45`, and the
  Containerfile), which conflicts with SDK 1.0.5; 8 test files in
  `tests/evalhub/`. Its ConfigMap mode calls the Kubernetes API
  (`adapter.py:128-141`), but EvalHub job pods mount no token for the
  adapter (eval-hub `job_builders.go:258`, `job_volumes.go:268-270`), so it
  should fail (I). What it has that ours lacks: S3, filesystem and ConfigMap
  dataset delivery, per-case progress, exit code, cost and turn metrics,
  OpenRouter cost provenance, any `eval.yaml`.
- ANOVA: only `model`, `effort` and `subagent` change the runner; every
  other factor becomes an `--input-override` (`matrix-schema.md:31-39`,
  `orchestrate.py:60`); `runner.type` is fixed for the whole matrix; a factor
  named `agent` is silently shadowed by the reserved `{agent}` placeholder
  (`cli_runner.py:102-124`), so an agent factor works only through the `cli`
  runner under another name; no reuse, the run id is the date plus levels,
  `fan_out` runs every cell one at a time (`orchestrate.py:111-123,
  192-246`).
- Traces: `/eval-mlflow` builds one trace per case from
  `cases/<id>/stdout.log`, Claude Code stream-json only, plus Harbor's
  `trajectory.json` (`log_results.py:514-540`, `trace_builder.py:1`); Codex
  output is not normalized (`codex.py:289-307`). `openshift-eval`'s
  `opencode_steps`, `claude_code_steps`, `codex_steps` would fit as
  per-format adapters in front of `build_trace`.

**Read again on `upstream/main` `175eed5` (V, 2026-10-14, phase 2).** Each
fact was reproduced with a failing test on that commit; spec 01 phase 2
status names the branches.

- Stop: as above, plus `cursor_agent.py:588,986` has the codex shape;
  `claude_code.py:436,502` and `_reap` (`:904`) kill the CLI only; a
  parallel run (`execute.py:1896`) leaves through `with ThreadPoolExecutor`,
  which on Ctrl-C first runs every queued case. EvalHub's local runtime
  cancels a job with `Kill(-pid, SIGKILL)` (eval-hub `local_runtime.go:65`).
- Cost: spec 014's ledger, reconcile and catalog price OpenRouter
  generations only (`agent_eval/providers/reconcile.py:233-234`);
  `models.providers` accepts only `openrouter` (`config.py:1417-1436`); other
  provider kinds and price tables are future work (`specs/014-openrouter-provider/spec.md:2488-2495, 2525`,
  PR-9 at `:3213`); `harness:estimate` is defined (`spec.md:422`) but
  nothing writes it. Claude Code's figure is `total_cost_usd` /
  `modelUsage.costUSD` (`claude_code.py:583-588`), adjusted by
  `_billed_cost` (`:959-973`).
- Gateway: the cost label read only the process env (`claude_code.py:410,
  948-956`), but `execution.env` and `runner.settings.env` reach the CLI
  through the workspace `settings.json` env block
  (`skills/eval-run/scripts/workspace.py:747-766, 907-943`), so a gateway
  set there was labelled `runner:reported`. Claude Code 2.1.299 appends
  `/v1/messages` to `ANTHROPIC_BASE_URL` itself
  (`website/reference/environment-variables.md:32` showed `…/v1`).
  codex-cli 0.154.0 ignores `OPENAI_BASE_URL` for its built-in provider and
  sends no `OPENAI_API_KEY`; a provider declared in `runner.settings`
  (`model_provider`, `model_providers.<name>` with `env_key`) routes it
  (`website/concepts/providers.md:93-94` said otherwise). The `cli` runner
  inherits the full environment and ignores `runner.env`
  (`cli_runner.py:44-53, 228-241`).
- Workspace: locally the agent's cwd is
  `<tmp>/agent-eval/<run-id>/cases/<case-id>/` (`workspace.py:89, 238`),
  holding `input.yaml` and `answers.yaml` (`:249, 252`), project symlinks
  (`:308`) and a project-root `additionalDirectories` grant (`:968, 1026`);
  annotations are not copied there. The EvalHub adapter runs in the
  downloaded case folder itself (`adapter.py:358, 384`), next to
  `annotations.yaml`. Issues #150 and #151 have no comments; the reporter
  proposed opaque case names and a workspace root per case.
- SDK: from 0.4.4 to 1.0.6 every change the harness touches is additive
  (`MessageInfo.message_origin`, `JobSpec.primary_score`,
  `JobResults.metrics_schema`; `ModelConfig.url` may be empty, sdk#178).
  `tests/evalhub/__init__.py`, with no `tests/__init__.py`, made pytest
  import `tests/evalhub` as the package `evalhub`, so `adapter.py:55` and
  `results_mapper.py:9` fell back to `stubs.py` and the EvalHub tests never
  touched the SDK. Every eval-hub-contrib adapter pins
  `eval-hub-sdk[adapter]~=1.0.5` (for example
  `adapters/inspect/requirements.txt:5`).
- Not yet in the catalogue: `--runner evalhub` cannot submit a job on
  either SDK — `runner.py:164-205` calls the async `EvalHubClient`
  (`evalhub/client/evalhub.py:196`) synchronously, and
  `ModelConfig(name=model)` sends an empty URL, which the server refuses as
  `model_url_required` (eval-hub `handlers/evaluations.go:319-324`).
  `execute.py` rounds the case-mode run total to 2 decimals. The Claude Code
  allowlist (`claude_code.py:802-826`) lacks `ANTHROPIC_DEFAULT_FABLE_MODEL`,
  which the OpenRouter plan sets (`providers/env.py:30-33`). The codex
  estimate prices an alias that matches a LiteLLM model name at that model's
  list price (`codex.py:590-592`).

**Read again on `upstream/main` `9bc9a8d` (V unless marked, 2026-10-14,
phase 2, C6 to C9).** v1.56.2; its two new commits touch the judge's
`tool_choice` (`ed062fe`) and the release. Each fact was reproduced with a
failing test on that commit (C7: on C4, `1bceb38`) or read in the code
named; spec 01 phase 2 status names the branches.

- Traces: `log_results.py:514-540` builds every trace with `build_trace`
  (`trace_builder.py:180-212`, Claude Code stream-json). A Codex log gives
  the root span only; an OpenCode log raises `TypeError` at
  `trace_builder.py:591` (millisecond integers reach the ISO parser), which
  stops `log_results.py:530` after the MLflow run is made. The flush at
  `log_results.py:592-593` imports `AsyncExportQueue`, a name no MLflow
  the package allows has (3.5.0 already calls it `AsyncTraceExportQueue`),
  so the flush never ran and links and feedback race the trace writer: on
  sqlite with MLflow 3.17.1 it failed 3 of 3 times, where 3.5.0 still
  linked (C30). A
  case-mode trace has no model on its spans (`execute.py:1432`,
  `log_results.py:527`). Harbor traces lose a tool's output when the
  stream-json result has no timestamp (`trace_builder.py:285`). The OpenCode
  cookbook wrapper writes `input + cache_read` and `cache_write`
  (`eval/opencode-smoke/scripts/run-opencode.sh:85,88`), where the harness
  reads `input` as uncached and `cache_create`. `{config_dir}`
  (`cli_runner.py:34`) is missing from the placeholder tables.
- EvalHub pod: `deploy/evalhub/entrypoint.py:35` built
  `DefaultCallbacks(job_id, benchmark_id)` without `sidecar_url` or
  `provider_id`, so no event reached the server. The server keeps the
  first terminal event: a later status gets 409 `job_can_not_be_updated`
  (eval-hub `540676f`, `internal/eval_hub/storage/sql/evaluations_status.go:27`,
  `messages/messages.go:61-65`), and `adapter.py:428` sent a metric-less
  `COMPLETED` before `report_results`. The SDK's `report_results` posts the
  `completed` event with the metrics itself. **I:** no pod watcher in
  eval-hub `runtimes/k8s` or `runtimes/local`, so a crashed pod leaves its
  job `running`. `adapter.py:116` calls `score_cases` without `run_id`, so
  the pod's judges never see stdout, exit code or metrics (Harbor passes
  one, `agent_eval/harbor/reward.py:222-226`). `results_mapper.py:108` puts
  `pass_rate` in `EvaluationResult.metadata`, which the SDK never sends.
  `runner.py:125,277`: `--timeout` defaults to `None`, so the client polls
  forever. The SDK logs an error body at debug level only
  (`evalhub/client/base.py:42`). **I:** `url: "vertex-ai"` fails the
  server's `omitempty,url` rule (`pkg/api/evaluations.go:98`).
- ANOVA: a cell missing a `thresholds:` entry exits 1 in `score.py:4188-4189`
  after `summary.yaml` is written, and `orchestrate.py:155-160` treats it as
  failed (reproduced in a scratch project). Input overrides are merged in
  `_execute_per_case` only (`execute.py:1815-1822`), so batch mode ignores
  every non-model factor, and only `input.yaml` gets them, not `input.yml`
  or `input.json` (`workspace.py:567-573`). `_safe_id_segment`
  (`matrix.py:179-182`) maps `a/b` and `a_b` to one run id.
  `analyze.py:478-497` pools runs of older recipes as replications.
- Optimize: the open optimize PR is #73 (astefanutti, based on 1.10.0),
  not one by sanjayb-rh, who has no PR in this repo; it rewrites most of
  `skills/eval-optimize/SKILL.md`. The skill lists judge types without
  `agent` (`SKILL.md:82`), though `score.py:2658` emits it.
- CI lint: `.github/workflows/lint.yml:21-24` runs the skillsaw action
  pinned at `d252498`, which installs skillsaw 0.10.0, with `strict: 'true'`
  (warnings fail). It warns when `AGENTS.md` (a link to `CLAUDE.md`)
  passes 6,000 estimated tokens; `9bc9a8d` has 22,977 bytes, so about
  1,160 bytes are left for every PR together. `.skillsaw.yaml:15` names a
  rule that skillsaw 0.21.0 removed, so a local `uvx skillsaw` warns where
  CI does not.

**Found while C30 to C34 were built (V unless marked, 2026-10-14, not
fixed).** Each read in the code named by the subagent of that branch, on
`9bc9a8d` unless marked; spec 01 phase 2 status has the branches.

- MLflow (C30):
  - `trace_builder.py:56,648` set span status `STATUS_CODE_OK`, which
    MLflow 3.5.0 rejects, so on 3.5.0 no built trace logs: the package's
    `mlflow[genai]>=3.5` floor is too low for traces.
  - `log_results.py:513-525, 540-541` reuse any unlinked trace whose
    `eval_run_id` is a case id. Case ids repeat across runs, so a trace
    the race left unlinked gets the next run's link and feedback.
  - `log_results.py:513` reads at most 500 traces, without paging, and
    `:515`'s `experiment_ids=` is a FutureWarning on MLflow 3.17.
  - Multi-step cases: `execute.py:1692-1694` keeps only the last step's
    stdout and `:1711` sums `per_model_usage` over every step, so all the
    cost lands on the last step's spans; the case result has no `model`.
  - `agent_eval/ci_context.py:217-226` warns `download_artifacts failed`
    on every log-results run: the run finds itself before its snapshot is
    uploaded.
- EvalHub pod (C31):
  - `score.py:224-226` reads annotations only from the dataset beside
    `eval.yaml`. With S3 or ConfigMap delivery the pod's cases are under
    `<tmp>/cases`, so its judges see none: a judge on `annotations['tag']`
    scored 0.0 (reproduced).
  - `adapter.py:375-376` uses `execution.timeout or 600` and
    `max_budget_usd or 5.0`. The docs say 3600 s and 100 USD, and that 0
    is honoured (`website/concepts/execution-model.md:137,139`). C7 moves
    the lines unchanged.
  - Pod case folders are not git repositories, so `_modified` and
    `modified_files` (`score.py:293-313`) never exist in the pod.
  - Harbor has the same gap as C31's first bug: its verifier writes
    `stdout.log` but no `run_result.json` (`harbor/reward.py:225-226`,
    `templates/test.sh.tmpl:11-16`), so judges on the exit code or metrics
    get their defaults.
  - C7 already fixes two more: the async client (`runner.py:131,164`) and
    the `score.py` path built from an unresolved `__file__` (`adapter.py:98`).
- Cost (C32):
  - `execute.py:1101` rounds a multi-step case's cost to 4 decimals and
    counts a step without a cost as 0; `:2016` rounds the plan run's
    estimate to 4 decimals.
  - Only reconcile writes `cost_usd_estimate`, under a plan: the per-case
    result (`execute.py:1241-1258, 1432-1450`) and batch mode
    (`:2130-2152`) drop it. So the estimate C2 keeps beside a configured
    price is lost from `run_result.json` without a plan.
  - Spec 014 (`spec.md:422`) names codex's price-table estimate
    `harness:estimate`; `codex.py:245,281` writes no label. With C2 and
    C32 merged, only a codex run on OpenAI's own API without
    `runner.pricing` is still unlabelled, and `/eval-compare` reads it as
    `runner:reported`.
  - `agent_eval/prompt_backends.py:23` knows `opus`, `sonnet` and `haiku`
    as Claude aliases, not `fable`: a judge model `fable` goes to the
    OpenAI SDK.
  - The cli runner contract (`docs/opaque-cli-runner-contract.md:54,72`,
    `website/concepts/runners.md:354`) never says `input` is uncached or
    names `cache_read` and `cache_create`, which is how the wrapper bug
    happened.
  - Under a plan `ANTHROPIC_DEFAULT_FABLE_MODEL` already reached the CLI,
    through the settings overlay (`claude_code.py:715`): C32's fix is for
    runs without a plan.
  - **I:** the OpenCode wrapper ignores `tokens.reasoning`
    (`run-opencode.sh:73-81`); Harbor's own Codex agent prices with
    litellm the same way.
- Stopping (C33, on C1 `ec71b53`):
  - `agent_eval/hooks.py:133-145` starts hooks with
    `start_new_session=True` and kills them only on timeout, so a stopped
    run leaves a hook's process group running.
  - `skills/eval-dataset/scripts/generate_synthetic.py:329,537` starts an
    agent and installs no stop handler; nor does the Harbor verifier
    (`harbor/reward.py:226,493`).
  - **I:** on Kubernetes the provider is the container's PID 1 (eval-hub
    `job_builders.go:189`), which gets no signal it has no handler for
    (pid_namespaces(7)), so before C33 a pod's SIGTERM was dropped. Not
    checked on a cluster.
- ANOVA (C34, on `fix/anova-cells` `7931dca`):
  - Case mode reads placeholders from `input.yaml` only
    (`execute.py:1161, 1308, 1486`, `CASE_INPUT` at `:1344, 1525`,
    `cli_runner.py:117`): an `input.yml` or `input.json` case passes
    `{name}` and `{{ input.name }}` through as written. The override does
    land in its file.
  - `orchestrate.py:89-97` counts only cases with `input.yaml`, so
    `/eval-anova` leaves out `.yml` and `.json` cases unless `--cases`
    names them.
  - Run ids still collide across factors: `-` is the separator and allowed
    in a level, so `{x: a-y-b, y: c}` and `{x: a, y: b-y-c}` share one
    (`orchestrate.py:111-123`), and so do the levels `1` and `"1"`.
  - `workspace.py:89-96` deletes `<tmp>/agent-eval/<run-id>` when it
    exists, and a run id carries no eval name: two evals with the same
    levels on the same day overwrite each other's workspace.
  - Case mode drops an override in silence when the input file is missing,
    a symlink or not a mapping (`execute.py:1795-1813`); a test pins the
    missing case (`tests/test_anova_orchestrator.py:212-214`).
  - C8's reuse recipe holds `agent_eval.__version__`, not the code. On
    `flywheel-integration`, still 1.56.2, a cell that ran before C34 with
    an ignored factor counts as done: re-run such a matrix with `--force`.

**Roadmap (V for the items).** Open: #73 optimize controls, #90 OpenCode
runner, #109 an `agent-eval run` CLI, #200 measurement validity, #4
sandboxed execution, #178 A/B testing with and without a skill, #150 and
#151 workspace leaks. Recent work: ANOVA statistics, judge calibration and
fencing, OpenRouter (spec 014), docs. Not in the tracker: GEPA, an agent ×
model benchmark, a UI. Direction (I): statistical rigour and judge quality.

**Status and people (V).** Upstream only in `opendatahub-io`, Apache-2.0,
created 2026-04-02, 45 stars, shipped as a Claude plugin through
`opendatahub-io/skills-registry`; no Red Hat product page names it.
Maintainers are Red Hat staff: Antonin Stefanutti (astefanutti, 655
commits, merges almost everything), then Roland Huss (rhuss) and Stephen
Benjamin (stbenjam). Jeremy Eder (Distinguished Engineer, Red Hat AI) wrote
EvalHub ADR 0005, tagged release "3.4". Outside contributors are welcome
(PR #213, the Cursor runner, +3341 lines across 45 files with docs under
`website/`). On PyPI, `agent-eval-harness` 0.1.0 is an unrelated project.

**What the harness models for any use case (V, `upstream/main` `175eed5`,
2026-10-14, for decision 10).** The `reward` block, the keys of
`summary.yaml`, the S3 layout and the workspace's git snapshot checked by
hand; the rest read by a subagent.

- Config: dataclasses and hand parsing, `EvalConfig.from_yaml`
  (`agent_eval/config.py:1938-2620`), no JSON Schema. Unknown top-level
  keys are ignored in silence; `skills/eval-analyze/scripts/validate_eval.py:437`
  warns on unknown judge fields only.
- Dataset: a folder of case folders, nothing else (no JSONL, Parquet or
  Hugging Face loader). `input.yaml` is what the agent sees.
  `annotations.yaml` is for the judges; a value that names a file of the
  case is loaded as `annotation_<key>_content`
  (`skills/eval-run/scripts/score.py:220-252`). Other case files reach the
  agent only through `dataset.workspace.files`, and a `{dest, source}`
  entry copies one shared file into every case (`config.py:476-491`,
  `agent_eval/workspace_provisioning.py:59-75`). `dataset.schema` is prose,
  never parsed. No splits: `--cases` takes exact ids
  (`skills/eval-run/scripts/workspace.py:46, 69-71`). For EvalHub the same
  layout is read from S3 as `{prefix}/{case_id}/{file}`
  (`agent_eval/evalhub/s3_dataset.py:16-25`). `/eval-mlflow`'s
  `sync_dataset.py` writes the cases into an MLflow evaluation dataset,
  through a field mapping an LLM derives from `dataset.schema`.
- Judges: five kinds, picked by the field that is set: `builtin`, `check`
  (inline Python), `agent`, an LLM judge (`prompt`, `prompt_file`,
  `llm_rubric`) and `module` + `function`; plus the reserved `pairwise`
  (`score.py:886-925`). Fields include `if`, `score_range`, `samples`,
  `context`, `model` and `arguments` (`config.py:1590-1652`); none holds a
  weight, a threshold or a gate.
- Combined score: `reward:` takes one judge, `weighted` with `weights`, or
  a formula; `gate: true` zeroes it when a boolean judge fails
  (`config.py:1655-1699`, `agent_eval/harbor/reward.py:287-352`). Harbor's
  `reward.json`, the report and `/eval-anova` use it. `summary.yaml` gets
  only `judges`, `per_case` and `judge_usage` (`score.py:4066-4072`).
- Gates: `thresholds` per judge (`min_pass_rate`, `min_mean`,
  `min_win_rate`, `max_error_rate`) make `score.py` exit 1 on a miss
  (`score.py:3841-3910`); none can target the combined score.
- Workspace: each case's workspace is a git repository with an `initial`
  commit (`workspace.py:240-290`), so the agent's edits are collected as
  `_modified/` (`collect.py:222-230, 390`). The project's `CLAUDE.md` and
  skills are symlinked in (`workspace.py:227`): the brain is implicit, not
  declared. No key for a knowledge base, a repository checkout, a container
  image or MCP servers per eval or per case; they go through
  `runner.settings`, a `cli` command, hooks, shared files or Harbor's
  `--image`.
- PR #73's branch `feat/skillopt-improvements` (not merged) adds
  `--split 40:20:40` (`scripts/split_dataset.py`, seed 42), written to
  `tmp/splits.yaml`. Its gate keeps an edit only when the selection split's
  score strictly improves, and does not define that score.
- The examples in the repo are coding and docs tasks only
  (`eval/anova-example/`, `eval/opencode-smoke/`,
  `tests/fixtures/evalhub-smoke/`).
- Where the dataset is read, for C19 (V, the fork's `flywheel-integration`
  `e0e21d0`, 2026-10-14 evening): no shared loader, and no single place
  where `dataset.path` is resolved. Thirteen non-test files name it:
  `agent_eval/config.py`, `agent_eval/evalhub/adapter.py`, `export.py`,
  `agent_eval/harbor/run.py`, `tasks.py`, `agent_eval/reorganize.py`,
  `skills/eval-analyze/scripts/validate_eval.py`,
  `skills/eval-anova/scripts/orchestrate.py`,
  `skills/eval-mlflow/scripts/sync_dataset.py`, and in
  `skills/eval-run/scripts/` `execute.py`, `report.py`, `score.py` and
  `workspace.py`. Most call `config.resolve_path(config.dataset.path)`
  (`workspace.py:62`); `execute.py:1342, 1526` read it raw, and
  `adapter.py:644` joins it to the config's folder. They run as separate
  processes. `workspace.py` deletes `<tmp>/agent-eval/<run-id>` when it
  exists, then makes it again. `collect.py` and `log_results.py` walk the
  run's `cases/`, not the dataset. Other case files reach the agent only
  through `dataset.workspace.files`. `agent_eval/harbor/tasks.py` is the
  one converter there: it writes case folders out as Harbor task packages.
  The harness's `CLAUDE.md` names its first design principle
  "Schema-driven — dataset and output structures described in natural
  language in eval.yaml; agents and judges interpret them, scripts just
  move files" (`:281`), with "no hardcoded field names" (`:234`). Features
  arrive spec-driven, as `specs/NNN-<name>/` (the newest is
  `specs/014-openrouter-provider`).

## 5. EvalHub, eval-hub-contrib, the TrustyAI operator

**Versions (V).** The reference checkout
`~/Projects/Github/eval-hub/eval-hub` was `540676f` (2026-10-13 07:49 UTC),
`v1.0.2-83`, `VERSION` 1.0.3 not released, equal to upstream `main`.
Release v1.0.2 (2026-09-18). PyPI: `eval-hub-server` 1.0.2,
`eval-hub-sdk` 1.0.6 (2026-10-13). Read again 2026-10-14 evening: still no
newer release (`v1.0.2` is `db34dc1`); upstream `main` `3f7b173` is 93
commits after it. The cluster's server, from ODH 3.6.0-ea.2, is
`quay.io/opendatahub/odh-eval-hub@sha256:ac217d00…`, built 2026-09-19 from
`opendatahub-io/eval-hub` `stable` `99ff1ff` and labelled 1.0.3 (`oc image
info` labels): its merge base with upstream `main` is `f440792`, `v1.0.2`
plus 4 commits, 89 behind `main`. This repo pins no server version;
`deploy/platform/evalhub/` takes ODH's. The upstream TrustyAI operator has no
release since v1.38.0 (2025-06) and has EvalHub only on `main`; the RHOAI
fork `red-hat-data-services/trustyai-service-operator` has `api/evalhub` on
branches `rhoai-3.4`, `3.5`, `3.6`, not `rhoai-3.3`.

**What it does (V).** API (`docs/openapi.json`): jobs (create, list, get,
cancel by DELETE, logs, per-benchmark logs, events), providers (CRUD),
collections (CRUD, clones), post-processing (confidence intervals, new
2026-10-07), `info`, `health`. A job evaluates a `ModelRef` (url, name,
secret_ref) or `pre_recorded_data` without a model URL. Per benchmark:
weight, `primary_score`, `pass_criteria` giving an overall `pass`; hardware
profile, Kueue queue, CPU, memory, GPU. Test data from S3, PVC, Git or HF;
results as a signed OCI EvalCard. 16 built-in providers
(`config/providers/`): lm-eval (~167 benchmarks), inspect (~90), lighteval,
ragas, garak, garak-kfp, guidellm, ibm-clear, deepeval, mteb,
nemo-guardrails, ruler, tooleval, ifbench, followbench, databench; 19
collections. Runtimes `k8s` (Job pods, adapter plus sidecar) and `local`
(subprocess). MLflow: one run per evaluation request, the experiment
created automatically (`MLFLOW.md`). Multi-tenancy: kube-rbac-proxy sets
`X-Tenant` (the namespace) and `X-User`; providers and collections can be
tenant-scoped. An MCP server (`discover_providers` filters by target
`agent`; `submit_evaluation`; a `compare_runs` prompt) and OTEL. No
leaderboard resource.

**Agents (V).** The thing under test is always a model endpoint. Agent
evaluation is indirect: CLEAR judges pre-recorded LangGraph and MLflow
traces (`ibm-clear.yaml`, `evaluation_targets: [agent]`); Inspect runs its
own agent loops around a model (GAIA, AgentDojo, TheAgentCompany, Cybench,
CyberGym); Dish (`inspect.yaml:1469`, `task_args: {"dish_scaffold":
"claude-code"}`, a research preview) is the only place an agent CLI is
named, still around the model under test; SWE-bench grades existing patches.
The ATIF adapter (`eval-hub-contrib` PR #152, by ruivieira, opened
2026-09-12, merged 2026-10-13, approved by julpayne, Jira RHAISTRAT-1843)
scores Harbor-format ATIF trajectories with an LLM judge and has a
`training_threshold` that outputs training-eligible sets; the SDK has the
ATIF models since 2026-09-08 (sdk#187). `agent-eval-harness` has zero code
hits across the four eval-hub repos; issues #546–#550 were moved there from
the harness. Issue #936 (closed) scoped the GA collections to "bare-model …
No agent harness"; issue #937 suggests a `trajectory_ref` in EvalCards.

**Where a provider lives (V).** Three repos, in order: the adapter and its
image in `eval-hub-contrib`; the provider YAML in eval-hub
`config/providers/`; a ConfigMap in the operator's
`config/configmaps/evalhub` (eval-hub `README.md:387-401`; a nightly sync
check enforces it). ToolEval shows the chain: eval-hub #1076 adds only the
YAML, operator #992 (our old pin `359bc8e`). A provider needs a
`provider.yaml` (id, name, `runtime.k8s` image, entrypoint and resources,
optional `runtime.local`, benchmarks with metrics and `primary_score`,
parameters), a `FrameworkAdapter.run_benchmark_job`, a Containerfile and a
public image (`validate-provider-images.yml` checks every new YAML's image
with crane). `type: community` means a contrib image
`quay.io/evalhub/community-*`; built-in means the CRD defaults garak,
garak-kfp, lm-evaluation-harness (operator
`api/evalhub/v1/evalhub_types.go:209-213`); the server ignores `type` (no
such field in `ProviderConfig`, `pkg/api/providers.go:58-66`); contrib's
CONTRIBUTING says `builtin` for community adapters, which contradicts
eval-hub. Review by `@eval-hub/maintainers` in both repos. The harness's
image `quay.io/rhoai/agent-eval-hub` returns 401, so it would fail the image
check. The contrib pattern is "invokes the framework via subprocess CLI"
(contrib `AGENTS.md`), so the home for C11 is a contrib adapter
`adapters/agent-eval-harness` running the harness's eval-run scripts as a
subprocess (I), agreed in an issue on the harness first.

**`openshift-eval`'s provider vs the harness adapter (V).** Only ours: it
runs the five eval-run scripts (parallelism, workspace prep, our runners,
`score_evalhub.py:352-357`); the whole run folder (reasons, `events.jsonl`)
comes back through MLflow (`:394-405`, `:321-332`); the brain travels in the
job parameters (`:218-225`); it exits on SIGTERM and the client cancels the
job on a stop or a timeout (`:338-405`, `:429`). The survivor should be our
execution model moved upstream plus the harness's extras.

**SDK 1.0.6 (V).** Adds `MlflowFileArtifact` (streamed upload, sdk#194),
OCI signing (#195), drops `oci_subject` (#196), CVE fixes; `callbacks.py`
differs from 1.0.5 only in the artifact type. On the laptop it can replace
`export_run_folder` with `callbacks.mlflow.save(..., artifacts=[...])` and
`results.mlflow_run_id`; it needs `experiment` on the job (`save` does
nothing without it, `callbacks.py:93`) and `MLFLOW_TRACKING_URI` in the
server's environment; one artifact per file. On a cluster it is blocked by
the injected `MLFLOW_WORKSPACE` (`job_config.go:149-157`): the SDK then
always sends `X-MLFLOW-WORKSPACE` (`mlflow.py:254-257`), which MLflow
3.16.1 refuses; the server probes workspace support only for itself
(`workspace_support.go:147-165`). ODH's MLflow with workspaces may remove
the problem (I).

**Small EvalHub defects (V).** `K8sRuntime` (`providers.go:118-133` at
`540676f`) has no json tags on seven fields, so the API drops the four
resource fields the OpenAPI schema names (`cpu_request` and others). Go's
decoder matches `image`, `entrypoint` and `env` without a tag, but the
API then returns them as `Image`, `Entrypoint` and `Env`, while
`docs/openapi.json` names them in lower case (I, from `encoding/json`'s
rules, not run); `gpu` and `image_pull_policy` have tags. The local runtime ignores a provider that
exits without a report (`local_runtime.go:414`, `_ = cmd.Wait()`). The
operator's failure watcher deliberately ignores an adapter's non-zero exit
(`controllers/evalhub/evaluation_job_failure_reconciler.go:113-114`,
`terminatedAdapterNeedsOperatorReport` at `:950`). Operator #985 (`639411f`) adds the NetworkPolicy
RBAC, but its policy forbids `delete`, while `openshift-eval` saw OpenShift
needing `delete` for the ownerReference update that `main` still makes
(`k8s_runtime.go:396-403`; its runs `eval-4zllw`, `eval-jqhra`).

**The TrustyAI operator restarts without KServe (V, `cluster-nm8mw`,
2026-10-14 17:22 UTC; trustyai-service-operator `upstream/main`
`4fa5c74`).** On the cluster, `trustyai-service-operator-controller-manager`
in `opendatahub` had restarted 180 times since it started on 2026-10-13
19:26 UTC. Each run ends with "failed to wait for trustyaiservice caches to
sync kind source: *v1beta1.InferenceService": `serving.kserve.io/v1beta1`
is not served, because `default-dsc` has KServe `Removed`. The
TrustyAIService controller watches `InferenceService` with no check
(`controllers/tas/trustyaiservice_controller.go:317`), and the manager
exits with it, so the EvalHub controller in the same manager runs only
between restarts. The EvalHub controller checks Kueue through discovery
first (`controllers/evalhub/kueue_workloads_discovery.go:26`). So `default-dsc`
flips between Ready and `Not Ready` ("Some modules are not ready:
trustyai"); the `evalhub` pod itself stayed Running.

**What C29 can reuse, and how ODH runs our images (V, 2026-10-14, 21:55
CEST).** The operator had restarted 204 times by then. Upstream PR #899
(merged 2026-09-03, `10710d0`, "self-heal on missing KServe CRD") added
`isInferenceServiceCRDPresent` (`controllers/tas/inference_services.go:32`,
used at `:239` and `:402`), but left the watch at
`trustyaiservice_controller.go:317` without a check. The image chain on the
cluster:

1. `opendatahub-operator-controller-manager` in `openshift-operators`, from
   the ODH CSV, carries `RELATED_IMAGE_ODH_TRUSTYAI_SERVICE_OPERATOR_IMAGE`
   and `RELATED_IMAGE_ODH_EVAL_HUB_IMAGE` in its env.
2. The `Platform` `default` (`config.opendatahub.io/v1alpha1`) owns
   `trustyai-operator-module-controller-manager` in `opendatahub`; its env
   has the same keys: the operator at
   `quay.io/opendatahub/trustyai-service-operator@sha256:b74d2d6e…`,
   EvalHub at `quay.io/opendatahub/odh-eval-hub@sha256:ac217d00…`.
3. That module controller runs `trustyai-service-operator-controller-manager`,
   which runs the `evalhub` server.

So a patch on a lower level is overwritten by its owner, and an override
belongs on the ODH operator: through the Subscription's `spec.config.env`
(I, spec 01 section 12; not tried).

**Issue rules (V, `upstream/main`, read 2026-10-14 evening).** eval-hub:
"Before starting work, create an issue to discuss" bug reports, feature
requests, architectural changes and questions (`CONTRIBUTING.md:112-121`).
An architectural change (a new executor or framework, an API endpoint
added or changed, a new dependency) needs the labels `kind/architecture`
and `status/accepted` before implementation, and its PR is accepted only
with them (`:123-140`). trustyai-service-operator: "All `fix` and `feat`
commits require an associated issue. Please add link to your Github
issue." (`CONTRIBUTING.md:102`). Its `make test` runs
`manifests generate fmt vet envtest` (`Makefile:136`), and envtest
downloads its binaries first (`:270-278`). Spec 02 decision 15 times these
issues.

**Use cases, data and gates in EvalHub (V, `upstream/main` `540676f`,
2026-10-14, for decision 10).** `TestDataRef`, the collection entry, the
0.5 default and the dashboard's BFF type checked by hand; the rest read by
a subagent.

- No benchmark resource and no dataset resource. A benchmark lives only
  inside a provider (`pkg/api/providers.go:58-66`), with `metrics`,
  `primary_score` and `pass_criteria`. A tenant registers its own provider,
  benchmarks included, through the API ("Bring Your Own Provider",
  `internal/eval_hub/handlers/providers.go:54-109`); the server keeps no
  schema of a provider's `parameters`.
- A collection entry (`pkg/api/collections.go:4-13`) carries
  `provider_id`, `weight`, `primary_score`, `pass_criteria`, `parameters`
  and `test_data_ref`; the collection has its own `pass_criteria`.
  Collections can be created, read, changed, deleted and cloned per tenant
  (`handlers/collections.go:367-427`); the system ones are read-only.
- `TestDataRef` (`pkg/api/evaluations.go:201-214`): exactly one of `s3`,
  `pvc`, `git` (`url`, `ref`, `sub_path`, `secret_ref`) or `hf`; a `type`,
  `data_set` or `pre_recorded_data`; and `resolved_sha`, which EvalHub
  fills after its init container resolved the ref. S3, git and HF land in
  an `emptyDir` at `/test_data`; a PVC of the job's namespace is mounted
  read-only (`internal/eval_hub/runtimes/k8s/job_volumes.go:175-202`). The
  adapter sees `/test_data` and `TEST_DATA_*`, not the ref.
- The gate: a job's score is the weighted mean of its benchmarks' primary
  scores. It passes at the job's threshold, else the collection's, else a
  hard-coded 0.5 (`internal/eval_hub/storage/sql/evaluations_results.go:37-103`).
  Each benchmark also gets its own `test.pass`.
- Hardware per benchmark entry: an ODH `HardwareProfile`, or CPU, memory,
  GPU and a queue (`BenchmarkHardwareConfig`, `pkg/api/evaluations.go:230`).
- No per-case results in the API; reasons stay in the adapter's artifacts
  and in MLflow. No agent under test: `ModelRef` is a URL, a name, auth and
  parameters (`evaluations.go:97-103`). No MLflow evaluation dataset in
  EvalHub or in SDK 1.0.6.
- The dashboard's `packages/eval-hub` creates, changes and copies
  collections with weights, thresholds, the primary metric and parameters,
  but no provider or benchmark. Its "agent" source is a name and an
  endpoint URL. Its BFF's `TestDataRef` holds S3 only, with no `type`
  (`packages/eval-hub/bff/internal/integrations/evalhub/evalhub_client.go:204-212`),
  and the form sends no `bucket`
  (`packages/eval-hub/frontend/src/app/utils/buildEvaluationRequest.ts:64-78`),
  which the server requires: that path fails validation (I, not run).

**ADR 0001, PR #1059 (V).** "Sandboxed evaluation runtime for agentic
frameworks", by Julian Payne (julpayne), draft since 2026-10-01, last update
2026-10-02, no reviews (CodeRabbit skipped it: it needs the
`ready-for-review` label), Jira RHAISTRAT-2289. P0: an ephemeral namespace
per evaluation, an `eval-sandbox-broker` sidecar, an operator
`SandboxedEvaluation` resource on standard `runc`; P1: OpenShell
(per-binary, per-process policy); P2: Kata (`RuntimeClassName`, needs bare
metal or nested virtualization; a provider may require
`min_isolation_tier: kata`). It names SWE-Bench, AgentDojo, ATIF/Harbor and
Terminal-Bench as the motivation, and rejects cleanup in the tenant
namespace for lack of deterministic cleanup (lines 199-201). No
open-questions section; open items elsewhere: the egress profile (eval-hub
#1069, operator #984 "Egress mode is unresolved"), the broker's caps, the
resource handshake, the image allowlist. Data `openshift-eval` can give:
deterministic cleanup with an ownerReference to the Score Job's pod
(`flywheel-ftrlq` left no pod; `eval-dgpdt`'s trial pods gone 36 s after
the suspend); Harbor 0.24 on Podman left 3 of 4 trial containers stopped
but not removed after a SIGINT; the verbs a broker needs for Harbor (pods
create/get/delete, pods/exec create/get, restricted-v2, no token); the ADR
speaks only of PSA, but on OpenShift the SCC decides, and Terminal-Bench
tasks need root, a RunAsAny SCC and the internet (I, not run).

## 6. Training Hub

Read at `main` `608f8a0` (V unless marked).

- **API.** `gepa(seed_candidate: dict[str,str], task_lm: str, …)` optimizes
  several named text components (`src/training_hub/algorithms/gepa.py:618-667`);
  data from `trainset`/`valset` or JSONL `{input, answer,
  additional_context}` (`:106-128`); the `evaluator`
  `(data, response) -> (score, feedback, objective_scores)` only feeds GEPA's
  DefaultAdapter, which uses only the first component as the system prompt
  of one chat call (gepa 0.1.4 `default_adapter.py:117`); `reflection_lm`
  defaults to `task_lm` (`:73-77`); budget `max_metric_calls`; `api_base`
  sets `OPENAI_API_BASE` for litellm and a dummy key (`:62-71`); returns a
  `GEPAResult` and writes `best_candidate.json`, `result.json`
  (`:131-147`). The `mlflow` backend calls `mlflow.genai.optimize_prompts`
  with `prompt_uris`, `predict_fn`, `scorers` and ignores `adapter`
  (`:241-264`). Pin `gepa>=0.1.1`.
- **Fit: poor for our Adjust step.** It runs GEPA's whole search, which is
  our loop; it has no "propose one candidate" call, which is all
  `adjust_gepa.py` uses (`StatelessReflectionLM.reflect`). A multi-file
  brain needs a custom `adapter`, and that route is broken: `task_lm` is
  required (`gepa.py:385`, `:618`, `get_required_params` `:561-566`) while
  gepa asserts `task_lm is None` with an adapter (gepa 0.1.4
  `api.py:210-213`); in Python only `task_lm=None` works, the CLI never
  (`cli.py:281` `required: True` next to `--adapter`, `cli.py:300`). Each
  metric call is one agent run, and GEPA first scores the seed on the whole
  `valset` (I). Components are fixed by the seed, so no new skills.
- **Footprint.** The base install pulls torch, instructlab-training,
  mini-trainer, transformers, numba, timm, pytest (`pyproject.toml:13-51`);
  `training-hub[gepa]==0.11.0` resolves to 173 packages for linux x86_64
  with torch 2.14.1, triton and 14 `nvidia-*` CUDA 13 wheels; `import
  training_hub` loads instructlab, datasets, transformers and torch
  (`__init__.py:36-50`), so `--no-deps` fails too. PyPI name
  `training-hub`, latest 0.11.0 (2026-10-12); the gepa extra since 0.9.0
  (2026-06-25).
- **Activity and rules.** `gepa.py` has one commit (`545a50c9`, PR #77,
  2026-06-05); docs PR #144 (2026-08-27); `thub gepa` in #103
  (2026-09-24); no open issue or PR on gepa. Maintainers Mustafa Eyceoz
  (Maxusmusti, 74 commits) and Oleg Silkin (RobotSail, 49). No CONTRIBUTING,
  no DCO; `docs/DEVELOPING.md` asks for Google Python style, tests and docs;
  CI is a GPU smoke test for SFT and OSFT only; a fork's PR needs the
  `ok-to-test` label; no GEPA backend test.
- **If GEPA should ever be the whole engine**, the two smallest upstream
  fixes: make `task_lm` optional with an `adapter` (in `gepa()`, `train()`,
  `get_required_params` and the CLI, with a test); load modules lazily (PEP
  562 `__getattr__`) in `src/training_hub/__init__.py`.

## 7. The OpenShift AI dashboard and Open Data Hub

**Bottom line (V).** The dashboard 3.x assumes the whole ODH stack: the
dashboard-operator, the ODH Gateway with kube-auth-proxy, a
`DataScienceCluster` and an `Auth` resource.

**Under the ODH operator (V).** In ODH 3.6.0-ea.2,
`spec.components.dashboard.managementState: Managed` (DSC v2) makes ODH
render the dashboard-operator's Helm chart (`dashboard-operator/charts/dashboard`
at `37dc648`, operator `manifests-config.yaml`) and create the `Dashboard`
resource `default-dashboard` (`components.platform.opendatahub.io/v1alpha1`).
The dashboard-operator renders its baked-in manifests
(`/opt/manifests/dashboard/odh`): one pod with three containers (the
dashboard on 127.0.0.1:8080, kube-rbac-proxy on :8443, core-bff on :8943),
an HTTPRoute to the Gateway `data-science-gateway`, one Deployment per
module, the `federation-config` ConfigMap. `devFlags.manifests`
(`{uri, contextDir, sourcePath}` in the 2.35.0 DSC CRD) is gone from the
3.3.0, 3.5.0 and 3.6.0-ea.2 CRDs. Images: the ODH operator copies
`RELATED_IMAGE_*` env into the dashboard-operator (`inject_env.go`); the
keys it passes are a fixed list (`internal/controller/modules/dashboard/support.go`
on `main`): `RELATED_IMAGE_ODH_DASHBOARD_IMAGE`,
`…_MOD_ARCH_MODEL_REGISTRY_IMAGE`, `…_GEN_AI_IMAGE`, `…_MLFLOW_IMAGE`,
`…_MAAS_IMAGE`, `…_EVAL_HUB_IMAGE`, `…_AUTOML_IMAGE`, `…_AUTORAG_IMAGE`,
`…_DATA_CONNECT_HUB_IMAGE`, `…_NOTEBOOKS_IMAGE`, `…_AGENT_OPS_IMAGE`,
`…_DATA_REGISTRY_IMAGE`, `RELATED_IMAGE_ODH_CORE_BFF_IMAGE`,
`RELATED_IMAGE_ODH_KUBE_RBAC_PROXY_IMAGE` and others. The dashboard-operator
image key is `RELATED_IMAGE_ODH_DASHBOARD_OPERATOR_IMAGE` (from the research,
verify). Setting them through the Subscription's `spec.config.env` (I).

**The ODH operator's TrustyAI module (V).** `internal/controller/modules/trustyai/handler.go`:
controller image `RELATED_IMAGE_ODH_TRUSTYAI_MODULE_OPERATOR_IMAGE`; operand
images for TAS, LMES, EvalHub, GORCH and NemoGuardrails, among them
`RELATED_IMAGE_ODH_EVAL_HUB_IMAGE`, `RELATED_IMAGE_ODH_TRUSTYAI_SERVICE_OPERATOR_IMAGE`,
`RELATED_IMAGE_ODH_KUBE_RBAC_PROXY_IMAGE`. ODH's modules on `main`:
aigateway, aihub, aipipelines, dashboard, data, databaseservice, kserve,
mcplifecycleoperator, mlflowoperator, monitoring, ogx, ray, sparkoperator,
trainer, trustyai, workbenches.

**Versions and the clash (V).** The `fast-3` head is 3.6.0-ea.2
(2026-09-22), declared for OpenShift 4.19–4.22; 3.5.0 GA is declared for
4.19–4.21 only. The ODH bundle ships no `trustyai.opendatahub.io` CRDs, so
with `trustyai` Removed nothing clashes with a standalone TrustyAI operator
(I); but the eval-hub page needs `trustyai` Managed, which installs a second
TrustyAI operator on the same CRDs, hence decision 5 removes the
standalone one. ODH 3.x also adds a GatewayClass
(`openshift.io/gateway-controller/v1`; that it pulls in Service Mesh is I),
kube-auth-proxy and an OAuthClient.

**Installed on `cluster-nm8mw` (V, 2026-10-13, OpenShift 4.22.16).** The
`community-operators` PackageManifest `opendatahub-operator`: default
channel `fast-3`, head `opendatahub-operator.v3.6.0-ea.2`; other channels
`fast` (2.35.0), `odh-2.8.z`, `rolling`, `stable`. The CSV supports
`AllNamespaces` only and owns `DSCInitialization`, `DataScienceCluster`,
`GatewayConfig`, `Auth`, `HardwareProfile`, `Kueue`, `Platform`,
`FeatureTracker`. The operator log: "default DSCI auto-creation is
disabled"; the CSV's `alm-examples` hold a `default-dsci` and a
`default-dsc`. DSC v2 components: aigateway, aipipelines, dashboard,
feastoperator, kserve, kueue, llamastackoperator, mcplifecycleoperator,
mlflowoperator, modelregistry, ogx, ray, sparkoperator, trainer,
trainingoperator, trustyai, workbenches; `trustyai.eval.lmeval` is
required, with `permitOnline` and `permitCodeExecution`. ODH creates the
Gateway `data-science-gateway` (`openshift-ingress`, Route host `rh-ai.<apps
domain>`), which answers 302 to the OpenShift OAuth login and accepts a
ServiceAccount's Bearer token for the dashboard's `/api/*`. The MLflow CRD
(`mlflows.mlflow.opendatahub.io`) is cluster-scoped and its CEL rule allows
only the name `mlflow`; the operator runs it in the applications namespace
with `--app-name=kubernetes-auth --enable-workspaces
--workspace-store-uri=kubernetes:// --static-prefix=/mlflow`, every
namespace is a workspace, and a call without `X-MLFLOW-WORKSPACE` is refused.
The EvalHub CRD's `spec.mlflow` has only `tls.caBundle`; the tracking URI
comes from `spec.env` `MLFLOW_TRACKING_URI`, and the operator mounts a CA
bundle and an MLflow token (fork clone `trustyai-service-operator`,
`controllers/evalhub/deployment.go:143-154`, `configmap.go:1011-1040`). The
CRD's defaults: providers garak, garak-kfp, lm-evaluation-harness;
collections leaderboard-v2, safety-and-fairness-v1,
toxicity-and-ethical-principles; tenancy `multi`. The lm-eval provider
ConfigMap: job image `quay.io/opendatahub/ta-lmes-job` (by digest), 192
benchmark ids, and the hint that the model name must be a HuggingFace
model ID, since it loads the tokenizer from the HF Hub. The image's source
is `opendatahub-io/lm-evaluation-harness` (`Dockerfile.lmes-job`; the
`odh-konflux-central` pipeline `ta-lmes-job-push.yaml`). On branch
`release/odh-3.6-ea2`, `main.py` `build_lmeval_config` uses lm-eval's
`local-completions` backend on `<model.url>/completions` with
`tokenized_requests: False` and no chat template, takes the tokenizer from
the benchmark's `parameters.tokenizer` (else the model name), and limits the
set with `parameters.num_examples`. The backend is hard-coded, with no
parameter to choose another: `return ("local-completions", …)` at
`main.py:621-636` on `release/odh-3.6-ea2`, and the same on `incubation`
(the development branch, `main.py:823`, last change `ebe6a20`
2026-10-13); `main` has no `main.py`. So the provider needs a model
endpoint with `/completions`, which EnMaaS has not ("The gateway on
EnMaaS"). Lukas, 2026-10-14: leave it, the flywheel does not use it. A
change to lm-eval's `local-chat-completions` would run only its
generation tasks (`ifeval`, `gsm8k`); **I** (lm-eval's docs, not checked
here): loglikelihood tasks (`mmlu`, `arc`, `hellaswag`) need the logprobs
of `/completions`. A job's `experiment.name` is the MLflow
experiment it logs to; on 2026-10-14 job `c57dd30f…` (`ifeval`, 5 prompts)
logged run `c5902a21…` with 7 metrics and 0 artifacts. The image adds about
12 GB to the node's disk.

**Modules (V).** Two shapes: an in-host plugin (`model-training`,
`plugin-template`) exports `./extensions`, is compiled into the main
bundle, has no BFF, needs a host rebuild; a federated remote (`eval-hub`,
`agent-ops`) is one image with the rspack bundle and a Go BFF, run as its own
Deployment and Service `odh-dashboard-<slug>-ui`, not a sidecar.
Registration: in dev the `module-federation` field of `package.json`; in
production the env `MODULE_FEDERATION_CONFIG` from ConfigMap
`federation-config`, key `module-federation-config.json`. The backend
proxies `/_mf/<name>/*` and `/<slug>/api` and writes the remotes into
`index.html`; the frontend loads `<name>/extensions` at runtime, so a new
remote needs no host rebuild, but host and remotes are version-locked
(`docs/module-federation.md`). Enabling: `spec.modules.<name>.state` in the
dashboard-operator plus DSC gates (skipped when `spec.components` is empty);
in the frontend `app.area` feature flags in `spec.dashboardConfig` plus
required DSC components. The dashboard-operator's registry
(`dashboard-operator/internal/controller/modules.go`, in the odh-dashboard
repo) has per module `Name`, `ContainerName`, `Port`, `ImageEnvVar`,
`ManifestSlug`, optional `ProxyPaths`, `RequiredByMaaSPortal`; ports in use
8043 (model-registry), 8143 (gen-ai), 8243 (maas), 8343 (mlflow), 8543
(eval-hub, container `eval-hub-ui`), 8643, 8843 (agent-ops).

**eval-hub at runtime (V).** The page needs `disableLMEval: false` (default
true) and DSC `trustyai` Managed. Its BFF finds EvalHub through env
`EVAL_HUB_URL`, then the `evalhub-discovery` ConfigMap, then an EvalHub
resource in the selected namespace, then one in the dashboard's namespace;
Role `trustyai-evalhubs-role` lets every logged-in user list EvalHubs in the
dashboard's namespace (why RHOAI looks only in `redhat-ods-applications`).

**agent-ops (V).** Its "agent" is a deployed runtime: a `Sandbox`
(`agents.x-k8s.io/v1beta1`) labelled `openshell.ai/managed-by=openshell`.
It lists, shows, starts, stops, restarts, deletes and deploys agents (A2A,
langgraph, crewai). Federated module `agentOps`, port 8843, no DSC gate,
feature flag `agentOps` (default off), a "Workspaces" tab on the AI hub ›
Agents page (Dev Preview); deploy routes behind `agentOpsDeploy`. Last
change 2026-10-08. Our tabs could join that page through
`app.tab-route/tab` on `agents-tab-page` (I); not taken, see the next
paragraph.

**AI hub, nested navigation and the flywheel's agents and models (V,
2026-10-14, odh-dashboard `upstream/main` `7140a4f`).**

- **AI hub order.** In `frontend/src/plugins/extensions/navigation.ts` the
  section `ai-hub` (line 44) holds:
  1. Agents: `agents-tab-page`, `/ai-hub/agents`, group `1_agents`, Dev
     Preview (lines 77-81).
  2. Models: `models-tab-page`, group `2_models` (lines 53-57). Its tabs
     are Catalog, Registry and Deployments.
  3. MCP servers: group `3_mcp_servers` (lines 65-71).
  4. Connections and Data come after, both behind flags that are off by
     default.
- **Nested sections.** An `app.navigation/section` whose `section` names
  another section is rendered inside it. The test "Nested sections
  (subsections)" puts Compute inside Settings
  (`frontend/src/app/navigation/__tests__/NavSection.spec.tsx:286-330`).
  No module contributes a nested section yet.
- **Agents › Catalog.** It sits in `packages/model-registry/upstream/frontend`,
  behind the flag `agentsCatalog` (default off), and needs the model
  registry component. It shows a card gallery with a Framework filter
  (Claude Code, OpenCode, Python among the labels).
  - A catalog `Agent` has `name`, `displayName`, `description`, `readme`,
    `framework`, `labels`, `logo`, `repositoryUrl`, `env`, `artifacts` (the
    image) and `customProperties` (`src/app/agentsCatalogTypes.ts:18-34`).
  - Nothing adds an entry from the dashboard. The empty state says "Use the
    OpenShift console to add agent templates to the catalog."
    (`src/app/pages/agentsCatalog/screens/AgentsCatalog.tsx:89`).
  - The BFF's model holds more than the frontend shows: an `AgentArtifact`
    with an `artifactType` and an inline `content`
    (`packages/model-registry/upstream/bff/internal/models/agent_catalog.go:5-62`).
    Its mocks show a `template-artifact` holding an `agent.yaml` (name,
    framework, description, env) beside `image-artifact` entries
    (`bff/internal/mocks/static_data_mock.go:4193-4210`). Read-only; the
    entries come from catalog sources (V, 2026-10-14, read by a subagent).
- **MaaS external models** are the dashboard's API models.
  - They are `ExternalProvider` and `ExternalModel` objects,
    `inference.opendatahub.io/v1alpha1`
    (`packages/maas/bff/internal/constants/gvr.go:36-46`).
  - They show under Models › Deployments as "External models", next to
    "Internal models".
  - The create form asks for Project, Name, a provider reference, and
    "GenAI studio for subscribed users". It has no price field
    (`packages/maas/frontend/src/app/pages/external-models/CreateExternalModel/CreateExternalModelForm.tsx:289-402`).
  - A provider holds a type, an endpoint, an authentication type and a
    credential Secret.
  - These provider types, API formats and gates were read by a subagent
    and not re-read:
    - provider types: OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Google
      Vertex AI
    - API formats: OpenAI Chat `/v1/chat/completions` and Anthropic
      Messages `/v1/messages`
    - the gates: flag `modelAsService` (on by default) and the DSC
      condition `ModelsAsAServiceReady`
- **On `cluster-nm8mw`, 2026-10-14:**
  - These DSC conditions are False: `ModelsAsAServiceReady`, `KserveReady`,
    `ModelRegistryReady` and `TrustyAIReady`.
  - The cluster has no `externalmodels`, `externalproviders` or `sandboxes`
    CRD.
  - AI hub shows only Models. Its Deployments page says "No model serving
    platform selected".
- **How the harness runs an agent it does not know** (`agent-eval-harness`
  `upstream/main`):
  - The `cli` runner runs a command template with the placeholders
    `{workspace}`, `{model}`, `{output_dir}`, `{timeout}`,
    `{system_prompt}`, `{args}` and others. The command must exit 0 and
    write to `{output_dir}`. Tokens and cost come only from
    `{output_dir}/metrics.json` (`docs/opaque-cli-runner-contract.md`).
  - The `responses-api` runner takes a `base_url`
    (`agent_eval/agent/responses_api.py:65-116`).

**EnMaaS, Red Hat Engineering's AI gateway (V, read 2026-10-13 in the
`openshift-eval` session `999d0b72`; reachability V 2026-10-14).**

- **Source.** The guide is on source.redhat.com
  (`departments/products_and_global_engineering/workload_management/enmaas`).
  That page embeds `https://dashboard.enmaas.devshift.net/welcome`, which
  was read with Lukas's own Chrome sign-in.
- **API.** The base URL is `https://api.enmaas.devshift.net/v1`. It serves
  `/chat/completions`, `/responses` and `/messages`. Auth is
  `Authorization: Bearer <key>`, or `x-api-key` on Messages. One key works
  for every model. The key comes from Atlas
  (`https://devservices.dpp.openshift.com/support/enmaas/`, VPN needed).
  The guide calls it `ENMAAS_KEY`.
- **The free model is GLM 5.3,** `rits/zai-org/glm-5-3`: "no usage cost".
  - It has a 1M context and 65,536 output tokens, and takes text only (an
    image is a 400).
  - It is a reasoning model and takes no `developer` role.
  - Set both penalties to 0, or it drifts into Chinese.
  - `GET /v1/models` can leave it out, so pin the id.
- **Other models cost money.** EnMaaS also routes Opus 5.5, GPT-5.6 and
  Claude Sonnet. Their spend counts against the user's Red Hat AI budget,
  which the "AI Budget Help" tool shows until the EnMaaS dashboard is live.
- **Beta.** It had maintenance announced for 2026-10-16, 15:00 to 17:00 ET.
- **Reach.** From the gateway pod on `cluster-nm8mw`, the host resolves to
  `32.190.33.3`, and `GET /v1/models` with no key answers 401. So the
  cluster reaches it without a VPN.
- **Not checked:** whether EnMaaS is built on ODH's MaaS.

**EnMaaS, measured with Lukas's key (V, 2026-10-14 15:01 to 15:03 UTC,
`scripts/enmaas/probe.py` run in the gateway pod on `cluster-nm8mw`).**
The Secret `enmaas` exists since 14:53 UTC; after `oc rollout restart
deploy/gateway` the alias `enmaas-glm-5-3` answered "ok" through the
gateway (200, 2.1 s, 19 in and 42 out tokens, 39 of them reasoning).

- **The catalog is not the list of models.** `GET /v1/models` lists 15 ids
  with `Authorization: Bearer` (4 Gemini, 11 Claude, all `owned_by:
  vertex`) and the 11 Claude ids with `x-api-key`. It lists no OpenAI
  model and no GLM, and both answer.
- **OpenAI ids go to OpenAI itself.** On `/chat/completions` and
  `/responses`, an id EnMaaS does not route itself is passed to OpenAI's
  API: an unknown id answers 404 `model_not_found` with the headers
  `openai-organization: red-hat-ymenlk` and `openai-project`. So an id that
  does not exist costs nothing, and a guess is the only way to find one: no
  list names them. 28 OpenAI ids answered by 15:47 UTC, and 4 more exist:
  - GPT-6, only under a code name: `gpt-6.1-sol`, `gpt-6-sol`,
    `gpt-6-astra`, `gpt-6-luna`. Plain `gpt-6` is a 404, and so are
    `gpt-6-mini`, `-nano`, `-pro`, `-codex`, `gpt-6.5-sol`, `gpt-7-sol` and
    about 40 more guessed names. The first probe tried no GPT-6 id at all;
    Lukas asked, and the code names turned up.
  - `gpt-5.6` (served as `gpt-5.6-sol`, which answers too), `gpt-5.6-luna`,
    `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano`, `gpt-5.3-codex`,
    `gpt-5.2`, `gpt-5.1`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`.
  - `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-4o`, `gpt-4o-mini`,
    `o3`, `o4-mini`, `o3-mini`, `o1`.
  - The `-pro` models exist and are not measured: `o3-pro` and `o1-pro`
    answered; `gpt-5.5-pro`, `gpt-5.4-pro`, `gpt-5.2-pro` and `gpt-5-pro`
    refused level `low` with a 400, which a missing id never gets.
  - 404: `gpt-oss-120b`, `gpt-oss-20b`, every `-mini`, `-nano` and `-codex`
    of 5.5 and 5.6, `gpt-5.2-codex`, `gpt-5.1-codex`, `gpt-5.1-codex-mini`,
    `gpt-5-codex`, every `-chat-latest`, `chatgpt-4o-latest`,
    `gpt-4.5-preview`, `o1-mini`. So today's judge `gpt-oss-120b` has no
    EnMaaS route.
- **`/messages` has its own allow list.** An id it does not allow answers
  403 "model '…' is not permitted by access policy", from EnMaaS, not from
  a provider. `gpt-5.6` and `gpt-5.4-mini` get that 403.
- **Claude, on Vertex.** 8 of the 11 listed ids answer on `/messages`:
  `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-opus-5`,
  `claude-sonnet-5`, `claude-opus-4-8`, `claude-opus-4-6`,
  `claude-sonnet-4-6`, `claude-haiku-4-5`. Listed but 404 from Vertex
  ("Publisher model `projects/ge-enmaas/…` was not found"):
  `claude-sonnet-4-5`, `claude-opus-4-5`, `claude-opus-4-7`. A Claude id on
  `/chat/completions` or `/responses` goes to OpenAI: 404.
- **Gemini, on Vertex.** The 4 listed ids answer on `/chat/completions`,
  served as `google/<id>`. Not tested on the other dialects.
- **The dialects, with a tool and streamed** (`get_weather`, the way an
  agent calls it):

  | Model | `/chat/completions` | `/responses` | `/messages` |
  |:--|:--|:--|:--|
  | `rits/zai-org/glm-5-3` | text, tool, stream | text, tool, stream | text, tool, stream |
  | `gpt-5.6`, `gpt-5.4-mini`, `gpt-6-sol`, `gpt-6-luna` | text; a tool only with `reasoning_effort: "none"` | text, tool, stream | 403 |
  | `gpt-6.1-sol`, `gpt-6-astra` | text; no tool: they refuse level `none` | text, tool, stream | 403 |
  | `claude-sonnet-5-5` | 404 | 404 | text, tool, stream |

  OpenAI's own rule, word for word: "Function tools with reasoning_effort
  are not supported for gpt-5.6 in /v1/chat/completions. To use function
  tools, use /v1/responses or set reasoning_effort to 'none'." The same for
  `gpt-5.5` and `gpt-5.4-mini`. It holds with no `reasoning_effort` in the
  request too, so the default level counts as one. So an agent that uses
  tools and reasoning on GPT 5.4 and later must speak Responses.
- **So, per agent:** Codex (Responses) runs on GPT or GLM; OpenCode runs on
  GPT through Responses, or on GLM and Gemini through Chat Completions;
  Claude Code (Messages) runs on Claude or GLM. GPT under Claude Code needs
  a translation, as the gateway's LiteLLM does for Cerebras today.
- **Rate limits.** Only OpenAI answers with limit headers:
  `x-ratelimit-limit-requests` 15000 and `x-ratelimit-limit-tokens`
  40000000, the per-minute limits of Red Hat's OpenAI organization, which
  every EnMaaS user shares. Claude, Gemini and GLM send none.
- **Prices.** EnMaaS shows none. The list prices in the gateway's LiteLLM
  1.99.1 table (`model_prices_and_context_window_backup.json`), USD per
  million tokens in, out, cached in: `gpt-5.6` 4, 20, 0.40; `gpt-5.5` 5,
  30, 0.50; `gpt-5.4` 2.50, 15, 0.25; `gpt-5.4-mini` 0.75, 4.50, 0.075;
  `gpt-5.4-nano` 0.20, 1.25, 0.02. For comparison, the gateway's Cerebras
  prices: `qwen-3.8-27b` 0.99, 1.49; `gpt-oss-120b` 0.35, 0.75. The table
  has no Claude 5 entry. Whether EnMaaS bills the Red Hat AI budget at list
  price is not checked.
- **What the probe spent.** About 1,300 input and 400 output tokens on paid
  models in all, about 0.01 USD at list price; 4 streamed calls are not
  counted.
- **Speed** (V, 2026-10-14 15:24 UTC, `scripts/enmaas/models.md`, the
  `speed` stage: 3 streamed answers of about 300 words per model, from the
  gateway pod, 4 models at a time). Tokens per second of the stream, the
  median:
  - `gpt-5-mini` 171, `gpt-4.1-mini` 151, `gpt-5.4-mini` 138, `gpt-5.4-nano`
    118; `gpt-5.6` 58, `gpt-5.4` 48, `gpt-5.5` 41. The first token comes
    after 0.6 to 1.2 s at reasoning level `none` or `minimal`.
  - GPT-6 (15:47 UTC): `gpt-6-luna` 113, `gpt-6-sol` 58, `gpt-6-astra` 40
    and `gpt-6.1-sol` 34, both at level `low`. No GPT-6 price is in
    LiteLLM's table; `gpt-5.6-luna` is 0.2 and 1.2 USD per million
    tokens, at 91.
  - `claude-sonnet-5-5` 107, `claude-opus-5-5` 104, `claude-haiku-4-5` 79,
    `claude-sonnet-4-6` 37.
  - `gemini-3.6-flash` 199, but its first token comes after 3.9 s: it
    thinks first, even at level `low`, and Vertex counts that thinking
    apart from `completion_tokens` (687 against 343).
  - `rits/zai-org/glm-5-3` 76, but it reasons first: 1,742 of 2,048 output
    tokens, so a 300-word answer was cut at the limit after 26 s.
  - For comparison, `openshift-eval` chose Cerebras for "500 to 800 tokens
    per second", in its own words; that is the reason in its `PLAN.md`
    decision row "Model hosting", not a measurement of this repo.
- **The speed stage spent** about 0.56 USD at list price, plus
  `claude-opus-5-5`, `claude-sonnet-5-5`, `gemini-3.8-flash` and the four
  GPT-6 ids, which have no price in LiteLLM's table.

**The gateway on EnMaaS (V, 2026-10-14, LiteLLM 1.99.1 in the gateway pod
on `cluster-nm8mw`; applied 16:04 UTC).**

- **How LiteLLM picks a model's fields.** It takes a model for GPT-5 when
  `"gpt-5" in model` (`litellm/llms/openai/chat/gpt_5_transformation.py:73`)
  and for the o series when the name is `o<digit>…` and in its own model
  list (`o_series_transformation.py:117-123`). Anything else gets the plain
  OpenAI path. `gpt-5-mini` works through it as it is.
- **GPT-6 on the plain path fails** (measured with `litellm.completion` in
  the pod):
  - On Chat Completions it sends `max_tokens`: 400 "Use
    'max_completion_tokens' instead".
  - It drops `reasoning_effort` as unsupported, or refuses it without
    `drop_params`.
  - On the Responses route (`openai/responses/<id>`) it sends
    `temperature`: 400 "Unsupported parameter: 'temperature'".
- **The fix is in the alias, not in code:** `model:
  openai/responses/gpt-6-luna` (every route goes through OpenAI's
  Responses API, where tools work at every reasoning level),
  `allowed_openai_params: ["reasoning_effort"]`, `additional_drop_params:
  ["temperature", "top_p"]`. On `/v1/responses`, LiteLLM sends the id
  upstream without the `responses/` prefix (`model: gpt-6-luna` came back).
- **The hook** (`deploy/gateway/config/cerebras_hook.py`) now acts only on
  aliases that start with `enmaas-glm-` or `unsloth-`. Tested in the pod:
  a Codex-shaped request to a GPT alias passes untouched (`reasoning`,
  `include`, `store`, `prompt_cache_key`, the developer item); the same
  request to GLM is shaped.
- **Through the gateway** (`probe.py` `--stage dialects` with
  `ENMAAS_BASE_URL=http://localhost:4000/v1`): `enmaas-gpt-5-mini`,
  `enmaas-gpt-6-luna`, `enmaas-gpt-6-sol` and `enmaas-glm-5-3` each answer
  on Chat Completions, Responses and Messages, plain, with a tool, and
  with a tool streamed. So Claude Code can run on GPT: LiteLLM translates
  Messages, which EnMaaS refuses for GPT.
- **Agent-shaped second turns** (`scripts/enmaas/agent_shapes.py`): Claude
  Code on `gpt-5-mini`, `gpt-6-luna` and GLM, Codex on the same three,
  OpenCode on `gpt-5-mini` and `gpt-6-luna`: all 200, all answered "12 °C,
  light rain" from the tool result, 0.8 to 3.3 s. The harness's judge
  shape, a forced tool call on Chat Completions: 200 with a grade on
  `gpt-6-sol` (5.7 s), `gpt-5-mini` and GLM.
- **JSON mode on GPT-6 needs the word "json" in the input.**
  `response_format: json_object` with "JSON" only in the system prompt:
  200 on `enmaas-gpt-5-mini`, 400 on `enmaas-gpt-6-sol`, "Response input
  messages must contain the word 'json'". The Responses route moves the
  system prompt to `instructions`, outside the input.
- **Rate limits differ per model:** `gpt-5-mini` answers with
  `x-ratelimit-limit-requests` 30000 and `x-ratelimit-limit-tokens`
  180000000 per minute, against 15000 and 40000000 for `gpt-5.6` and
  `gpt-6-sol`.
- **No legacy `/v1/completions` on EnMaaS** (about 18:20 UTC, free GLM
  calls through the gateway). `enmaas-glm-5-3` answered
  `/v1/chat/completions` in 3.0 s ("Ok"), and `/v1/completions` with 503
  and the OpenShift router's page "Application is not available": no
  backend serves that path. EvalHub's lm-eval provider calls only
  `<model.url>/completions` (its `local-completions` backend, see "How the
  lm-eval provider calls a model" in spec 01 phase 1 status), so it has no
  model on the cluster since the switch; spec 01's phase 1 DoD 2 ran on a
  Cerebras alias.

**Dev loop (V).** A package alone with a mocked BFF, no cluster: `cd
packages/<pkg> && make dev-start` (eval-hub uses ports 9106 and 4002).
Inside the dashboard: `pnpm run dev:backend`, `pnpm run dev:frontend`,
`make dev-start-federated` in the package, then `localhost:4010`; needs `oc
login` as a cluster-admin. Frontend only against a cluster: `cd frontend &&
pnpm run start:dev:ext` (falls back to a Route without an HTTPRoute).

**Build (V).** Node 22 (`ubi9/nodejs-22`, ≥22.18.0), pnpm 11.22.0, Go 1.26.
The root `Dockerfile` builds the whole monorepo with
`--max-old-space-size=8192` (87 s on a GitHub runner, run 38406217532); a
module builds from `packages/<m>/Dockerfile.workspace` at the repo root with
`CGO_ENABLED=1`. Images: host, core-bff, kube-rbac-proxy, one per module,
the dashboard-operator. Build on the x86_64 cluster, not the arm64 Mac (I).

**The three routes Lukas was offered (2026-10-13).** A, ODH 3.6.0-ea.2 with
the dashboard and TrustyAI on: the real stack and the upstream module path,
but an early-access release and EvalHub reinstalled the ODH way (picked). B,
the dashboard by hand without ODH: small, keeps the standalone EvalHub, but
fake platform objects and a swapped login that nobody upstream runs. C, a
second cluster with ODH for the UI only: the demo cluster stays as it is,
but a second RHDP order and two clusters to keep alive. Before that, "the
console first, the dashboard later" was offered as the safer pick; Lukas
chose the dashboard module from the start.

**Fallback, route B: the dashboard without ODH (V for the blockers, I for
the fixes).** If ODH 3.6 cannot go on the cluster: without a DSC the
frontend shows "Could not load component state" (`AreaContext.tsx`,
`backend/src/utils/dsc.ts` reads `datasciencecluster.opendatahub.io/v2`),
fixed by installing the DSC CRD and patching a DSC's status (`trustyai:
Managed`); without `auths/auth` (`services.platform.opendatahub.io`)
`isUserAllowed` fails, fixed by the Auth CRD and an `auth` object with
`allowedGroups: [system:authenticated]`; kube-rbac-proxy expects a token
from ODH's Gateway, fixed by the OpenShift oauth-proxy with
`--pass-access-token` and a Route (the backend still accepts
`x-forwarded-access-token`, `docs/migration-openshift-4.19.md`); the CRDs
(`manifests/base/crd`), ClusterRoles and ConsoleLink need cluster-admin; we
write `federation-config` ourselves (the backend creates
`odh-dashboard-config`). The dashboard would sit in `agent-flywheel`, find
EvalHub by the namespace fallback or `EVAL_HUB_URL`, and need our EvalHub
NetworkPolicy widened. Risks: the faked objects can break with any
upstream change; the oauth-proxy swap is untried.

**Contributing (V).** Definition of Ready: a Jira, approval by the Dashboard
Architect, UX sign-off. PR template Problem / Solution / Evidence with
screenshots and a cluster check. Prow-style OWNERS per area. Tests `pnpm
run test`, `test:unit`, `test-unit`, `test:lint`, `test:contract`, Cypress
mocked and e2e (`packages/cypress/cypress/tests/e2e/<module>`). A new module:
the `/module-onboarding` skill, an entry in `modules.go`,
`manifests/modules/<slug>`, a Konflux `.tekton` pipeline, `pnpm run
validate:ports`. The fork `lukaskellerstein/odh-dashboard` was 0 ahead, 1
behind upstream on 2026-10-13.

## 8. `openshift-eval` facts this work must know

- Its `CLUSTER.md` on `main` still says "Do not install Open Data Hub or
  RHOAI" (Lukas, 2026-10-10). Lukas lifted that for this integration on
  2026-10-13. On a cluster both use, remove its TrustyAI operator
  (`deploy/evalhub/operator`, namespace `trustyai-operator`) and its
  `EvalHub` resource before ODH goes in; its Score backend `evalhub` then
  needs ODH's EvalHub.
- Its `docs/my-specs/01-new-design.md` line 7 says "no release has
  EvalHub": true for the upstream operator only. OpenShift AI ships EvalHub
  from 3.4, GA in 3.5.
- Its phase 7 found three things live on EvalHub on OpenShift: the provider
  must be named in the `EvalHub` resource, the server lacks a Role for its
  per-job NetworkPolicy, and the provider needs a SIGTERM handler
  (`openshift-eval` `PLAN.md` section 0, `CLUSTER.md` Status).
- Its stop-fix tests lived in a gitignored `tmp/tests/stopfix/` of a
  removed worktree; they are not in the main checkout.
- The cluster `cluster-vj7vb` (`api.cluster-vj7vb.dyn.redhatworkshops.io:6443`)
  answered neither `oc` (502 Bad Gateway through the sandbox proxy) nor a
  direct request (15 s timeout) on 2026-10-13.
- Its blog posts at `https://www.kellerstein.org/blog/projects/agent-flywheel/`
  carry two small inaccuracies (`docs/outreach.md`, section 5).
- Its branch `generalization` (worktree `.worktrees/generalization`, on
  `a601ae1`, not committed on 2026-10-14) holds
  `docs/my-specs/03-generalization.md`: one flywheel for any use case
  through a "task pack" `tasks/<name>/` (its "task" is our use case, its
  "case" our task, spec 02 decision 12; `task.yaml` beside the harness's `eval.yaml`,
  `cases/`, `splits.yaml`, `agent/` with the v0 brain and `resources/`,
  `hidden/` for what only the judges see), decided by Lukas there on
  2026-10-13 (its section 18). Its phase 1, the support agent as the first
  pack with the same MLflow records, is built and checked on the laptop
  (its `PLAN.md` row "Generalization, phase 1": 92 loader checks, 71 record
  checks, a free live loop on Gemma); phases 2 to 7 are not built. The
  support pack is 100 files, 404 KB on disk, 40 KB as a `tar.gz`.

## 9. Sources

- Red Hat AI 3.5 press release:
  <https://www.redhat.com/en/about/press-releases/red-hat-puts-safety-and-observability-core-enterprise-ai-red-hat-ai-35>
- OpenShift AI 3.5 release notes, new features and Technology Preview:
  <https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/new-features-and-enhancements_relnotes>,
  <https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.5/html/release_notes/technology-preview-features_relnotes>
- OpenShift AI 3.4, Evaluating AI systems:
  <https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/evaluating_ai_systems/index>
- Evaluate AI agents with IBM CLEAR and EvalHub:
  <https://developers.redhat.com/articles/2026/09/03/evaluate-ai-agents-ibm-clear-evalhub-openshift-ai>
- EvalHub: "looks good to me" isn't a benchmark:
  <https://developers.redhat.com/articles/2026/05/19/evalhub-because-looks-good-me-isnt-benchmark>
- Fine-tune AI pipelines on OpenShift AI:
  <https://developers.redhat.com/articles/2026/02/26/fine-tune-ai-pipelines-red-hat-openshift-ai>;
  GRPO with Training Hub:
  <https://developers.redhat.com/articles/2026/08/26/reinforcement-learning-from-verifiable-rewards-with-training-hub-on-red-hat-openshift-ai>;
  Ray with Training Hub:
  <https://developers.redhat.com/articles/2026/08/22/fine-tune-llms-on-ray-with-training-hub-on-red-hat-openshift-ai>
- OpenShift sandboxed containers (Kata):
  <https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html/openshift_sandboxed_containers/index>
- GitHub: <https://github.com/opendatahub-io/agent-eval-harness>,
  <https://github.com/eval-hub/eval-hub>,
  <https://github.com/eval-hub/eval-hub-contrib>,
  <https://github.com/trustyai-explainability/trustyai-service-operator>,
  <https://github.com/opendatahub-io/odh-dashboard>,
  <https://github.com/opendatahub-io/opendatahub-operator>,
  <https://github.com/Red-Hat-AI-Innovation-Team/training_hub>,
  <https://github.com/gepa-ai/gepa>, <https://github.com/rh-ai-quickstart>
