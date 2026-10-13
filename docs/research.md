# Research behind the plan

Gathered on 2026-10-13 by a Claude session in
`~/Projects/Github/lukaskellerstein/openshift-eval` (branch
`redesign-redhat-upstream`, discarded afterwards: everything it found is
here), with nine research agents reading upstream code through `gh` and the
local clones, and direct checks. **V** = verified in code, an API or a doc;
**I** = inferred, not run. Line numbers are of upstream `main` on that day
unless a version is named. `PLAN.md` is the plan; this file is the evidence.

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

| Our piece | Why we built it | Upstream today | Contribution (`PLAN.md` section 7) |
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

## 5. EvalHub, eval-hub-contrib, the TrustyAI operator

**Versions (V).** The reference checkout
`~/Projects/Github/eval-hub/eval-hub` was `540676f` (2026-10-13 07:49 UTC),
`v1.0.2-83`, `VERSION` 1.0.3 not released, equal to upstream `main`.
Release v1.0.2 (2026-09-18). PyPI: `eval-hub-server` 1.0.2,
`eval-hub-sdk` 1.0.6 (2026-10-13). The upstream TrustyAI operator has no
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

**Small EvalHub defects (V).** `K8sRuntime` (`providers.go:115-127`) has no
json tags, so the API drops the four resource fields the OpenAPI schema
names (`cpu_request` and others). The local runtime ignores a provider that
exits without a report (`local_runtime.go:414`, `_ = cmd.Wait()`). The
operator's failure watcher deliberately ignores an adapter's non-zero exit
(reconciler, lines 113-114). Operator #985 (`639411f`) adds the NetworkPolicy
RBAC, but its policy forbids `delete`, while `openshift-eval` saw OpenShift
needing `delete` for the ownerReference update that `main` still makes
(`k8s_runtime.go:396-403`; its runs `eval-4zllw`, `eval-jqhra`).

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
`app.tab-route/tab` on `agents-tab-page` (I).

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
