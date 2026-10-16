# PR drafts for the fork branches

Drafts, not posted. Each PR is opened by Lukas, in his own voice, after his
go (spec 01 §0). Each branch is in Lukas's fork clone of
`fullsend-ai/agent-eval-harness` (`opendatahub-io` until 2026-10-15,
`docs/research.md` §4), made from `upstream/main` `175eed5`
(2026-10-13; C1 to C4), `9bc9a8d` (v1.56.2, 2026-10-14; C6, C8, C9,
C19, C30, C31, C32, C34) or `b306e63` (v1.56.3, 2026-10-16; C20), C7
from C4, C33 from C1. All branches live in the
clone `~/Projects/Github/lukaskellerstein/forks/agent-eval-harness`, with no
worktrees; check one out there with `git switch <branch>`.
Before a PR, rebase the branch on the newest `upstream/main` (spec 01 §5):
on 2026-10-16 it was `b306e63` (v1.56.3), with commits on `score.py`'s
judge deny list after `9bc9a8d`; `flywheel-integration` merged it at
`1bf99ae` without a conflict.
The branches of the other forks (spec 02 §5) get their sections here
too, each naming its repo, its base commit and its clone; their issues
are opened with the PRs (spec 02 decision 15).

Written by the subagent that built each branch, checked by the agent
(2026-10-14). The test counts are the agent's own runs; the baseline is
2289 passed on `175eed5`, 2296 on `9bc9a8d`, 2291 on C4, each with 4
skipped and 2 deselected. From the second round (C35 to C39, 2026-10-15),
the branch's count under **Tests** is its subagent's run, and the agent's
own count is for the `flywheel-integration` merge, in spec 02 §5.1.

## The order matters

- C1 kills each agent's process group by `pid`. If C1 lands first, the
  codex tests of C2 and of the gateway recipe need `pid = 4242` on their
  fake process and a stubbed `os.killpg` (done on `flywheel-integration`,
  commit `e4413f5`).
- C2 and the gateway recipe both edit the `cost_source` row of
  `website/reference/runs-directory.md`; C2 and the sealed workspace both
  edit the `runner` line of `CLAUDE.md` and the field table of
  `website/reference/config/runner.md`. The second to land keeps both
  texts.
- The recipe says that no runner has a price table for gateway aliases;
  once C2 lands, that sentence points at `runner.pricing` (the
  `flywheel-integration` text).
- C4 before both C7 PRs: they are stacked on it, because their tests need
  the real SDK. The reuse PR of C8 is stacked on its runner-factor PR.
- `AGENTS.md` (a link to `CLAUDE.md`) has a 6,000-token budget in CI's
  skillsaw (0.10.0, `--strict`; warnings fail). All branches together
  measured 6,071 before C2 and C3 got their short `runner` lines
  (`1bbe22f`, `5a1bd5e`); now 23,721 bytes, about 100 tokens under. A new
  line in `CLAUDE.md` on any branch: check the sum again on
  `flywheel-integration`.
- C2 and C32's PR B both change codex's cost (`codex.py` `_cost`, five
  doc pages). `flywheel-integration` `1e7868b` holds the merge: a
  configured price wins behind a gateway, with no litellm estimate beside
  it, and without one the cost is `unavailable`; C2's three codex pricing
  tests run on OpenAI's own API (`gateway=False` in their helper), and one
  new test covers a price behind a gateway. With C36's `50f9058`
  (`flywheel-integration` `986153c`), the no-price path on OpenAI's API
  returns litellm's figure as `harness:estimate`, or `unavailable`, and
  C2's two tests of it assert that. The second of the two to land takes
  that.
- C7 and C31 meet in `agent_eval/evalhub/adapter.py` and `runner.py`
  (`e0e21d0`): both sets of runner helpers stay; C7's
  `_load_judges_and_score` takes C31's `run_dir` and passes
  `run_id=run_dir.name, runs_dir=run_dir.parent`; the run is closed before
  scoring, as C31 does. C31's `test_runner_wait.py` fixture then needs
  `SyncEvalHubClient` and `EVALHUB_MODEL_URL`.
- C33 waits for C1. With C7 landed, C33's subagent suggests one more line in
  C7's thread pool: `process_group.stop_all()` before
  `pool.shutdown(cancel_futures=True)`, so Ctrl-C does not wait for the
  other running agents (not done: C7's branch has no `process_group`).
- C33 with C37's round of C34 (`flywheel-integration` `2c55f55`):
  `agent_eval/hooks.py` imports both `process_group` and
  `case_input.find_input_file`, and the hooks CLI's stop test runs on an
  `input.json` case. The second of the two to land takes that.
- C34 and C8, with C37's round (`flywheel-integration` `1a2f2bc`,
  `b62f9da`): the guide's and the matrix reference's "any other factor"
  rows take C34's text and keep C8's `runner` row and its `cli`
  placeholder sentence. With C34's threshold fix, a cell that misses a
  floor is stamped and reused, and `thresholds` leave C8's recipe
  (`_NOT_IN_RECIPE`). The second of the two to land takes that.
- C34 with C3, C19 and C38 (`1a2f2bc`, `3bb423c`): under C3's sealed
  workspace the input file is read from the case record; C38's
  `agent_eval/workspace_files.py` drops its own `find_input_file` for
  `agent_eval/case_input.py`'s; the new workspace path
  `<tmp>/agent-eval/<eval-name>/<run-id>` goes into C19's `task_format`
  docstring and spec 016, and into C3's `runner.md` and its sealed tree in
  `skills/eval-run/references/data-pipeline.md`. The second of each pair
  to land takes that.
- C6 and C30 meet in `trace_builder.py`'s tool-result loop and
  `log_results.py`'s case-mode loop (`flywheel-integration` `0084662`). An
  untimed tool result keeps its output for every log, so `keep_untimed`
  and C6's `STREAM_JSON` import go; the per-step loop keeps C6's
  `agent=runner_type`; C6's golden traces take the `OK` status and the
  Harbor Bash span's output. The second of the two to land takes that. On
  MLflow 3.5.0, C6's `test_log_results_traces_codex_opencode_and_plain_cli_runs`
  then fails: 3.5.0 renames repeated span names (`shell_1`, `shell_2`;
  `mlflow/tracing/utils/__init__.py:191`), 3.17 does not. C6's test
  accepts both, or C6's PR says it needs 3.17.
- C31 with C38's round, on `flywheel-integration` `392baca`: with C7,
  C7's pool builds each case's workspace in `run()`, the guardrails, the
  snapshot and `_modified/` live in C7's `_run_case`, `_load_judges_and_score`
  passes `dataset_dir`, and C7's OCI export takes the cases the judges
  read, without `.git` (it merged without a conflict and copied the
  delivered dataset, annotations included; a test catches it). With C19,
  `score.py`'s `_dataset_root` falls back to `resolve_dataset(config)`,
  C19's `task_files` rides along into `agent_eval/workspace_files.py`,
  `copy_dataset` fills `<tmp>/dataset`, and a task's `expected` reaches the
  pod's judges but not its agent (local, ConfigMap, S3). With C3, the
  sealed split is one `provision_case_workspace(..., record=)` call and
  its per-case `git init` goes, since `snapshot()` makes the repository.
  The second of each pair to land takes that.
- C19 and C8's reuse PR: C8's `_cell_recipes` (`orchestrate.py`) reads
  `dataset.path` directly; with C19 it must digest
  `resolve_dataset(config)`, or a changed task reuses a stale cell
  (`flywheel-integration` `89cb326`, with a test in
  `tests/test_anova_reuse.py`). C19 drops `adapter.py`'s `import shutil`;
  C7's run-folder export still needs it. The second of each pair to land
  takes that.
- C20 and C37's round of C34 both add `--no-fail-on-regression` to
  `score.py` (`flywheel-integration` `2293963`): one flag, its exit
  following `enforced`, its help naming both uses. C20 moves the reward
  composition out of `agent_eval/harbor/reward.py`, where C38 and C39
  changed the verifier. The second of each pair to land takes that.
- C21 is stacked on C19 (it reads `task.yaml`). C20 and C21 are separate
  branches; on `flywheel-integration` `2137cdd` each split block also
  carries its cases' reward mean, and C21's keys are written after C20's
  reward in `score.py`'s `cmd_judges` and Harbor's `run.py`. The second
  of the two to land adds those few lines, with the tests in
  `tests/test_named_splits.py`.
- C6 to C9 share files with other contributions:
  `website/reference/runs-directory.md` (C2, the gateway recipe, C8, C9),
  `website/reference/config/runner.md` (C2, the sealed workspace, C6),
  `agent_eval/evalhub/adapter.py` (the sealed workspace, C7),
  `agent_eval/agent/cli_runner.py` (C1, C8), `tests/test_config_raw_readers.py`
  (C7, C9) and a few more pages in `website/`. Git merged them all into
  `flywheel-integration` without a conflict; a branch rebased after
  another one lands can still conflict there.

## C1 — `fix/stop-on-sigterm` (`ec71b53`)

**Title:** `fix: stop every agent when the harness stops (SIGTERM, Ctrl-C, SIGKILL)`

**Problem.** The CLI runners start agents in their own sessions, so nothing
sent to the harness's group reaches them, and the group was killed only on a
timeout. Python's default SIGTERM action skips every `finally`. A SIGTERM to
`execute.py` (Kubernetes stopping a pod, Claude Code ending a background
task) or a SIGKILL (EvalHub's local runtime cancelling a job with
`Kill(-pid, SIGKILL)`, `local_runtime.go:65`) left agents running and
spending. The claude-code runner's timeout killed the CLI but not its
children. A parallel run under Ctrl-C kept running every queued case.

**Solution.**

- `agent_eval.agent.process_group`: `popen()` and `release()` give a group
  kill on every exit path, for all four CLI runners.
- `install_stop_handler()`: SIGTERM and SIGHUP kill every tracked group, then
  exit 128 + signum through the normal cleanup. `nohup` is respected.
- A lifeline-pipe watchdog kills the remaining groups when `execute.py` dies
  by SIGKILL.
- `execute.py`'s parallel loop cancels queued cases and kills running agents
  on any exit.

**Tests.** `tests/test_stop_agents.py` uses a fake agent that spawns a
long-lived child. It covers leftovers after a normal exit, the claude-code
timeout, SIGTERM per runner, SIGTERM and SIGINT on a parallel run (no queued
case starts), SIGKILL per runner, no spawn once stopping, and an ignored
SIGHUP staying ignored. Every one of them failed on main. Full suite: 2303
passed.

**Points a reviewer can raise** (from the subagent's report): SIGKILL
without a TERM grace period; the group is also killed after a normal exit;
claude-code no longer gets the terminal's Ctrl-C directly; cursor is
included; `stop_all()` refuses new agents for the rest of the process; a
SIGTERM during a spawn can miss that one agent.

## C2 — `feat/runner-price-override` (`1bbe22f`)

**Title:** `feat(runner): runner.pricing — price claude-code and codex runs of models the runner cannot price`

**Problem.** Claude Code prices every token at Anthropic rates. Behind an
`ANTHROPIC_BASE_URL` gateway serving a non-Claude model (a LiteLLM alias
such as `gpt-oss-120b`), its figure is the price of a model that never ran,
labelled `runner:estimate`. The codex runner prices through
`litellm.model_cost` only, so a gateway alias gets `cost_usd: null`. Spec
014's cost substrate prices OpenRouter generations only and lists a price
table as future work.

**Solution.**

- `runner.pricing` maps a model id to `input_per_mtok` / `output_per_mtok`
  (plus optional `cache_read_per_mtok` / `cache_write_per_mtok`, defaulting
  to the input price), in USD per million tokens. It lives in
  `agent_eval/providers/pricing.py` and is parsed on every runner block.
- When every model that used tokens has a price, claude-code reprices
  `modelUsage` per model and codex prices its turn usage, on both the normal
  and the timeout path. `cost_source` becomes `harness:estimate`, the label
  spec 014 reserved; Claude Code's own figure stays as
  `per_model_usage[m].cost_usd_estimate`.
- A missing price leaves the run exactly as today and warns, naming the
  model. The table is ignored under an OpenRouter plan. Without the block
  nothing changes.
- Docs: the runner reference, the cost-provenance tables, `CLAUDE.md` and
  the eval.yaml template.

**Tests.** 33 new tests with a fake `claude` binary and a fake codex process
(no model calls): the price arithmetic, parsing and load errors with their
config path; model lookup, the single-model fallback and the all-or-nothing
rule; the plan exclusion, the timeout paths, and unchanged behaviour without
the block. Full suite: 2322 passed. `mkdocs build --strict` and
`skillsaw --strict` are clean.

## C3 — `docs/gateway-recipes` (`0ca0f69`)

**Title:** `docs(cookbook): run agents through a model gateway — pin the env routing and fix the claude-code cost label`

**Problem.** A LiteLLM-style gateway already works with the `claude-code`,
`codex` and `cli` runners by environment alone, but nothing documented or
tested it, so a refactor of the allowlists, the `runner.env` merge,
workspace settings or the Codex `-c` overrides could break it silently. Two
doc statements sent users the wrong way: an `ANTHROPIC_BASE_URL` example
ending in `/v1`, and the claim that Codex reads `OPENAI_BASE_URL`
(codex-cli 0.154.0 does not). The claude-code runner also mislabelled a
gateway set through `execution.env` / `runner.settings.env` as
`runner:reported`, contrary to spec 014.

**Solution.**

- A cookbook recipe covering claude-code, Codex through a model provider
  declared in `runner.settings`, the cli runner, the `openai:/` judge, a
  check before a paid run, and cost labels per runner. It adds no provider
  kind, stays on spec 014's plain-env path, and links Model providers.
- The cost label now follows the endpoint the CLI actually calls: the
  `--settings` env block counts, and Vertex/Bedrock override the base URL.
- Two doc corrections.

**Tests.** `tests/test_gateway_env.py` (10 tests): exported and `runner.env`
gateway variables reach Claude Code; the settings env gateway gets
`runner:estimate`; a Codex provider written as a mapping or as dotted keys
parses back to the same TOML; `env_key` passes only via `runner.env`; the
key never appears on argv; the cli runner inherits the environment and
ignores `runner.env`. `tests/test_claude_cli_direct.py`: unit tests for the
label. Full suite: 2302 passed. `mkdocs build --strict` is clean. Behaviour
was checked against Claude Code 2.1.299 and codex-cli 0.154.0 with local
stand-in servers, no model call.

## C3 — `feat/isolated-case-workspace` (`5a1bd5e`)

**Title:** `feat(workspace): sealed per-case workspace (runner.workspace_mode: sealed)`

**Problem.** In case mode the agent runs in
`<tmp>/agent-eval/<run>/cases/<case-id>/`. The path carries the case name,
which can spell out the expected answer (#150). `input.yaml` and
`answers.yaml` sit beside the agent, and every sibling case, plus earlier
runs, is one `../` away (#151). Symlinks and an `additionalDirectories`
grant lead back into the project, where the dataset and past runs live.

**Solution.** Opt-in `runner.workspace_mode: sealed`. Each case runs in a
fresh `<tmp>/tmpXXXXXXXX/workspace` with a private parent, holding only
`dataset.workspace.files`, the output directories and the harness settings:
no case file, no case-named path, no sibling, no project link. The harness
keeps `input.yaml` to render the prompt and for hooks. `execute.py` moves
each workspace back to `cases/<id>/workspace` for `collect.py`, and removes
the emptied root only when it held nothing but that workspace. Sealed is
rejected with batch mode and on step or agent-judge runners. The EvalHub
adapter warns that it is not applied in-pod. The default layout is
unchanged. It is a layout, not a sandbox; the docs say so and name the
follow-ups (EvalHub, Harbor, cli `{field}`).

**Tests.** `tests/test_sealed_workspace.py` drives `workspace.py` →
`execute.py` → `collect.py` with a fake agent that probes its own path,
`../`, `input.yaml`, a sibling case and settings. It covers the default
layout as a control, sealed at parallelism 1 and 2, multi-step, hooks,
in-place-edit collection, cleanup (a root that holds anything else is left
untouched) and config validation. Full suite: 2306 passed. skillsaw
`--strict` and `mkdocs build --strict` are clean.

## C4 — `chore/eval-hub-sdk-1.x` (`1bceb38`)

**Title:** `fix(evalhub): allow eval-hub-sdk 1.x`

**Problem.** The `evalhub`/`all` extras and the `agent-eval-hub` image pin
`eval-hub-sdk[adapter]>=0.1.7,<1.0`. EvalHub's server is on 1.0.x, the SDK
on 1.0.6, and every eval-hub-contrib adapter pins `~=1.0.5`, so the
harness's EvalHub adapter cannot be installed next to a current SDK (uv: "No
solution found"). While checking 1.x compatibility: the evalhub tests never
exercised the SDK. `tests/evalhub/__init__.py` (with no `tests/__init__.py`)
is imported by pytest as the top-level package `evalhub`, shadowing the SDK,
so the adapter and results mapper fell back to `agent_eval/evalhub/stubs.py`
under test, whatever SDK was installed.

**Solution.**

- Pin `eval-hub-sdk[adapter]>=1.0.6,<2` in `pyproject.toml` (both extras),
  `deploy/evalhub/Containerfile` and the container-images reference. 1.0 is
  a stability release; changes since 0.4.4 are additive, and every SDK name
  the adapter, entrypoint and evalhub runner use is unchanged. 1.0.6 raises
  the urllib3/anyio floors to patched versions.
- Remove the empty `tests/evalhub/__init__.py` so the SDK is importable
  under pytest (test basenames are unique).
- Add `tests/evalhub/test_real_sdk.py`: the pod-side path with the SDK's own
  `FrameworkAdapter` init, `JobSpec` (server-shaped job.json) and
  `DefaultCallbacks` against a fake sidecar.

No adapter code changes were needed.

**Tests.** `pytest tests/`: 2291 passed with eval-hub-sdk 1.0.6. The evalhub
tests now pass against the real SDK, 1.0.6 and 0.4.4 alike. `uv pip
compile` resolves `.[all,test]` on Python 3.11 and 3.12. `mkdocs build
--strict` passes. Not done: container build, a run against a live EvalHub
server.

## C6 — `feat/trace-adapters` (`af39c32`)

Made from `upstream/main` `9bc9a8d` (v1.56.2).

**Title:** `feat(mlflow): build /eval-mlflow traces from Codex, OpenCode and plain CLI output`

**Problem.** `/eval-mlflow log-results` builds one trace per case from
`cases/<id>/stdout.log` (`skills/eval-mlflow/scripts/log_results.py:514-540`),
and `build_trace` reads Claude Code stream-json only
(`agent_eval/mlflow/trace_builder.py:180-212`). The Codex runner stores its
raw `codex exec --json` events (`agent_eval/agent/codex.py:289-307`). So a
`codex` run gets a trace with the root span alone. An OpenCode run through
the `cli` runner (cookbook `cross-runner-opencode.md`) crashes `build_trace`
at `trace_builder.py:591`, because OpenCode's epoch-millisecond timestamps
reach the ISO parser; that aborts `log_results.py:530` after the MLflow run
was created, so no trace is linked and no feedback attached. Plain `cli`
output gets no trace. The docs said tracing needs Claude Code
(`cross-runner-opencode.md:289`, `docs/opaque-cli-runner-contract.md:146`).

**Solution.** A new `agent_eval/mlflow/trace_adapters.py` rewrites each
runner's log into the stream-json events `build_trace` already reads:

- Codex: `agent_message` becomes text, `reasoning` thinking,
  `command_execution` a `shell` tool call with its output; any other item a
  tool call named after its type.
- OpenCode: each `step_start`…`step_finish` model call gives its text,
  reasoning and tool parts in the order they started, with their times.
- Any other `cli` output: one text message, with tokens and cost from the
  run's metrics.

`build_trace` takes an optional `agent` (the runner type in
`run_result.json`), which `log_results.py` passes; the trace's `source` tag
names the format it read. Claude Code logs pass through untouched. The
tracing concept page gains an "Other runners" section, and the pages that
said tracing needs `claude-code` are corrected.

**Tests.** Claude Code and Harbor logs are pinned to the exact traces the
previous builder made; that commit passes on the old code, and the traces
stay equal whatever runner type is passed. Codex and OpenCode fixtures,
trimmed from real runs: tool spans and outputs, step grouping, timings,
session ids. The plain-text fallback, format detection, and malformed
events that must never raise. An end-to-end run of `log_results.py`
against a temporary sqlite store: a batch Codex run and a case-mode `cli`
run. `pytest tests/`: 2344 passed (baseline 2296). `mkdocs build --strict`
and skillsaw clean.

## C7 — `fix/evalhub-runner-submit` (`c0385c2`)

Stacked on C4 (`chore/eval-hub-sdk-1.x`): open it after the C4 PR lands.

**Title:** `fix(evalhub): make --runner evalhub submit, with the model URL the server requires`

**Problem.** `agent_eval/evalhub/runner.py:131,164` builds
`EvalHubClient`, which in eval-hub-sdk 1.x is `AsyncEvalHubClient`:
`jobs.submit` and `close` return coroutines that are never awaited, so the
run dies with `AttributeError: 'coroutine' object has no attribute
'resource'` before any request is sent. Past that, `runner.py:187` sends
`ModelConfig(name=model)` with an empty URL, and the server refuses it with
400 `model_url_required` (eval-hub
`internal/eval_hub/handlers/evaluations.go:319-325`). The refusal showed as
a bare `HTTPStatusError`, because the SDK logs the body only at debug
level. The docs used `url: "vertex-ai"` (`website/guides/evalhub.md:153`,
`deploy/evalhub/evalhub-job.yaml:12`).

**Solution.**

- Submit, poll and close through the SDK's `SyncEvalHubClient`.
- `--model-url`, else `EVALHUB_MODEL_URL`; no default. Without either the
  runner exits 1 before it creates anything.
- Print the server's `message` and `message_code` when it refuses a job.
- Document the flag and the variable (the EvalHub guide, the CLI and
  environment-variable references, the eval-run skill); fix the example
  job's URL and its "Submit with" path.

**Tests.** `tests/evalhub/test_runner_submit.py`, 7 tests against a fake
EvalHub on `httpx.MockTransport` that serves the server's JSON and refuses
an empty `model.url`: submit and result mapping, the URL from the
environment and the flag winning over it, the missing URL, server and
non-server refusal bodies, the CLI wiring. `pytest tests/`: 2298 passed
(baseline 2291 on C4). `mkdocs build --strict` and skillsaw clean.

## C7 — `feat/evalhub-adapter-results` (`8588735`)

Stacked on C4 (`chore/eval-hub-sdk-1.x`): open it after the C4 PR lands.
Squash `8588735` into `69fcdd2` (the parallel-cases commit fails the
YAML-reader guard alone). The first three commits (`7a8d0c4`, `6ab95ce`,
`1317145`) can be a PR of their own: without them nothing reaches the
server.

**Title:** `feat(evalhub): per-case judge results, parallel cases, run-folder export and visible failures from the in-process adapter`

**Problem.**

- `deploy/evalhub/entrypoint.py:35` built its callbacks without the job's
  `callback_url` or `provider_id`, so no status and no result reached the
  server.
- `agent_eval/evalhub/adapter.py:428` sent a metric-less terminal
  `COMPLETED` first. The server keeps the first terminal event and refuses
  the rest with 409 `job_can_not_be_updated` (eval-hub
  `storage/sql/evaluations_status.go`), so the metrics were lost.
- A crash never reported `failed`, and nothing watches the pod, so the job
  stayed `running`.
- A judge that could not load completed the job unscored
  (`adapter.py:116-119`).
- The job carried per-judge means only; `pass_rate` sat in metadata the
  SDK never sends (`results_mapper.py:108`); no per-case scores or reasons.
- Cases ran one at a time (`adapter.py:357`), though the docs promise
  `execution.parallelism`.
- The run folder was lost with the pod, even when the job asked for an OCI
  export.

**Solution.**

- Callbacks from `DefaultCallbacks.from_adapter`; the terminal event is
  left to `report_results`, which carries the metrics.
- `failed`, with the exception text, when the run raises or returns
  nothing.
- A judge that cannot load or run fails the job; a judge error on one case
  stays visible on that case.
- Per-case judge values, rationales and errors, and each case's exit code,
  as the `agent-eval.results` artifact.
- Cases in a pool of `min(parallelism, cases)`, one runner per case.
- With `exports.oci`: the local-run layout (`summary.yaml`,
  `run_result.json`, `cases/<id>/`) pushed with `create_oci_artifact`, and
  `JobResults.oci_artifact` set.
- Without `parallelism` or `exports.oci`, behaviour and metrics are
  unchanged. The guide documents the results mapping, judge errors, how
  the job ends and the export.

**Tests.** `tests/evalhub/test_pod_results.py`, 12 tests that run the real
entrypoint and SDK callbacks against a fake EvalHub keeping the server's
first-terminal-event rule: the callback URL, the stored metrics, a failed
run, an unloadable judge, a missing engine, no judges, per-case scores and
reasons, parallel cases (a barrier) and a parallel failure, the OCI export
and its reference, no export, a refused push. Two mapper tests; C4's
real-SDK test now expects no terminal event from the adapter. `pytest
tests/`: 2305 passed (baseline 2291 on C4). `mkdocs build --strict` and
skillsaw clean.

## C8 — `feat/anova-runner-factor` (`8f0918e`)

Made from `upstream/main` `9bc9a8d` (v1.56.2).

**Title:** `feat(eval-anova): runner as a matrix factor; reject factors the cli runner shadows`

**Problem.** Only `model`, `effort` and `subagent`/`subagent_model` reach
the runner (`skills/eval-anova/scripts/orchestrate.py:58-60`,
`references/matrix-schema.md:31-39`); every other factor becomes an
`--input-override`. All four eval-run steps get the same `--config`
(`orchestrate.py:162-180`), so `runner.type` is fixed for the whole matrix
and agents cannot be compared in one. `CliRunner.execute` adds input
fields only `if k not in placeholders`
(`agent_eval/agent/cli_runner.py:102-124`), so a factor named `agent`,
`workspace`, `timeout` or another built-in placeholder is silently
shadowed, and every level runs the same command.

**Solution.**

- A `runner` factor: its levels are runner types, or names of blocks under
  a new `matrix.runners`, which carry a level's own settings (an OpenCode
  `cli` command, for example).
- Each such cell runs under `runner.yaml`, an `extends:` profile of the
  eval config with the level's runner block: mappings merge, scalars win,
  lists the level sets replace. The run's `config_chain` records it.
- Workspace and execute run under the profile; collect and score keep the
  eval config, so every cell is judged the same way.
- Every level's config is loaded and its runner built before the first
  cell runs, and under `--dry-run`, which prints each level's runner type.
- When a cell runs the `cli` runner, strict parsing rejects a factor named
  after a built-in placeholder; for `agent` the message points at the
  `runner` factor. The set is `cli_runner.BUILTIN_PLACEHOLDERS`.
- A matrix without a `runner` factor runs as before.

**Tests.** `tests/test_anova_runner_factor.py`, 30 tests: level resolution
and parse errors, the placeholder rules with and without a `cli` cell,
`BUILTIN_PLACEHOLDERS` pinned to the runner's own placeholder dict, the
per-cell profile and the list-replace merge, the dry-run refusing a level
the config cannot run, and an end-to-end run through the real eval-run
scripts with two `cli` levels, each running its own command. `pytest
tests/`: 2326 passed (baseline 2296). `mkdocs build --strict` and skillsaw
clean.

## C8 — `feat/anova-cell-reuse` (`5550792`)

Stacked on `feat/anova-runner-factor`: the reuse key hashes the per-cell
runner block, and both rewrite `fan_out`. C37 added `5550792` on the first
version, `5b5a3de` (2026-10-15).

**Title:** `feat(eval-anova): reuse a finished cell instead of running it again`

**Problem.** The run id is the date plus the levels
(`skills/eval-anova/scripts/orchestrate.py:111-123`), and `fan_out` runs
every cell on every call (`orchestrate.py:192-244`). Nothing records what
a run measured, so adding a level or a replication, or going on after a
crash, pays for the whole matrix again.

**Solution.**

- Each cell gets a recipe, a SHA-256 over:
  - the harness code the cell runs: the four eval-run step scripts, every
    `agent_eval` module or sibling script they import (read off their
    import statements, recursively, a deferred import included), the
    builtin judges, `tools.py` and `orchestrate.py`;
  - the cell's resolved config (`extends:` and the runner level merged,
    every key but `matrix`);
  - its factor levels;
  - every file in each case's dataset directory.

  An edit to that code re-runs every cell. An edit elsewhere (the
  analysis, `report.py`, Harbor, EvalHub, the docs), or a release that
  changes none of it, does not.
- The recipe and the replication are stamped into `condition.json` only
  after all four eval-run steps succeed.
- A cell whose recipe and replication match a finished run is skipped, and
  that run reused; `--force` re-runs every cell.
- `--dry-run` reports `Reused: N of M cells` and estimates the rest only.
- A restarted cell loses its stamp until it finishes again.
- Not hashed: files the config only points at (the skill under test,
  `plugin_dirs`, prompt files), the agent CLI's version and the installed
  packages' versions. The docs say so, and say to use `--force` after
  changing them.

**Tests.** `tests/test_anova_reuse.py`:

- reuse, `--force` and the stamp; only the new replications or the new
  level run;
- changes that must not re-run a cell (analysis settings) and changes that
  must (judges, arguments, effort, case files, a case subset, a runner
  block);
- failed and restarted cells; two identical runner blocks under two names;
  the dry-run count and estimate; old stamps without a recipe;
- an end-to-end run through the real eval-run scripts, called twice: 2
  runs, then 0;
- the code digest: a code change re-runs, a version change alone does not;
  edits on a fake plugin tree that must and must not change it; the real
  cell-code file set (57 files on the branch, 63 on
  `flywheel-integration`, about 0.1 s).

`pytest tests/`: 2366 passed for the branch. `mkdocs build --strict` and
skillsaw clean.

**Points a reviewer can raise.**

- The import walk is static: a module loaded by a string name is missed,
  which is why `agent_eval/judges` and `tools.py` are listed by hand.
- The walk reads `agent_eval` from the plugin tree, which is where the
  scripts import it from (`agent_eval/_bootstrap.py`: the venv holds only
  third-party packages).
- Any edit to `config.py` or a runner re-runs every grid.
- `thresholds` are in the recipe here. On this branch alone, a cell that
  misses a threshold fails, is never stamped, and re-runs every time; C34
  fixes that.
- A forced re-run on another day adds a run instead of replacing one, and
  the analysis pools both as replications.

On `flywheel-integration` (`b62f9da`), with C34's threshold fix: a cell
that misses a floor finishes, so it is stamped and reused (a test through
the real eval-run scripts: 2 cells run, then 0), and `thresholds` leave
the recipe beside `matrix` (`_NOT_IN_RECIPE`), because a cell only reports
a missed floor (a test: a threshold change re-runs nothing). C19's
`resolve_dataset` in `_cell_recipes` stays.

## C9 — `feat/optimize-no-verify` (`5641025`)

Made from `upstream/main` `9bc9a8d` (v1.56.2): `8079ebc`, `97817e7`, and
C39's `5641025` (2026-10-15). Clear of #73 (astefanutti's optimize
rewrite, the only open optimize PR): the default loop gets two table rows,
one routing paragraph and one Step 2 bullet, and the mode lives in new
files. If both land, the Step 0 table takes both sets of rows, and one
line says `--strategy` has no effect with `--no-verify`.

**Title:** `feat(eval-optimize): add --no-verify, one proposed edit for a caller that scores it`

**Problem.** `/eval-optimize` always verifies its own edits: Step 1 runs
`/eval-run` when no results exist (`skills/eval-optimize/SKILL.md:44-52`),
Step 5 re-runs it with `--baseline` (`:142-154`), and Step 6 keeps or
reverts (`:167-174`), for up to `--max-iterations` (`:20`), with
`AskUserQuestion` among its tools (`:5`). A caller that scores edits itself
(a training loop with a held-out set, a CI job) cannot ask for one proposal
and keep the decision; today it copies the skill, rewrites its
`allowed-tools` and prompts it to skip Steps 1 and 5.

Separately, Step 2's failure map lists the judge types as `builtin`,
`check`, `llm`, `code` (`:82`), though `score.py`'s `load_judges` also
gives `agent` (`:2658`). So the loop has no advice for an agent judge's
failure, and the new mode's no-change call ("a judge that looks wrong")
rests on that list.

**Solution.**

- `--no-verify` reads a run that is already scored (`--run-id`, as-is) and
  the artifact under test (`--artifact`, a file or a directory; by default
  the skill's `SKILL.md`), runs Steps 2 to 4 once, makes one edit or none,
  and stops: no `/eval-run`, no keep or revert, no `AskUserQuestion`. A
  missing input is an error, not a question.
- The procedure is in `references/no-verify.md`; the default loop's
  behaviour is unchanged.
- `scripts/proposal.py` writes `<run dir>/proposal.json` (`status`,
  `run_id`, `artifact`, `file`, `hypothesis`, `change`, `judges`, `cases`).
  It refuses a judge or case that is not in `summary.yaml` and a file
  outside the artifact (symlinks resolved), exits 2 and writes nothing.
  The format is documented in the skill reference and in
  `website/reference/runs-directory.md`.
- Step 2 lists `agent`, inline and as a bullet, as the guide's table
  already does.

**Tests.** `tests/test_eval_optimize_no_verify.py`, 18 tests: the skill
text contract (the flags in Step 0, the route before Step 1, the `## Never`
rules, every `${CLAUDE_SKILL_DIR}` path resolves, the documented keys match
the script's output, and Step 2's judge types equal the `judge_type`
values `load_judges` assigns, which fails before the change) and
`proposal.py` (a valid write, a file created in a directory artifact,
`no-change`, three ways to lie outside the artifact, an unknown judge or
case, a missing case, `--no-change` with `--file`, an unscored run, the
script run by path). `pytest tests/`: 2315 passed for the branch, 4
skipped, 2 deselected (baseline 2296). skillsaw strict and `mkdocs build
--strict` clean. Not tested: what a model does with the text; no model
calls were made.

**Points a reviewer can raise.**

- The judge-type check reads `score.py` with `ast`, not by running
  `load_judges`: a refactor that stops assigning `judge_type` as a literal
  fails it loudly.
- `eval-review`'s `SKILL.md:42` and its guide sort judges into
  deterministic and qualitative and name neither `agent` nor `code`; that
  skill is out of this PR.
- `--no-verify` makes one edit per call; a caller that wants several calls
  it several times.

## C30 — `fix/mlflow-traces` (`a05e61e`)

Made from `upstream/main` `9bc9a8d`; 14 commits, C30's and spec 02's C35
(2026-10-15). Meets C6 (see "The order matters").

**Title:** `fix(eval-mlflow): traces MLflow 3.5.0 can store, one per case or step, each with its own run and feedback`

**Problem.**

- `log_results.py` imports `AsyncExportQueue`, which no supported MLflow
  has, so the flush before linking and feedback is a no-op; on a sqlite
  store (MLflow 3.17.1) every case-mode run failed both, the link with
  `FOREIGN KEY constraint failed`, the feedback with `Trace … not found`.
- Case entries have no `model`, so LLM spans carry no model and no cost.
- The trace builder writes span status `STATUS_CODE_OK`, which MLflow
  3.5.0 (the package's floor) rejects, so no built trace logs there.
- A tool result without a timestamp (all of Harbor's) loses its output.
- log_results reuses any unlinked trace whose `eval_run_id` is a case id.
  Case ids repeat across runs, so another run's trace took this run's link
  and feedback. It also read at most 500 traces.
- A multi-step case got one trace, from its last step's log, with the
  whole case's cost on it.
- Every log warned `download_artifacts failed`: the snapshot search found
  the run being logged.
- On 3.5.0 every flush logged an ERROR.
- `find_run_traces` ignored its run id, window and cap, and iterated the
  DataFrame `mlflow.search_traces` returns, so `attach_feedback.py` found
  no trace on any MLflow 3, in push and in pull mode. Had it found any, it
  would have put every case's feedback on every trace.
- A case without a trace got the first case's trace in log_results.
- A reused Harbor step trace got no step routing.
- A re-logged batch run got a second trace.

**Solution.**

- Flush through `mlflow.flush_trace_async_logging()`, inside
  `trace_builder.flush_traces()`, which drops only 3.5.0's two "no queue"
  ERRORs.
- A case entry without a model takes the run's; `execute.py` records each
  case's and each step's model.
- Span status `OK`; tool output is kept without a timestamp.
- Every trace log_results builds carries `harness_run_id`; only the run's
  own unlinked traces are reused, from every page, in case, Harbor and
  batch mode.
- One trace per step (`<case>/<step>`), from the step's own log and
  metrics. A step judge's feedback goes to its step's trace, any other to
  the last step's.
- The snapshot search leaves out the run being logged.
- `find_run_traces` pages with `MlflowClient` and keeps the run's traces:
  its `harness_run_id`, or, for older traces, a batch trace's
  `eval_run_id` or a link to an MLflow run named after the eval run.
- `attach_feedback.py` routes each case's feedback to that case's trace,
  by the same rule as log_results (`traces.step_trace_for`); a case with
  no trace gets none.
- The tracing and eval-mlflow pages say so.

**Tests.** `tests/test_log_results_sqlite.py` runs `log_results.py`
against a temporary sqlite store: a two-case run (no warnings, every trace
linked, each with its feedback, model and cost on the LLM spans), a re-log
beside another run's trace with the same case id, a multi-step case, a
case with no trace, a reused Harbor step, a re-logged batch run.
`tests/test_attach_feedback_sqlite.py` pushes and pulls feedback for one
of three runs in one experiment; `tests/test_mlflow_traces.py` tests
`find_run_traces` on sqlite; unit tests for the flush filter, the span
status, the untimed tool output and the per-step model. `pytest tests/`:
2335 passed (baseline 2296); the MLflow-facing tests also pass on MLflow
3.5.0 (214). skillsaw and `mkdocs build --strict` clean.

**Points a reviewer can raise** (from the subagent's report):
`experiment.py` `log_feedback` swallows every exception and
`attach_feedback.py` counts each entry as attached anyway; every step
trace gets the run-level `runner_type`, since `run_result.json` records
no runner per step.

## C31 — `fix/evalhub-pod` (`a44eb8b`)

Made from `upstream/main` `9bc9a8d`: C31's commits up to `04d184e`, then
C38's round on top (spec 02): `e708405` (annotations), `6d8a824` (timeout
and budget), `a5e067b` (`_modified/`), `60d4c35` (Harbor's verifier),
`26edf11` (docs), `a44eb8b` (the agent's workspace). Meets C7 in
`adapter.py` and `runner.py`, C19 in `score.py`, `adapter.py` and
`workspace_files.py`, C3 in `workspace.py` (see "The order matters";
merged in `flywheel-integration` `392baca`).

**Title:** `fix(evalhub,harbor): score pod and verifier cases as a local run does; bound the runner's job wait`

**Problem.**

- `agent_eval/evalhub/adapter.py:116` calls `score_cases` without a run
  id, and nothing in the pod wrote `stdout.log`, `events.json` or
  `run_result.json`, so `load_case_record`
  (`skills/eval-run/scripts/score.py:316,428`) gave every judge an empty
  record: a judge on `outputs["exit_code"]` got its default, 1, on every
  case; turns, cost, stdout, stderr and the conversation were missing.
  Under an OpenRouter plan the pod also scored before the run's end, with
  each case's cost still pending.
- The rest of a judge's record differed from a local run's too.
  `score.py:224-226` reads annotations only from `dataset.path` beside
  `eval.yaml`, while the pod's cases arrive from S3 or a ConfigMap in its
  temp folder, so its judges saw none. `adapter.py:375-376` ran each case
  with `timeout or 600` and `max_budget_usd or 5.0`, not the documented
  3600 s and 100 USD (`website/concepts/execution-model.md`,
  `execute.py:524,527`), and a deliberate `0` became the default. The pod
  took no git snapshot, so `_modified/` never reached its judges, and
  `score.py:293-296` read a `_modified/` the agent had written itself.
- The pod ran each agent in its case folder as delivered
  (`adapter.py:358,384`), beside `annotations.yaml` and every other file of
  the case. A local run gives its agent only the input file,
  `answers.yaml`, the listed `workspace.files`, the shared files and the
  output dirs (`skills/eval-run/scripts/workspace.py:242-269`), so in the
  pod an agent could read its answer key.
- Harbor's verifier (`agent_eval/harbor/templates/test.sh.tmpl:9-11`)
  writes `stdout.log` but no `run_result.json`, so `reward.py:222-226` gave
  its judges the default exit code and no turns or cost, and its `cat >`
  wrote through a link the agent planted.
- `agent_eval/evalhub/runner.py:125,277`: `--timeout` defaults to `None`,
  so the runner polls forever on a job that never ends (EvalHub sets no
  deadline), and a given timeout escaped as a traceback without the job's
  state.

**Solution.**

- The adapter leaves what a local run leaves: each case's `stdout.log`,
  `stderr.log`, `events.json` and `run_result.json`, and the run's
  `run_result.json` with `per_case`. It replaces a file the agent planted
  there rather than writing through it.
- `score_cases` takes `runs_dir` and `dataset_dir` and passes them to
  `load_case_record`; the defaults are unchanged.
- Under a plan, the pod closes the run before its judges score it.
- The per-case part of `workspace.py` moves into
  `agent_eval/workspace_files.py` (`provision_case_workspace`, with the
  copier `workspace_files.py` held), called by `workspace.py` and by the
  pod. The pod keeps the delivered cases in `<tmp>/dataset`, where its
  judges read annotations and the files they name, and builds each
  agent's workspace in `<tmp>/cases/<id>` before its git snapshot. A
  shared file `export_dataset` packaged into a case is taken from there
  (`materialize_shared_files(packaged_in=)`), without following a link.
- `ExecutionConfig.guardrails()` resolves timeout and budget for
  `execute.py` and the pod alike: flag, `eval.yaml`, then 3600 s and
  100 USD, a `0` kept.
- `agent_eval/workspace_changes.py` holds the git snapshot and the
  `_modified/` collection, moved out of `workspace.py` and `collect.py`.
  The pod snapshots each case's workspace once built, before its agent,
  and collects after, replacing whatever the agent left at `_modified`;
  without git it warns and scores without `_modified/`.
- Harbor's verifier writes the case's and the run's `run_result.json` from
  the transcript (exit code from its final event, turns, tokens, cost) and
  `events.json` when traces are on, reading no ledger from the workspace;
  `test.sh` removes `stdout.log` before writing it.
- The runner waits up to 7200 s by default, `--timeout 0` for no limit;
  on a timeout it exits 1, naming the job, its last state and the server's
  message. The job keeps running on the server.
- Docs: the EvalHub and Harbor guides, execution-model, runs-directory,
  the dataset reference.

**Tests.** `tests/evalhub/test_pod_scoring.py`: exit code, turns, stdout,
stderr and conversation reach the judges; the file layout matches a local
run's; `traces.events: false`; a planted symlink is not written through;
the settled cost under a plan; `score_cases(runs_dir=)`; annotations from
S3 and a ConfigMap, unchanged by an agent that edits its workspace,
`score_cases(dataset_dir=)`; an agent that lists its working directory
finds no `annotations.yaml` or gold file, while the judges still see them;
listed and packaged shared files reach it; a local run and the pod give
the agent the same files; the guardrails' defaults, values and `0`;
`_modified/` from the agent's edits, an agent-made `_modified/` replaced,
a planted link, the same record as a local `workspace.py` → `execute.py`
→ `collect.py` → `score.py` run, a pod without git. They pass on the
stubs and on the real SDK 0.4.4 and 1.0.6. `tests/evalhub/test_runner_wait.py`,
with a fake SDK module: the default bound, a timeout, `0`, an unreadable
last state, the CLI defaults. `tests/test_config.py` (guardrails),
`tests/test_workspace_changes.py`, `tests/test_input_files.py`
(`packaged_in`), `tests/test_harbor_reward.py` (claude-code and codex
transcripts, no final event, a planted `run_result.json` and ledger,
`test.sh`). `pytest tests/`: 2341 passed (baseline 2296). skillsaw and
`mkdocs build --strict` clean.

**Points a reviewer can raise.**

- The pod's default per case goes from 5 USD to the documented 100 USD,
  and its timeout from 600 s to 3600 s.
- The pod's agent now gets only the files a local run's gets: a case file
  not listed in `dataset.workspace.files` no longer reaches it.
- The delivered cases stay at `<tmp>/dataset` in the pod, reachable by
  path, as the dataset is in a local run; `runner.workspace_mode: sealed`
  is still not applied in the pod.
- With `packaged_in`, a shared file the case holds wins over its source.
- `workspace_files` moves from `skills/eval-run/scripts/` into
  `agent_eval/`, imported as `agent_eval.workspace_files`; one
  parametrized case of `test_venv_activation` goes with it.
- Harbor's exit code is inferred from the transcript's final event: none
  gives `None`, so the judge's default; codex `error` events can be
  transient, so the last final event wins.
- A pod without git warns instead of failing the job, and the pod
  replaces an agent-made `_modified/` rather than refusing the case.
- Harbor's judges still get no annotations (the bundle sets
  `dataset.path: ""`), no `_modified/`, and no per-case listed
  `workspace.files` (`agent_eval/harbor/tasks.py:395-407, 540-547`).
- `guardrails()` changes `execute.py`'s code but not its behaviour.
- Harbor writes `run_result.json` with an empty ledger: a ledger in the
  workspace would be the agent's, not the harness's.
- `pass_rate` is not touched here: on `9bc9a8d` `results_mapper.py:108`
  puts it in `metadata`, which the SDK drops; the results PR (C7) sends it
  in the `agent-eval.results` artifact, and its `metadata` line is dead.

## C32 — `fix/cost-figures` (`a605864`), two PRs

Made from `upstream/main` `9bc9a8d`: C32's four commits, then C36's round
on top (spec 02). PR A is `754b037`, `3480586`, `4e21613`, `d811aca`,
`ad48cdc`, `0f86b73`, `215bb08`, `d5f037b`, `a605864`; PR B is `e244129`
and `50f9058`, and meets C2 (see "The order matters"; merged in
`flywheel-integration` `986153c`). Each PR applies alone onto `9bc9a8d`
(checked with `git merge-tree`); B then A gives the branch's tree. Within a
PR, `ad48cdc` needs `d811aca`, `50f9058` needs `e244129`, `a605864` needs
`3480586`. Each new commit body ends with a "Part of PR A/B" line: strip
it before opening upstream.

**PR A — Title:** `fix: keep cost figures exact and labelled, and the fable alias and OpenCode token counts intact`

**Problem.**

- `skills/eval-run/scripts/execute.py:2055` rounds the case-mode run
  `cost_usd` to cents: two cases at $0.002 record `0.0`, and MLflow's
  `cost_usd` metric, logged only when truthy, disappears. `:1101` rounds a
  multi-step case's cost to 4 decimals and counts a step without a cost
  as 0; `:2016` rounds the plan run's estimate to 4 decimals.
- `RunResult.cost_usd_estimate` is dropped by the case (`:1241-1258`,
  `:1432-1450`), step and batch (`:2130-2152`) results and by
  `agent_eval/evalhub/adapter.py:205`; only reconcile writes it, under a
  plan.
- A case-mode run without a plan has no run-level `cost_source`, so a run
  of `runner:estimate` cases reads as `runner:reported` in `compare.py:133`
  and `analyze.py:606`.
- `eval/opencode-smoke/scripts/run-opencode.sh:73-88` writes `input =
  tokens.input + cache_read` and a `cache_write` key, but OpenCode's
  `tokens.input` is already uncached and the harness reads cache writes as
  `cache_create` (`report.py:1307`, `score.py:4024`,
  `trace_builder.py:1089`, `log_results.py:357`), so cache reads count
  twice and cache writes are lost; it also drops `tokens.reasoning`, which
  OpenCode reports apart from output (since its PR #21047) and Claude Code
  and Codex count in output.
- The cli contract (`docs/opaque-cli-runner-contract.md:12-24, 54, 72`,
  `website/concepts/runners.md:333-372`) shows `token_usage` as
  `{input, output}`, never says `input` is uncached, and omits
  `{config_dir}` (`cli_runner.py:34`).
- `fable` is missing from the `agent_eval/agent/claude_code.py:802-826`
  allowlist (the plan sets `ANTHROPIC_DEFAULT_FABLE_MODEL`,
  `agent_eval/providers/env.py:30-33`), from `prompt_backends.py:23` and
  from `scripts/ensure_deps.py:248`, so without a plan a host mapping of
  the fable alias never reaches the CLI, and a `fable` judge goes to the
  OpenAI SDK.

**Solution.**

- The run total and a multi-step case's total are exact to 6 decimals, as
  reconcile writes; only the `COST:` line rounds to cents. A multi-step
  case with a step of unknown cost is `null` with `unavailable` (spec
  014's null-cost arithmetic: a partial sum is not spend).
- A total carries its entries' label: the one they share, else the first
  estimate among them; at run level `runner:reported` is left out, so a
  plain run reads as before.
- Every result keeps `cost_usd_estimate`; a multi-step case and a
  case-mode run sum their entries' estimates, plan or not.
- The wrapper writes `input` as OpenCode reports it, `cache_create`, and
  `output` plus `reasoning`; the cookbook says what `input` means.
- The contract and `runners.md` say what each token key counts (`input`,
  `cache_read`, `cache_create`, `output`) and list `{config_dir}`.
- `fable` joins the env allowlist and routes to the Anthropic SDK.

**Tests.** End-to-end runs through `workspace.py` and `execute.main` with
the `cli` runner and with the fake `claude` behind a gateway URL; a
multi-step case with an unpriced step; a structural check that every
result dict keeps the estimate; the wrapper against a fake `opencode`
event stream, with reasoning; an allowlist test that reads the alias slots
from the plan's own env block, and alias routing derived from them; a doc
test that runs the runner against both placeholder tables. `pytest
tests/`: 2342 passed for the branch. skillsaw and `mkdocs build --strict`
clean.

**Points a reviewer can raise.**

- Without a plan the run total is still a partial sum when a case has no
  cost, as upstream's `test_run_cost_aggregate_preserves_unknown_cost`
  pins, unlike spec 014's table.
- When two estimate labels mix, the first one wins.
- OpenCode up to 1.3.15 counted reasoning inside `output`, so with those
  versions the wrapper counts it twice.
- Landed alone, this PR leaves the Cost Provenance row in `report.md` and
  the "In the report" paragraph in `providers.md` stale until PR B.

**PR B — Title:** `fix(codex): label the runner's cost: unavailable behind a gateway, harness:estimate for litellm's figure`

**Problem.** `agent_eval/agent/codex.py:590-592` prices a run by looking
its model name up in `litellm.model_cost`. Behind a gateway the name is an
alias the operator chose; a name that matches a litellm key (`gpt-5`,
`cerebras/gpt-oss-120b`) gets that model's list price whatever was served,
a wrong figure that looks right, which `cost_budget` then judges. On
OpenAI's API the figure carries no label and reads as `runner:reported`,
although spec 014 (`spec.md:422`) names it `harness:estimate`; when
litellm cannot price the run, the null is unlabelled too. The report's
`unavailable` banner (`skills/eval-run/scripts/report.py:1079-1081`)
always named the OpenRouter sources.

**Solution.**

- When codex does not talk to OpenAI's API (a `model_provider` other than
  `openai`, or an `openai_base_url` / `OPENAI_BASE_URL` host other than
  `api.openai.com`, hook env included), the runner returns `cost_usd:
  null` with `cost_source: unavailable`.
- On OpenAI's API litellm's figure is `harness:estimate`, or `unavailable`
  when litellm cannot price the run.
- A run reconcile never touched gets its own banner, naming the model and
  the endpoint.
- Runners, providers, report, runs-directory and environment-variables
  pages updated.

**Tests.** Five gateway set-ups, the hook env and the timeout path give
`unavailable`; three OpenAI-API set-ups and an OpenAI-API timeout give
`harness:estimate`; litellm absent or the model unknown gives
`unavailable`; the banner for a run without a plan.

**Points a reviewer can raise.**

- A model litellm does not know now shows a red banner.
- Harbor's own Codex agent prices the same way; out of scope here.
- With C2, whichever lands second takes `flywheel-integration`
  `986153c`'s `_cost`.

On `flywheel-integration` (`986153c`): C2's two tests of the no-price path
on OpenAI's API now assert `unavailable` and `harness:estimate`; the
gateway cookbook's codex row, stale since C32's first merge, is fixed in
the merge commit, while the `docs/gateway-recipes` branch keeps the old
text.

## C33 — `fix/stop-handlers` (`ce6eca8`)

Stacked on C1 (`fix/stop-on-sigterm`, from `175eed5`): open it after the
C1 PR lands. Commits: `dec86ed`, `1065af1`, `7e59702`, and C39's
`f49f329`, `603b2ce`, `ce6eca8` (2026-10-15).

**Title:** `fix: stop every agent and running hook when any harness process is stopped`

**Problem.** C1 makes a stopped `execute.py` stop its agents. Every other
process that starts an agent or a hook in a process group of its own
leaves it running:

- `score.py` runs agent judges and runner-backed LLM judges through the
  CLI runners (`skills/eval-run/scripts/score.py:3212`,
  `agent_eval/prompt_backends.py:309`), each in a process group of its own
  (`agent_eval/agent/process_group.py:53`), and installs no stop handler
  (`:4289`). SIGTERM, SIGHUP and SIGKILL leave the judge's agent running.
  Ctrl-C reaches `score.py` alone, and `score_cases` leaves its pool
  through the `with` block (`:2657`), which first scores every queued
  case.
- The EvalHub provider runs cases and judges in-process, and
  `deploy/evalhub/entrypoint.py:63` installs no handler: EvalHub's local
  runtime cancels with `Kill(-pid, SIGKILL)` to the provider's group
  (eval-hub `internal/eval_hub/runtimes/local/process_unix.go:12`), which
  the agents are not in. On Kubernetes the provider is the container's
  PID 1, which gets no signal it has no handler for.
- The synthetic case generator (`skills/eval-dataset/scripts/generate_synthetic.py:329,537`,
  runner-managed models) and the Harbor verifier
  (`agent_eval/harbor/reward.py:226,493`, agent judges) install no
  handler.
- Lifecycle hooks start in sessions of their own and are killed only at
  their timeout (`agent_eval/hooks.py:133-145`). A run stopped while a
  hook runs, from `execute.py`, `score.py`, `report.py` or the hooks CLI,
  leaves the hook and its children running; in a parallel run, the stop
  waits for every running `before_each` up to its timeout.

**Solution.**

- `score.py`, `entrypoint.py`, `generate_synthetic.py`,
  `harbor/reward.py`, `report.py` and `python -m agent_eval.hooks` install
  `process_group.install_stop_handler()` at their script entry, as
  `execute.py` does: a SIGTERM/SIGHUP handler and a SIGKILL watchdog.
- `score_cases` leaves its pool as `execute.py`'s parallel loop does: it
  cancels the queued cases, kills the running judges' groups and
  re-raises.
- Hooks start through `process_group.popen_hook`, so `stop_all()`, the
  handler and the watchdog reach a running hook, and Ctrl-C or an
  exception kills it on the way out. A hook that ended is only untracked
  (`forget`): what it left running (a fake API server for `after_all` to
  stop) stays, as before.
- The `after_*` hooks (`run_hooks_safe`) still start once the run is
  stopping; any other hook is refused, as a new agent is. The stop notice
  counts hooks apart from agents.
- No new machinery. The runners page's "Stopping a run", the
  lifecycle-hooks page, the hooks reference, the agent-judge docs, the
  EvalHub guide and the cli runner contract are updated.

**Tests.** `tests/test_stop_agents.py`, with a fake agent and a fake hook
that each start a child:

- SIGTERM to `score.py` with an agent judge on `cli`, `codex` and
  `claude-code`; SIGTERM, Ctrl-C and SIGKILL with two judges, and no
  second judge starts; Ctrl-C cancels the cases not yet scored.
- SIGTERM and group-SIGKILL to `entrypoint.py` while a case's and a
  judge's agent run.
- A running hook stopped by SIGTERM (`execute.py` `before_all`, `score.py`
  `before_scoring`, `report.py` `before_report`), by Ctrl-C and by SIGKILL
  (`execute.py` `before_each`); a stopped parallel run still runs
  `after_each` and `after_all` and starts no queued hook; once stopping, a
  before hook is refused and an after hook runs; a hook that ended keeps
  its child.
- SIGTERM and SIGKILL to `generate_synthetic.py` and to `python3 -m
  agent_eval.harbor.reward`.

22 of the PR's 23 new tests fail before the change (the finished-hook
guard passes by design). `pytest tests/`: 2326 passed for the branch (C1's
head 2303); the 37 stop tests 3 of 3 runs. skillsaw and `mkdocs build
--strict` clean.

**Points a reviewer can raise.**

- A hook that exited keeps its background children, as before. If the
  harness is SIGKILLed, `after_all` never runs, so such a service stays:
  the watchdog knows only running hooks.
- `report.py` and the hooks CLI now keep a watchdog process for their
  lifetime, as `execute.py` and `score.py` do.
- `process_group._live` is now a dict (process to kind); `popen_hook` and
  `forget` are new.
- The stop notice changes its wording when hooks were running.
- `before_report` goes through `run_hooks_safe`, so it would start while
  stopping; nothing runs it on the way out.
- Hook `condition:` commands are not tracked (30 s limit).
- In a Harbor trial the container's teardown ends the verifier anyway, and
  `test.sh` runs `python3` as a child of bash, which forwards no signal:
  the handler matters for a verifier run outside a container, or signalled
  itself.
- `prompt_backends.run_prompt_via_runner` still leaves its
  `prompt-backend-*` workspace behind on a stop.
- C7's EvalHub thread pool gets `stop_all()` from whichever of C1 and C7
  lands second.

On `flywheel-integration` (`2c55f55`): C37's `find_input_file` import
and this branch's `process_group` import meet in `hooks.py`; both stay,
and a test runs the hooks CLI on an `input.json` case, which the hook
sees as `CASE_INPUT` and SIGTERM stops. C38's `harbor/reward.py` merged
without a conflict, and the verifier stop test runs C38's
`write_case_run` path.

## C34 — `fix/anova-cells` (`a4545ce`)

Made from `upstream/main` `9bc9a8d`: C34's first round (`7931dca`) and
C37's seven commits on it (2026-10-15). It merges into
`flywheel-integration` with conflicts against C3, C8, C19, C35 and C38,
resolved in `1a2f2bc`.

**Title:** `fix(eval-anova): make every cell run its own levels and count its result`

**Problem.** `/eval-anova` passes every factor but `model`, `effort` and
`subagent` to eval-run as `--input-override`. Between that and the
analysis, a cell can run something other than what its levels say, or
lose its result:

- `execute.py` merges overrides only in case mode
  (`skills/eval-run/scripts/execute.py:1815-1822`) and only into
  `input.yaml`. The batch path (`:559-617`) ignores them, and so do cases
  whose input is `input.yml` or `input.json`, which `workspace.py:567-573`
  accepts.
- An override that cannot land (no file, a symlink, a value that is not a
  mapping) does nothing, in silence (`_merge_input_overrides`,
  `:1778-1780`).
- Placeholders are filled only from `input.yaml`: the three case paths
  (`:1153`, `:1300`, `:1478`), `CASE_INPUT` (`:1336`, `:1517`;
  `agent_eval/hooks.py:323`) and `{field}` in the cli runner
  (`agent_eval/agent/cli_runner.py:117`). `_enumerate_cases` skips the
  other cases entirely (`skills/eval-anova/scripts/orchestrate.py:89-97`).
- Run ids collide:
  - `_safe_id_segment` maps `a/b` and `a_b` to one id
    (`agent_eval/anova/matrix.py:179-182`);
  - `{x: a-y-b, y: c}` and `{x: a, y: b-y-c}` give one id
    (`orchestrate.py:111-123`);
  - every workspace sits at `<tmp>/agent-eval/<run-id>`
    (`workspace.py:89-95`), so two evals started with one run id delete
    each other's workspace, and `--run-id .` deletes all of them.
- The log line (`orchestrate.py:223`) and the guide row
  (`website/guides/eval-anova.md:166`) promise placeholders that batch
  mode does not fill.
- `score.py judges` exits 1 when a threshold is missed (`score.py:4188`),
  so a low-scoring cell is dropped (`orchestrate.py:155`), and the
  analysis pools what is left as a single `{model}` condition: the factor
  leaves the ANOVA.

**Solution.**

- **Overrides:** batch mode merges them into every `batch.yaml` entry
  before `{prompt}` is resolved. Case mode merges them into the case's own
  input file, and JSON stays JSON. A batch entry or a case the override
  cannot land in stops the run before any agent starts, naming each case.
- **Input files:** a new `agent_eval/case_input.py` finds and reads the
  input file in `workspace.py`'s order. Every placeholder reader,
  `CASE_INPUT`, the copy in the run record and `_enumerate_cases` use it.
- **Run ids:**
  - `_safe_id_segment` keeps every value that already is a valid segment;
    any other value is cleaned and gets 8 hex digits of its SHA-256
    (`a/b` → `a_b-c14cddc0`);
  - a cell whose run id reads more than one way gets 8 hex digits of its
    condition id; every other run id is unchanged;
  - a factor with two levels that reach the run as the same text (`1` and
    `"1"`, or one level twice) is refused in strict mode.
- **Workspaces:** each lives at `<tmp>/agent-eval/<eval-name>/<run-id>`,
  and `--run-id .` is refused.
- **Thresholds:** a new `--no-fail-on-regression` flag on `score.py
  judges` reports a missed floor and exits 0. Orchestrate passes it; the
  CI gate is unchanged.
- **Docs:** the log, the guide, the matrix reference and the hook, runner
  and dataset docs say where an override lands and how run ids are made.

**Tests.**

- `tests/test_input_overrides.py` runs the real `workspace.py` and
  `execute.py` with a `cli` runner: batch and case mode; `.yaml`, `.yml`
  and `.json` inputs; `{name}`, brace and Jinja placeholders; multi-step
  and in-repo prompt cases; `CASE_INPUT`; the record copy; an end-to-end
  `/eval-anova` batch cell. A parametrized test covers each refusal.
- `tests/test_case_input.py`: 13 tests.
- `TestSafeIdSegment`, `TestDistinctLevels`, the collision cases, and an
  exhaustive test over 13 awkward level values: no two cells share a run
  id.
- `tests/test_workspace_dir.py`: two evals with one run id; `.` and `..`
  refused.
- `tests/test_anova_thresholds.py`: the gate still exits 1, the flag exits
  0, and a fan-out where one cell misses a floor keeps both cells and both
  levels.
- `pytest tests/`: 2369 passed for the branch (baseline 2296). skillsaw and
  `mkdocs build --strict` clean.

**Points a reviewer can raise.**

- The new workspace path breaks a script that hardcodes
  `<tmp>/agent-eval/<run-id>`. `specs/006-execution-hooks/spec.md:111`
  still names it for `AGENT_EVAL_WORKSPACE`; the spec is left as written.
- Refusing an override that cannot land changes the old no-op; the pinned
  helper test changes for that reason.
- `--no-fail-on-regression` is a new public flag.
- Run ids can still collide: levels that differ only in letter case, on a
  filesystem that ignores case; across matrices with different factor
  sets; and through the `-r<n>` suffix.
- Two configs with the same eval name share one runs directory and one
  workspace folder.
- Some readers still see only `input.yaml`: `{{ inputs }}` in `score.py`,
  `tools.py`, `examples.py`, `log_results.py`, `from_traces.py`,
  `sync_dataset.py`.
- A cell that fails after `summary.yaml` for another reason still leaves a
  `{model}` run behind, which the analysis picks up.

On `flywheel-integration` (`1a2f2bc`): with C3's sealed workspace the
input file sits in the case record, so the placeholders, `CASE_INPUT` and
the override read the record, with a test; C38's `workspace_files.py`
takes `find_input_file` from `case_input`; C19's `task_format` docstring
and spec 016, C3's `runner.md` and the sealed test's fixture name the new
workspace path, and `3bb423c` fixes the sealed tree in
`skills/eval-run/references/data-pipeline.md`, which the merge missed.

## C19 — `feat/task-format` (`f1cea07`)

Made from `upstream/main` `9bc9a8d`, five commits: the converter
(`572bf4f`), every reader of `dataset.path` (`7d3e3a1`), the S3 download
(`15f4950`), the docs and `specs/016-task-format/` (`b9c0e79`), a task's
files in the report (`f1cea07`). Spec 015 is taken by astefanutti's open
PR #251. Before the PR: one stray blank line in `task_format.py` (three
before `_cached_cases`).

**Title:** `feat(dataset): read a task-format dataset, one YAML file or one JSONL line per task`

**Problem.** A dataset is a folder of case folders and nothing else.
Datasets made elsewhere, generated by another agent or exported from a
ticket system, are one record per task: a YAML file each, or a JSONL file.
Each team converts them by hand, each with its own idea of where the
judges' data goes and how a task's attachments reach the agent. Twelve
modules read `dataset.path` on their own, so no one place can add a
layout.

**Solution.**

- `agent_eval/task_format.py` converts a task dataset into case folders:
  `input.yaml` from `input`, `annotations.yaml` from `expected`,
  `task.yaml` (the task, with `split` and `tags`) and the task's files.
  The keys inside `input` and `expected` stay free.
- Every reader of `dataset.path` calls `resolve_dataset(config)`. It
  returns the dataset itself for case folders, otherwise a cache under
  `<tempdir>/agent-eval-datasets/<hash>/`, keyed by content and written
  atomically (a staging folder, then a rename). It sits beside
  `<tempdir>/agent-eval/`, not in it: eval-run deletes
  `<tempdir>/agent-eval/<run-id>`, and `datasets` is a valid run id.
- A task's files reach the workspace through the same copier as
  `dataset.workspace.files`, and the report lists them.
- EvalHub converts a task dataset from S3 (task files at the prefix's top
  level), from a local path such as `/test_data`, and from a ConfigMap.
- `validate_eval.py` reports every invalid task as an error.
- Case-folder datasets read byte for byte as before.

**The new contract.**

```yaml
id: registry-removed     # YAML: defaults to the file name; JSONL: required
split: train             # optional, kept in task.yaml
tags: [plain-fix]        # optional, kept in task.yaml
input: {...}             # required -> input.yaml
expected: {...}          # optional -> annotations.yaml
files: [screenshot.png]  # optional, under <id>/ beside the task
```

`dataset.path` names a folder of `<id>.yaml` files, or one `.jsonl` file.
Refused, with the file or `file:line` named in one error: an unknown key
(a typo like `expect:` would otherwise drop the judges' data); a missing
or non-mapping `input`; an invalid id (`[A-Za-z0-9][A-Za-z0-9._-]*`, no
leading `.`, `-` or `_`) or a duplicate; a JSONL line without `id`; a
listed file that is missing, a symlink, outside `<id>/`, or named like a
converted file; task files beside case folders.

**Tests.** `tests/test_task_format.py` (32): layouts, conversion, the
cache (location, reuse, a new hash on a change, the per-process memo, a
lost rename race) and every refusal. `tests/test_task_format_pipeline.py`
(7): the same tasks as YAML, as JSONL and as hand-written case folders
give equal workspaces (`workspace.py`) and equal judge records
(`score.py`); also `validate_eval.py`, `/eval-anova`'s case list, the
EvalHub export and the report's case inputs.
`tests/evalhub/test_task_format_downloads.py` (7): S3 with task YAML, one
JSONL, case folders with a stray YAML, two JSONL files refused, the
adapter's local path and ConfigMap. `pytest tests/`: 2342 passed
(baseline 2296). skillsaw 0.10.0 `--strict` and `mkdocs build --strict`
clean. Docs: `website/reference/task-format.md` and the dataset pages.

**Points a reviewer can raise:**

- A case-folder dataset whose top level holds a YAML mapping with an
  `input` key now fails as a mixed folder; a folder with only non-task
  YAML files and no case folders now fails instead of reading as empty.
- The EvalHub adapter's local and ConfigMap branches copy case folders
  only (`copy_dataset`), not the dataset's top-level files. Nothing in the
  harness reads them there: shared `workspace.files` resolve against the
  project (`resolve_workspace_source`).
- The cache is never cleaned; each changed dataset adds a folder under the
  temp folder.
- Out of scope, in `specs/016-task-format/`: Harbor stages no per-case
  files, batch mode none either, and the EvalHub runner's report gets the
  raw config (`docs/research.md` section 4). `/eval-dataset`'s skill writes
  case folders into `dataset.path`; against a task dataset that is a mixed
  folder (not run).

On `flywheel-integration` (`89cb326`): `/eval-anova`'s cell reuse
(`_cell_recipes`, C8) read `dataset.path` directly, so a changed task
reused a stale cell; it now digests the converted case folders through
`resolve_dataset` (a test in `tests/test_anova_reuse.py` fails with the old
line). `adapter.py` keeps `import shutil`, which C7's run-folder export
still uses. The agent's run of `89cb326`: 2664 passed twice, skillsaw and
mkdocs clean.

## C20 — `feat/summary-reward-verdicts` (`f2ca79e`)

Made from `upstream/main` `b306e63` (v1.56.3, 2026-10-16), nine commits:
spec 017 (`e404dde`); the reward composition moved to
`agent_eval/reward.py` (`60c0048`); each case's reward and the run's mean
in `summary.yaml` (`08f3ed8`); every threshold check there (`1fe4705`);
`thresholds.reward` with its readers (`e7d026d`); the reward and its gate
on Harbor (`c2cc5de`); `--no-fail-on-regression` (`8136702`); the docs
(`700d9f9`, `f2ca79e`). No open PR or issue covers it; astefanutti's open
PR #200 (`thresholds.simulator`) changes the same threshold evaluator and
config parsing, so the second to land resolves a conflict there.

**Title:** `feat: the reward and the threshold verdicts in summary.yaml, a threshold on the reward, and --no-fail-on-regression`

**Problem.** The reward a `reward:` block composes goes into Harbor's
`reward.json`, the report and `/eval-anova`, but not into `summary.yaml`.
Threshold verdicts reach only stdout and the exit code. No threshold can
gate the reward. A missed threshold always fails the step, so a caller
that only measures has to ignore the exit code, which also hides crashes.

**Solution.**

- The reward composition moves to `agent_eval/reward.py`;
  `agent_eval/harbor/reward.py` still exports the same names, so there is
  one implementation wherever it is imported.
- `score.py judges` writes a `reward` block: each case's reward, the mean
  and `scored_cases`; a case no judge scored is `null`, as in the report.
- It also writes a `thresholds` block: `passed`, `enforced`, and every
  check with its target, check, metric, limit, value and verdict.
  `detect_regressions` is built from the same checks, so the printed
  regressions, the exit code and the written verdicts cannot disagree.
- `thresholds.reward` takes `min_mean` and `min_per_case` (which names the
  cases below the floor). Config load refuses it when a judge is also
  named `reward`, without a `reward:` block, with any other key, or with a
  limit that is not a number, and refuses `min_per_case` on a judge. A
  summary whose `judges` holds a judge named `reward` still reads as that
  judge.
- The report (a reward row), the MLflow tag, `score.py regression` and
  the Harbor runner read the same verdicts; Harbor's summary gets the same
  `reward` block.
- `--no-fail-on-regression` writes the verdicts with `enforced: false`
  and exits 0. A miss still exits 1 by default.

```yaml
reward:
  mean: 0.5833
  scored_cases: 3
  per_case: {c1: 1.0, c2: 0.75, c3: 0.0, c4: null}
thresholds:
  passed: false
  enforced: false
  checks:
  - {target: ok, check: min_pass_rate, metric: pass_rate, limit: 1.0, value: 0.667, passed: false}
  - {target: reward, check: min_mean, metric: mean, limit: 0.5, value: 0.583, passed: true}
  - {target: reward, check: min_per_case, metric: lowest_case, limit: 0.6, value: 0.0,
     passed: false, cases_below: [c3], detail: 1 of 3 cases below 0.6}
```

**Tests.** 45 new or extended, all with inline check judges and no model:
`tests/test_summary_reward_verdicts.py`, the reward cases in
`test_threshold_consumers.py`, the Harbor run and task-generation tests,
`test_validate_eval.py`, and a test that the composition is one
implementation wherever it is imported. The subagent's runs of the
branch: 2381 passed twice (2336 on `b306e63`), each with 4 skipped and 2
deselected; skillsaw 0.10.0 `--strict` and `mkdocs build --strict` clean.

**Points a reviewer can raise:**

- The move to `agent_eval/reward.py`; the alternative is to import from
  `harbor/reward.py`, as the report and `/eval-anova` did.
- `reward` as a reserved name inside `thresholds`: only a judge also
  named `reward` is refused; unlike #200 there is no warning when only the
  judge exists.
- An unscored case is `null` and stays out of `min_mean` and
  `min_per_case`, while Harbor's `reward.json` gives it 0.0; coverage is
  gated by a judge's `max_error_rate`.
- Only `score.py judges` writes the verdicts block: Harbor writes the
  reward and gates on it, but writes no verdicts; `--runner evalhub` maps
  only the judges' means back, so `thresholds.reward` reads unavailable
  there (documented).
- Nothing is written without a `reward:` block; the default composition
  is not recorded. The CLI does not print the cases below the floor; they
  are in `summary.yaml`.
- Found, not fixed: `min_win_rate` is never evaluated, upstream too. The
  pairwise result is never among the per-judge results the gate reads and
  nothing writes a `win_rate`, so that threshold is skipped in silence,
  though `website/guides/ci.md` tells users to rely on it.
- A judge record keeps `error` and no `rationale` when the judge raised,
  and an inline check that returns a bare value gives `rationale: ""`; a
  reader of reasons takes `rationale or error`.

On `flywheel-integration` (`2293963`, after `1bf99ae` merged
`upstream/main` `b306e63` without a conflict): `harbor/reward.py` keeps
C38's and C39's verifier changes and imports the composition from
`agent_eval.reward`; C37's `fix/anova-cells` already adds a
`--no-fail-on-regression` for `/eval-anova`'s cells, and the merge makes
it one flag whose exit follows `enforced`, with both uses in its help (a
new test in `tests/test_anova_thresholds.py`: a cell that misses a
threshold gets a summary with the failed check and `enforced: false`);
`ci.md` and `thresholds.md` combine both texts. The subagent's runs of the
merge: 2903 passed twice.

## Phase 5 — odh-dashboard `feat/agent-flywheel-module` (`0d8575068`)

Not a PR yet: every page is a placeholder until Lukas has reviewed the
boards (spec 02 phase 5). From upstream `37dc648`, the commit ODH
3.6.0-ea.2's host runs, not from `upstream/main`, and never merged into
`flywheel-integration`. Six commits: `2ca7b5593` (the module tests lose
`dataRegistry`, which #9850 commented out; four tests failed on the base),
`146f2539a` (the `agentFlywheel` flag), `b428634c2` (the package),
`89c1ee360` (`modules.go` and the manifests), `e98380b86` (fork-only:
`params.env` points at our cluster's ImageStream, so it never goes
upstream), `0d8575068` (the BFF builds as root in its builder stage). The
PR text is written when the pages are real, on a branch rebased onto the
`upstream/main` of that day, without `e98380b86`.

## C27 — odh-dashboard `feat/eval-hub-test-data-sources` (`2676e771e`)

Repo `opendatahub-io/odh-dashboard`, clone
`~/Projects/Github/lukaskellerstein/forks/odh-dashboard`, made from
`upstream/main` `b4e406cb5` (2026-10-16), two commits: the BFF
(`96a366551`), the form (`2676e771e`); merged into the new
`flywheel-integration` `7983bd799` without a conflict. Both commits carry
`Co-Authored-By: Claude Code`, as upstream's #10232 does; drop it if
Lukas prefers. The repo has issues turned off; its Definition of Ready
asks for a Jira, the Dashboard Architect's approval and UX sign-off
(`docs/research.md` section 7). It complements jefho-rh's open draft
#10012 (decision 17).

**Title:** `feat(eval-hub): git, PVC and Hugging Face test data sources`

**Problem.** EvalHub lets a benchmark load its test data from S3, a PVC,
a git repository or Hugging Face Hub, and reports the fetched version as
`resolved_sha`. The dashboard knows only S3. A job that uses another
source shows an empty `test_data_ref`, and sending that back is refused.
Suite benchmarks lose their test data in the drawer, on copy and on
edit. A single-benchmark run can use only the benchmark's own dataset.

**Solution.**

- The BFF types and both OpenAPI copies model the full `TestDataRef`:
  `pvc`, `git`, `hf` and a read-only `resolved_sha`; `CollectionBenchmark`
  gains `test_data_ref`.
- The start form gets a "Test data" picker for single-benchmark runs
  outside pre-recorded mode (the benchmark's dataset, git, a PVC or
  Hugging Face), checked against the rules EvalHub applies (http(s) URLs,
  https when a secret is set, DNS-label names); errors show on blur and
  the run stays disabled while a source is invalid. Reconfigure restores
  it.
- Job details show the source and the resolved version, the suite drawer
  each benchmark's source, and copying or editing a suite keeps it.
- No API breaks; `resolved_sha` is never sent.
- It complements #10012 (S3 bucket parsing and `type:
  pre_recorded_data`) and leaves that path alone. They meet in the
  `TestDataRef` type in `evalhub_client.go`, `types.ts` and both OpenAPI
  copies; its `type` field has #10012's exact shape. Against #10012 on
  top of `upstream/main` there are three mechanical conflict hunks (the
  two `TestDataRef` types: take this branch, which holds #10012's `Type`
  line; one import in `startEvaluationRun.schema.ts`: keep both); the
  OpenAPI copies merge on their own (not run together).

```json
"test_data_ref": {"git": {"url": "https://github.com/org/eval-data.git", "ref": "v1.2", "sub_path": "arc"},
                  "resolved_sha": "3f2c9e1d7a"}
```

**Evidence.** New Go tests cover responses and requests for jobs and
collections; on `main` they fail, and the frontend run had 7 failing
suites and 8 failing tests. New frontend tests cover the ref builder and
validator, the form's schema and hook, request building, reconfigure,
copying and editing a suite, the details, the drawer and the picker:
1435 tests on `b4e406cb5`, 1475 here, 88 suites. `test:lint`,
`test:type-check`, `make lint` and `make test` (the BFF: 197 top-level Go
tests) are clean. Not run: Cypress (its binary is not installed in the
sandbox) and the contract tests (the sandbox refuses envtest). Lukas adds
screenshots of the picker, the job details and the drawer; the template
asks for them on UI changes.

**Points a reviewer can raise:** the picker covers single-benchmark runs
only, and suites keep the refs stored on each benchmark; there is no
secret picker, the secret is typed by name as in the existing fields;
`resolved_sha` is shown but not compared across reruns; the S3 source
stays with the pre-recorded fields until #10012 lands, and
`inferSourceMode` reads any S3 ref as pre-recorded, which #10012's `type`
fixes.

## C25 — `feat/sealed-workspace-diff` (`06e5815`)

Stacked on C38's `fix/evalhub-pod` `a44eb8b`: C38 creates
`agent_eval/workspace_changes.py`, the one module both the local run and
the pod collect from, so this PR opens after C38's. `fix/evalhub-pod` is
8 commits behind `upstream/main` and merges into it without conflict
(`git merge-tree`). 4 commits: spec 023 (`bcac94a`), the diff against
the snapshot ref (`9dcbb34`), the change recorded when the agent is done
(`f4e5480`), docs (`06e5815`). Merged into `flywheel-integration` at
`23f7690`: in `execute.py`'s `finally` the order is C23's verify, then
the change record, then `after_each`; `diffstat.diffstat` takes the
snapshot ref as its base too, so a committing agent's lines count; the
merge's test runs one eval locally (normal and sealed) and in the pod,
with hooks, hidden tests, no declared output and a committing agent, and
every path records the same `_modified/` and `_diffstat.json`.

**Title:** `fix(eval-run): _modified/ holds only the agent's change`

**Problem.** A case's `_modified/` should hold what its agent changed.
Three things get in the way, measured with a fake agent that edits one
file, adds one and deletes one:

- The harness writes its own copy of the agent's stdout into the
  workspace's `output/`. With no declared `output` path, every case
  "added" `output/stdout.log`, and a `diff` judge fails on it.
- Files a `before_each` or `after_each` hook writes into the workspace
  count as the agent's.
- An agent that commits its work moves `HEAD`, so its change disappears,
  locally and in the EvalHub pod.

**Solution.**

- The snapshot commit is pinned as `refs/agent-eval/snapshot`, and the
  diff runs against it, not against `HEAD`.
- `execute.py` takes the snapshot again after the `before_each` hooks.
- `execute.py` writes `_modified/` when the agent is done, before the
  `after_each` hooks and before it copies the logs into `output/`: where
  the pod already collects. `collect.py` only counts the files.
- Spec 023 holds the details.

**Tests.** With fake agents and no model, through `workspace.py`,
`execute.py` and `collect.py`, single-step and multi-step: no declared
output, a `before_each` hook, an `after_each` hook, an agent that
commits; a unit test for a committed change; a pod test for a committing
agent. All fail on the base. `make test` 2341 to 2349 passed (the
subagent's run); the agent's runs of `flywheel-integration` `23f7690`:
3347 passed twice, `mkdocs build --strict` exit 0, skillsaw `--strict`
clean.

**Points a reviewer can raise:** `collect.py` no longer collects
`_modified/` itself, so a workspace `execute.py` never ran records no
change; what `before_step` and `after_step` hooks write still counts (a
non-goal, documented); the second snapshot also commits
`.claude/settings.json` and the project symlinks into the case's own
`.git`; files the agent's tools create, such as `__pycache__/`, count
unless the case ships a `.gitignore`; the pod runs no lifecycle hooks at
all, unchanged here; it stacks on the C38 PR.

## C24 — `feat/runner-permissions` (`82e1620`)

From `upstream/main` `1a980e7` (the fullsend per-repo installation), not
stacked; 3 commits: spec 022 (`efa25ee`), the mapping in every runner
(`176670a`), docs (`82e1620`). Merged into `flywheel-integration` at
`1fcae5a`: `RunnerConfig` holds both `pricing` (C2) and `permissions`;
the matrix `runner` factor now repeats each level's limitation warning,
naming the level, because it checks levels with warnings silenced. The
merge also brings upstream's `.fullsend/config.yaml` and two workflows;
they run only from a default branch and need fullsend's secrets, so
they do nothing on the fork's `flywheel-integration`. `CLAUDE.md` is
about 5,995 of skillsaw's 6,000 tokens on the merge: one line was
changed, none added. PR #254 (`--permission-mode manual`) overlaps.

**Title:** `feat(runner): one portable permission setting, runner.permissions: {edit, bash, web}`

**Problem.** An eval that says "edit and shell, but no web" must say it
in each runner's own terms: Claude Code's allow and deny lists,
`permission_mode` and `settings.json`; for Codex only `permission_mode`,
which becomes a sandbox mode; Cursor's `.cursor/cli.json`. Pointed at
another runner, the intent is lost without a word. On `main`, a block
like `runner.permissions` loads without complaint, and none of the three
commands keeps the agent off the web.

**Solution.**

- `runner.permissions` takes `edit`, `bash` and `web`, each true, false
  or left out. Left out means "not set": the runner behaves as today. (A
  default of true would turn on Codex's live web search for
  `{edit: false}`; a default of false would take the shell away for
  `{web: false}`.)

  ```yaml
  runner:
    type: codex
    permissions:
      edit: true
      bash: true
      web: false
  ```

- Each runner maps it onto its own controls (spec 022):

  | Runner | edit | bash | web |
  |:--|:--|:--|:--|
  | claude-code | disallows `Edit,Write,MultiEdit,NotebookEdit`; true: `acceptEdits` unless `permission_mode` is set | `Bash,BashOutput,KillShell,Monitor` | `WebFetch,WebSearch` |
  | codex | `--sandbox read-only` or `workspace-write` | `features.shell_tool` | `web_search` and the sandbox's `network_access` |
  | cursor | deny `Write(**)`, or join the allowlist | deny `Shell(**)`, or join | deny `WebFetch(*)`, or join |

- A key a runner cannot enforce warns at load, naming the runner and the
  key: `edit: false` or `web: false` with a shell on Claude Code and
  Cursor (the shell is not sandboxed), `web: true` in Codex's read-only
  sandbox, any key on a runner that maps none.
- A contradiction with the runner's own settings is refused at load and
  named in one error (an allow rule for a tool whose key is false, a
  whole-tool deny for a key that is true, a contradicting
  `permission_mode` or Codex sandbox, Codex `bypassPermissions` with
  `web: false`); settings that agree are accepted. A scoped deny such as
  `Bash(rm:*)` stays allowed.
- Steps inherit the block (`permissions: {}` on a step lifts it);
  `--agent <type>` is checked again for the runner that runs; prompt
  judges never get it, and an agent judge's runner refuses it; the
  EvalHub pod applies it; Harbor task generation warns that its packages
  do not carry it.

**Tests.** Fake `claude`, `codex` and `cursor-agent` executables record
the command each runner builds; no model is called. One eval runs
through `workspace.py` and `execute.py` with each runner (it fails on
`main`); parsing, inheritance, 20 refused conflicts, the accepted
combinations, the warnings, the commands per runner, and the Harbor and
prompt-judge paths: 72 tests in `tests/test_runner_permissions.py`.
`make test` 2336 to 2408 passed (the subagent's run); the agent's runs
of `flywheel-integration` `1fcae5a`: 3337 passed twice, `mkdocs build
--strict` exit 0, skillsaw `--strict` clean.

**Points a reviewer can raise:** the Codex keys `features.shell_tool`
and `sandbox_workspace_write.network_access` come from codex-cli
0.154.0's `--help` and strings, not from a run against a model; Claude
Code's tool list is fixed, so a tool a later CLI adds is not covered
(`--permission-mode manual`, #254, is the other way); `bash: true` with
`web: false` on Claude Code or Cursor only warns, since the shell can
still reach the network; a conflict is refused, not resolved by a
winner; a key left out means "not set"; steps now inherit a runner
field; Cursor's `true` only joins an allowlist that already exists;
OpenCode maps nothing until its runner (#90) lands.

## C23 — `feat/hidden-tests-after-agent` (`92df98e`)

Stacked on C22's `feat/builtin-text-judges` `6c388f7`: the new judge
uses C22's `check_arguments` convention, and the tests use C22's `diff`
judge to show the agent's change record stays clean; so it opens after
C22. 8 commits: spec 021 (`8aa133e`), the run after each agent
(`a3dab95`, which also carries the load-time refusal of `builtin: verify`
without `execution.verify` that belongs with the judge), the `verify`
builtin (`2019d67`), the EvalHub pod (`9623042`), docs (`6048fdc`,
`6575f27`), packaging the verify files a pod cannot resolve (`3d228c4`),
and a shorter `CLAUDE.md` line (`92df98e`). Merged into
`flywheel-integration` twice (`03f3b58`, then `0671a25`): in the pod,
the verify run sits after the agent on C38's own workspace, before the
change record is collected, and `_verify.json` is a harness path, never
the agent's change; `verify.case_folder` reads task-format datasets
through C19's `resolve_dataset`.

**Title:** `feat: execution.verify, hidden tests after the agent, and the verify builtin` (stacked on the C22 PR)

**Problem.** A coding eval asks the agent to fix a bug so that tests
pass, and must keep those tests out of its workspace while it works. The
harness has no place for them. An `after_each` hook with a `check:` judge
works locally, but the hidden tests and the run's `.pyc` files land in
`_modified/` and `_diffstat.json` as the agent's change (4 files where
the agent changed 1, measured on `main`), the hook's
`.hook-outputs.yaml` is never read and counts as an agent file, its log
has no bound, and the EvalHub pod runs no hooks, so it gives no verdict.

**Solution.**

- `execution.verify {command, files, timeout, output_limit}`, case mode
  only, runs after each case's agent exits, whatever its exit code, after
  the last step and before `after_each`.
- The workspace is copied to a scratch folder and the files are staged
  there: paths from the case's folder, or `{dest, source}` project files
  with `{case_id}`. A staged path replaces what the agent left there; a
  symlink the agent planted is not written through.
- The command runs with `bash -c` in its own process group, with a
  timeout (SIGTERM, then SIGKILL after 5 s, and whatever it left running
  is killed); only the end of its output is kept. The result goes to
  `cases/<id>/_verify.json` and to `outputs["verify"]`.
- The `verify` builtin passes on exit 0 and quotes the last output line:
  `The verify command failed with exit code 1: "2 failed in 0.03s".` A
  command that could not run makes the case an error sample; a case with
  no record abstains.
- Config load refuses the setting in batch mode and in-repo mode, unknown
  keys, `.` as a file, and a `verify` judge without the setting.
- The EvalHub pod runs it after each agent; `export_dataset` packages the
  `{dest, source}` files into `.agent-eval-verify/` for a pod with no
  project.

  ```yaml
  execution:
    mode: case
    verify:
      files:
        - hidden_tests
        - {dest: hidden_tests/test_edge.py, source: "eval/hidden/{case_id}/test_edge.py"}
      command: python3 -m pytest -q hidden_tests
      timeout: 300
      output_limit: 4000
  judges:
    - name: tests
      builtin: verify
  ```

**Tests.** A fake agent through `workspace.py`, `execute.py`,
`collect.py` and `score.py` (the verdicts, that the agent never sees the
tests, a clean change record, steps, `after_each`, a failed
`before_each`); the config, staging, timeout and process cleanup, the
output tail and errors; the judge's verdicts and abstention; the pod,
with a dataset exported and run without the project. `make test` 2446 to
2503 passed on the branch (the subagent's run); the agent's runs of
`flywheel-integration` `0671a25`: 3263 passed twice, `mkdocs build
--strict` exit 0, skillsaw `--strict` clean.

**Points a reviewer can raise:** the copy costs one workspace of disk per
running case; the verdict is the exit code only, with no per-test counts;
on `main` the pod's agent runs in its delivered case folder and can
reach the verify files until the pod's case isolation (C38) lands;
Harbor abstains; a non-list `dataset.workspace.files` is now refused
(before, a string was split per character); a missing source at export
only warns; `.agent-eval-verify/` is a new reserved name; one command per
eval; `a3dab95` carries a check that belongs to `2019d67`; the name is
unrelated to `/eval-optimize`'s `--no-verify`.

## C22 — `feat/builtin-text-judges` (`6c388f7`)

From `upstream/main` `b306e63` (not stacked on C19: annotations exist on
`main`, and C19's `expected` becomes `annotations.yaml`); 7 commits:
spec 020 (`82d07fa`), the load-time argument check (`6ce4582`), the text
builtins (`e2d1729`), `_diffstat.json` in `collect.py` (`7af138b`), the
`diff` builtin (`58ceba2`), docs (`32404f1`), and shorter `CLAUDE.md`
lines (`6c388f7`, after the first merge took it over skillsaw's 6,000
token limit). Merged into `flywheel-integration` twice (`640b9a3`, then
`39153c8`): `jsonschema` stays one extra shared with C26, and
`_diffstat.json` is written by C38's `workspace_changes.collect_modified`,
so pod runs get it too. `opendatahub-io/agent-eval-harness` now redirects
to `fullsend-ai`; no open PR or issue there covers this.

**Title:** `feat(judges): deterministic text and diff builtins with arguments`

**Problem.** Evals keep writing the same inline `check:` bodies: what the
answer must mention, must not say, or must cite, its sections and length,
a pattern, an exact value, a number, a JSON shape. Each copy has its own
bugs, such as substring citations (KB-1042 counted as cited by KB-10423)
and missed negations. Nothing can limit how much of the workspace an
agent changed. A misspelled builtin argument only shows after the paid
run.

**Solution.**

- Nine text builtins in `agent_eval/judges/text/`: `contains`,
  `forbidden`, `cites`, `sections`, `length`, `regex`, `exact`, `numeric`
  and `json_schema`; and `process/diff`, limits on the workspace change.
  None calls a model.
- Each verdict is a value and a one-sentence rationale, for example:
  `Changes 2 files, more than the 1 allowed, and touches the path notes.md, which no 'allow' covers.`
- A per-case value comes from the case's annotations through
  `<name>_from`; a case without that field abstains. Every builtin takes
  `file:`, a pattern for a collected file (default: the conversation).

  ```yaml
  judges:
    - name: mentions
      builtin: contains
      score_range: [0, 1]
      arguments: {file: output/answer.md, items_from: must_mention, partial: true}
    - name: small_change
      builtin: diff
      arguments: {max_files: 3, max_lines: 60, allow_from: may_touch, deny: ["tests/*"]}
  ```

- A new optional `check_arguments` hook checks a builtin's arguments
  when the config loads; a scored builtin declares its `score_range`.
- `collect.py` writes `_diffstat.json` (path, status, lines added and
  removed, deletions included) beside `_modified/`; `score.py` loads it
  as `outputs["diffstat"]`.
- `jsonschema` is an optional extra; `ensure_deps.py` installs it for a
  config that uses `json_schema`, and the base image has it.

**Tests.** Unit tests per judge with the load-time refusals; a parity
test runs a real support eval's four checks against the builtins (they
agree on all 10 shared cases, except where the originals had the bugs
above); `diffstat` on a real git repository, binary, deleted and
symlinked files included; an end-to-end test with a fake CLI agent
through workspace, execute, collect and score. `make test` 2336 to 2446
passed (the subagent's run); the agent's runs of `flywheel-integration`
`39153c8`: 3203 passed twice, `mkdocs build --strict` exit 0, skillsaw
`--strict` clean.

**Points a reviewer can raise:** `check_arguments` is a new convention
the existing builtins do not use; a scored builtin needs an explicit
`score_range`, since `report.py` reads eval.yaml as raw YAML; `forbidden`
decides negation per clause, in English only; `_diffstat.json` and
`_modified/` miss changes the agent committed itself; `diff` abstains on
Harbor runs (and on EvalHub runs before C38); abstaining on a missing
annotation could hide a dataset gap; ten modules make a big PR, so the
text judges and `diff` could be two.

## C26 — `feat/task-json-schema` (`5f3fbb0`)

Stacked on C19's `feat/task-format` `f1cea07`, so it opens after C19; 11
commits: spec 019 (`725bd43`, with a fix-forward of two stray lines,
`c875227`), the unknown-key warning (`a7a1faa`) and its report in
`validate_eval.py` (`1275eae`), the `dataset.json_schema` key
(`b2e94f2`), a task's file and line (`c986561`), the check
(`48a08aa`), in `validate_eval.py` (`a45e3b7`) and at every run start
(`8e8649b`), docs (`11d2d35`, `5f3fbb0`). Merged into
`flywheel-integration` `2c2173d` after C20 and C21: the merge keeps C20's
reward-threshold check beside the key table, which learned upstream
1.56.3's `judges[].agent.denied_tools` and `matrix.runners.*`; the check
runs on the selected split's cases; 14 tests pin the resolutions. It
overlaps open PR #200 only on the warnings for `thresholds.<judge>`.

**Title:** `feat(dataset): a JSON Schema for a task's input and expected, and warnings on unknown eval.yaml keys` (stacked on the task-format PR)

**Problem.** Nothing checks what a case holds. `dataset.schema` is prose,
so a dataset missing the field a judge reads fails case by case mid-run,
or passes a check that found nothing to compare. Nothing checks the keys
of `eval.yaml` either: `dataset.shema`, `execution.timout` or
`thresholds.q.min_pass` load silently, and the run then does something
other than what the file says.

**Solution.**

- An optional `dataset.json_schema` maps `input` and `expected` to a JSON
  Schema, inline or as a file next to `eval.yaml`. `$schema` picks the
  draft (2020-12 by default), `format` is asserted, and a `$ref` works
  within one document.
- It checks the value the agent and the judges get: task files and JSONL
  lines before conversion, and a case folder's input file and
  `annotations.yaml`. Every problem names its file, its line and its JSON
  path, all in one report:

  ```text
  ERROR: dataset.json_schema: 2 problem(s):
    - tasks.jsonl:2: $.input.ticket: 42 is not of type 'string'
    - cases/b/annotations.yaml: $: 'must_mention' is a required property
  ```

- `validate_eval.py` reports every problem as an error; `workspace.py`,
  `orchestrate.py`, Harbor's `generate_tasks` and the EvalHub adapter
  refuse the selected cases before any agent starts. A malformed block is
  refused at config load, which never reads the schema files and never
  imports `jsonschema`.
- `agent_eval.task_schema` exposes `check`, `validate`, `load_schemas`
  and `check_task` (for a caller that holds its tasks in memory).
- Separately, a key that no reader reads warns at load
  (`UnknownKeyWarning`, a `UserWarning`), naming the nearest known key:
  `eval.yaml: unknown key 'dataset.shema' is ignored; did you mean 'dataset.schema'?`.
  `validate_eval.py` lists the same.
- `jsonschema>=4.18` is a new optional extra (also in `all`), imported
  only when a config declares the block; `ensure_deps.py` installs it for
  such a config.

**Tests.** 122 new tests, with fake agents only: the check in every
dataset layout, the schema's own problems, the missing-package hint, the
validator, the refusal at each run start, a typo per block of the key
table, the table pinned to the dataclasses and to what `score.py` reads,
and the repository's own 182 eval.yaml-shaped examples loading with no
warning. `make test` 2464 passed on the branch (the subagent's run); the
agent's runs of `flywheel-integration` `2c2173d`: 3089 passed twice,
`mkdocs build --strict` exit 0, skillsaw 0.10.0 `--strict` clean.

**Points a reviewer can raise:** an unknown key only warns, so a config
with extra keys keeps loading (no strict mode); `jsonschema` is a new
extra; a `$ref` to another file is reported, not resolved; the judge
agent keys and the matrix keys are listed by hand in `config.py`; it
also warns on unknown `thresholds.<judge>` keys, as #200 does; two test
fixtures use keys nothing reads (`inputs.tools[].name`,
`judges[].weight`) and are left as they are; case-folder YAML gives a
line only for a syntax error; a schema file path is read as written,
absolute paths included, like the config's other paths; the docs are in
`website/` and the skill references, since no `SKILL.md` has budget to
spare.

## C21 — `feat/named-splits` (`39a2bcd`)

Stacked on C19's `feat/task-format` `f1cea07`, since it reads C19's
`task.yaml`; 12 commits: spec 018 (`67f270e`), reading a case's split and
selecting one split (`2d244ed`), `--split` on the workspace (`0cdd9ed`),
`split` and `splits` in `summary.yaml` (`24c6896`), Harbor (`bf5846d`),
`/eval-anova` (`c4924c4`), the EvalHub adapter's `parameters.split`
(`1eb3e81`), the MLflow tag (`c496b64`), docs (`032ca6b`, `e7c5b5c`), and
two test fixes (`05c9a3c`, `39a2bcd`). No open PR or issue covers named
splits: #73 adds ratio splits to `/eval-optimize`, and #255 (cap-evolve,
WIP) leaves splits to cap-evolve.

**Title:** `feat: named splits — --split <name> and per-split summaries` (stacked on the task-format PR)

**Problem.** A dataset has no splits. `--cases` takes exact ids, so a
held-out set is a list of ids every caller keeps by hand, and nothing in
a run says which set it scored. The task format already keeps each
task's `split` in `task.yaml`; nothing reads it.

**Solution.**

- `--split <name>` wherever `--cases` selects cases: `workspace.py`,
  Harbor's `run.py` and `/eval-dataset`'s `harbor.py` (task generation),
  and `/eval-anova` (its cells get the chosen ids as `--cases`). With
  `--cases` too, the cases in both run, since a loop re-runs its failing
  cases inside one split. Refused, with a clear message: no case has a
  split, an unknown split (naming the splits the dataset has), an empty
  overlap with `--cases`, a ratio such as `40:20:40`. Cases without a
  split are left out and counted in the log.
- `summary.yaml`: `split: <name>` when every scored case is in that
  split, or `splits` (per split: the case count, each judge's mean and
  pass rate) when the run spans several. The keys come from the scored
  cases, not the flag, so a re-score, a Harbor run and an anova cell name
  their split too. The overall keys are unchanged (a test checks it). The
  MLflow run gets a `split` tag when the summary names one.
- The EvalHub adapter runs only the split that `parameters.split` names,
  after any delivery (declared in `deploy/evalhub/provider.yaml`).
- A case's split is the `split` key of its `task.yaml`; a hand-written
  case folder can carry one.

```text
workspace.py ... --split test  ->  "--split test: left out 1 case(s) with no split", CASES: 2
summary.yaml:  split: test
no --split:    splits: {test: {cases: 2, judges: {mentions: {mean: 0.5, pass_rate: 0.5}, ...}}, train: {cases: 3, ...}}
```

**Beside #73.** #73 puts a ratio `--split 40:20:40` on `/eval-optimize`;
its script takes `--ratio` and writes `tmp/splits.yaml`. This PR gives no
flag or file a second meaning: `--split` lives on eval-run's scripts and
names one split, a ratio there is refused, and it reads and writes no
`splits.yaml`. If `split_dataset.py` wrote each case's set into its
`task.yaml`, `/eval-run --split selection` would run #73's validation
set, and one run would report train and selection apart in `splits`.

**Tests.** `tests/test_named_splits.py`, all with fake agents and inline
`check` judges. The subagent's runs of the branch: 2386 passed twice
(2342 on `f1cea07`), each with 4 skipped and 2 deselected; skillsaw 0.10.0
`--strict` (0 warnings) and `mkdocs build --strict` clean.
`skills/eval-run/SKILL.md` ends at 4,498 tokens of 4,500: a Step 1 line
that repeated Step 3's command went.

**Points a reviewer can raise:** `--split` and `--cases` together run the
intersection instead of refusing; `score.py` and the `--runner evalhub`
client have no `--cases`, so no `--split`; in Harbor and the EvalHub
pod, which score after the agent ran, an unreadable `task.yaml` drops the
split keys with a warning instead of failing, while `score.py` checks
before any judge runs; with the summary-reward PR (C20), each split
block also carries its cases' reward mean, about 8 lines in whichever PR
lands second. Found in #73, for its authors: it tells `/eval-run` to use
`--case <ids>`, "comma-separated, substring matching", a flag that does
not exist (it is `--cases`, exact ids separated by spaces), and its
`split_dataset.py` lists the folders of `dataset.path`, which on a
task-format dataset are the tasks' file folders, not the cases.

On `flywheel-integration` (`2137cdd`): the merge resolves
`evalhub/adapter.py` (C7's parallel-case helper and the split filter; the
split narrows the cases before the workers are counted), `harbor/run.py`
and `score.py`'s `cmd_judges` (C20's reward written first, then the split
keys), and the merged `score_cases` signature; it adds the reward per
split, the split keys in the EvalHub pod's `summary.yaml`, the reward on
the `splits` row of `runs-directory.md`, and 6 tests in
`tests/test_named_splits.py`. The subagent's runs of the merge: 2953
passed twice.

## C11 — eval-hub-contrib `feat/agent-eval-harness-adapter` (`ef0fb5c`)

Repo `eval-hub/eval-hub-contrib`, clone
`~/Projects/Github/lukaskellerstein/forks/eval-hub-contrib`, made from
`upstream/main` `78f01e4` (2026-10-16), four commits: the adapter
(`044712e`), its make targets (`77c6b5f`), a CI workflow (`5c2de66`), the
README row (`ef0fb5c`); merged into the new `flywheel-integration`
`98d7683`. Signed off, `Co-Authored-By: Claude Opus 5.5`; `cz check`
passes. It needs a harness release with C19 to C21 (the task format,
`--split`, the reward block): against harness `main` `b306e63`, 11 of its
29 tests fail. Its CI workflow pins `lukaskellerstein/agent-eval-harness@2137cdd`,
which is on no remote until Lukas pushes `flywheel-integration`, so CI
fails until then; an upstream PR needs the harness release instead.

**Title:** `feat(agent-eval-harness): add an adapter that runs any agent-eval-harness eval`

**Problem.** EvalHub cannot evaluate CLI agents (Claude Code, Codex,
OpenCode) with their instructions and skills on a team's own tasks.
agent-eval-harness does this locally, but its runs stay outside EvalHub:
no job, no pass criteria, no MLflow record.

**Solution.**

- A community adapter with one benchmark, `eval-run`, for every eval. The
  eval folder is the benchmark's test data at `/test_data`, so a new eval
  needs no new image. It is checked while the job initializes: an
  `eval.yaml` that `EvalConfig` loads, with a `reward:` block.
- It runs the harness's own eval-run scripts as subprocesses
  (`workspace.py`, `execute.py`, `collect.py`, `score.py judges
  --no-fail-on-regression`), on a copy of `/test_data`, with `TMPDIR` and
  the runs folder in the job's own folder, so a job scores like a local
  run and no harness code is copied. A SIGTERM stops the running script
  and its agents, with 30 s before a kill.
- `split` selects the tasks (`workspace.py --split`; an unknown split
  fails the job). `brain` (`runs:/<run_id>/<path>`, an MLflow artifact
  folder) is laid over the project root and only its top-level entries
  are linked into each workspace; a brain entry that would replace an
  eval file is an error, and a sealed workspace refuses a brain.
- `summary.yaml`'s `reward.mean` is the primary score; each judge's mean
  and pass rate and the agents' cost are metrics. The run folder (every
  task's verdicts and reasons) goes to the job's MLflow experiment and to
  the OCI export.
- The image builds on a harness image passed as `BASE_IMAGE`, and runs
  the offline smoke test at build time.

```text
EvalHub: overall_score 1.0; reward 1.0, reward_scored_cases 2, correct_mean 1.0,
  correct_pass_rate 1.0, policy_mean 1.0, policy_pass_rate 1.0; num_examples_evaluated 2
MLflow: run/summary.yaml, run/run_result.json, run/console.log, run/collection.json,
  run/cases/<task>/{input.yaml, output/answer.txt, run_result.json, events.json}
```

**Tests.** 29 offline tests run a fake agent on a three-task eval with no
model and no network: the score with and without the brain (1.0 and
0.25), split selection, MLflow and OCI output, that the agent never sees
the answer key (`annotations.yaml`, `task.yaml`, `eval.yaml`, `hidden/`),
failing agents, invalid input, the MLflow download, and stopping on
SIGTERM. Before `main.py` existed the suite failed on its import. The
agent's runs of the merge: 29 passed twice, the smoke test passed, ruff
0.16.9 check and format clean; `make test-atif` 132, as on `main`.

**Points a reviewer can raise:** it needs a harness release, and CI pins
a commit until then; the default base image
`quay.io/rhoai/agent-eval-harness:latest` has no OpenCode, and whether it
is public is not checked (quay.io is outside the sandbox; the harness's
other image, `quay.io/rhoai/agent-eval-hub`, answered 401 on 2026-10-14);
`ArtifactReader` uses private members of the SDK's MLflow client, since
SDK 1.0.6 has no download; the workspace is isolated the harness's way,
by working directory, so the copy of `/test_data` with `hidden/` and the
answer keys stays reachable by absolute path, as in a local run; the job's
`model.url` is not read (the model name goes to `--model`, the endpoint
comes from the image's env or `runner.env`), as in the harness's own
adapter; `type: community`, while contrib's CONTRIBUTING says `builtin`;
open upstream PR #224 also moves adapters to SDK 1.0.6 artifacts. What
the harness lacks, all worked around: no packaged entry point for the
headless pipeline (the scripts live in `skills/`, outside the wheel), no
explicit "link nothing" in `workspace.py` (the adapter passes `,`), no
overlay option for extra files.

## C29 — trustyai-service-operator `fix/tas-watch-without-kserve` (`c724383`)

Repo `trustyai-explainability/trustyai-service-operator`, clone
`~/Projects/Github/lukaskellerstein/forks/trustyai-service-operator`, made
from `upstream/main` `258b3a9` (2026-10-15). Its CONTRIBUTING asks for an
issue on every `fix` commit: phase 7 opens it and adds the link.

**Title:** `fix(tas): watch InferenceServices only when the KServe CRD is installed`

**Problem.** The TrustyAIService controller registers a watch on KServe's
`InferenceService` with no check (`controllers/tas/trustyaiservice_controller.go`,
`SetupWithManager`). When the cluster does not serve
`serving.kserve.io/v1beta1`, for example Open Data Hub with KServe
`Removed`, that kind source never syncs. After `CacheSyncTimeout` the
controller fails with `failed to wait for trustyaiservice caches to sync
kind source: *v1beta1.InferenceService`, and the manager exits with every
controller in it: EvalHub, LMES, NeMo Guardrails. On an ODH 3.6.0-ea.2
cluster the operator restarted 228 times in 30 hours, and `default-dsc`
kept flipping to `Not Ready`. PR #899 made reconcile skip InferenceService
handling without the CRD but left the watch; `ARCHITECTURE.md` calls
KServe optional.

**Solution.** In `SetupWithManager`, register the watch only when
`isInferenceServiceCRDPresent` (the uncached `APIReader` from #899) finds
the CRD; otherwise log one line and start without it, as the EvalHub
controller does for Kueue. If the check itself fails, setup returns the
error. A KServe installed later is watched after the next operator
restart; until then reconcile's periodic requeue still handles its
InferenceServices. No RBAC change: CRD `get` is already granted.

**Tests.** `controllers/tas/inference_service_watch_test.go` starts its
own envtest with only the TrustyAIService CRD and runs the real
`ControllerSetUp` in a manager with a 5 s `CacheSyncTimeout`. Without the
KServe CRD the controller must start its workers and register no
InferenceService source; on `main` this fails with the error above. With
the CRD installed, the source must be registered. `make test`: 249 Go
tests and 255 Ginkgo specs pass (baseline 247 and 255; the baseline's one
failure needs `python` on `PATH`). `go mod tidy` leaves no change.

**Evidence.** On `cluster-nm8mw` (ODH 3.6.0-ea.2, KServe `Removed`) the
image of `flywheel-integration` `2a28e81` ran 1 h 52 min with 0 restarts
(2026-10-15 01:26 to 03:38 CEST), where the ODH image had restarted 228
times. It needs the NetworkPolicy and Events rights of upstream's roles,
which ODH 3.6.0-ea.2 does not grant yet (`docs/research.md` section 5).

**Points a reviewer can raise:** the test reads the started sources from
the manager's log; KServe enabled later needs an operator restart.

## C14 — trustyai-service-operator `fix/evalhub-adapter-exit` (`24e6886`)

Repo and clone as C29, made from `upstream/main` `258b3a9`; merges with
C29 without a conflict. Issue as for C29.

**Title:** `fix(evalhub): report an adapter that exits non-zero without a result`

**Problem.** The EvalHub failure watcher ignores an adapter container that
exits non-zero for any reason other than OOM
(`terminatedAdapterNeedsOperatorReport`), because an adapter often posts
its own result before it exits non-zero. So an adapter that crashes before
it reaches EvalHub leaves its evaluation job `running`. Posting `failed`
on every non-zero exit is not safe either: while other benchmarks of the
job still run, EvalHub replaces a benchmark's status and results with a
later terminal event (`updateBenchmarkStatus`, `updateBenchmarkResults`),
so a blind post would overwrite a result the adapter already reported.
And EvalHub answers any event on a terminal job with 409
`job_can_not_be_updated`, which the failure watcher and the Kueue workload
watcher both retry every 30 seconds for as long as the Job exists.

**Solution.** For an adapter that exits non-zero for a reason other than
OOM, GET the evaluation job first, and post `failed` only while the job is
not terminal and the benchmark has no terminal status; if EvalHub cannot
be read, requeue. OOMKilled and the other operator-only failures post as
before, without the GET. A 409 `job_can_not_be_updated` ends the sync:
the Job (or the Workload) is marked reported, with no `Failed` phase and
no Event, since EvalHub keeps the outcome it recorded. Any other refusal
is retried as before. No RBAC change: the operator already holds `get` on
`evaluations`.

| Case | Before | After |
|:--|:--|:--|
| Adapter exit 0 | ignored | ignored |
| Exit ≠ 0, benchmark open | ignored, job stays `running` | GET, one `failed` post, `Failed`, Event |
| Exit ≠ 0, benchmark or job terminal, or job gone | ignored | GET, no post |
| Exit ≠ 0, EvalHub not readable | ignored | requeue after 30 s |
| OOMKilled, init, sidecar, image pull, mount | post | unchanged |
| 409 `job_can_not_be_updated` | retried every 30 s, forever | done, no phase, no Event |

**Tests.** `evaluation_job_failure_reconciler_adapter_exit_test.go`, with
a fake EvalHub serving the job GET and the events POST: an exit while the
benchmark is open posts one `failed`; a completed, failed or cancelled
benchmark, a terminal job or a missing job gets no post; EvalHub
unavailable requeues; a 409 `job_can_not_be_updated` is done for both
watchers; any other 409 is retried. The adapter-exit and 409 tests fail on
`main`. `make test` on `flywheel-integration` `e4ddb1a` (C29 and C14):
256 Go tests and 255 Ginkgo specs pass, twice.

**Points a reviewer can raise:** an exit EvalHub already has gets no
annotation, so a replayed Job costs one more GET; `exitCodeFromPod` looks
for the native sidecar in `ContainerStatuses` only (its status is in
`InitContainerStatuses`), left as it is.

## C10 — eval-hub `fix/k8s-runtime-json-tags` (`86d4fcf`)

Repo `eval-hub/eval-hub`, clone `~/Projects/Github/lukaskellerstein/forks/eval-hub`,
made from `upstream/main` `3f7b173` (2026-10-15). Commits signed off, with
the `Generated with: Claude Code` trailer. eval-hub asks for an issue
before any work, and counts an API change as architectural: the issue
below frames it as a bug, the API not matching its documented schema.

**Title:** `fix(api): serialize provider k8s runtime fields with their documented names`

**Problem.** `K8sRuntime` (`pkg/api/providers.go`) has `mapstructure` and
`yaml` tags but no `json` tags on `image`, `entrypoint`, `cpu_request`,
`memory_request`, `cpu_limit`, `memory_limit` and `env`; `EnvVar`
(`pkg/api/common.go`) has none on `name` and `value`. `encoding/json` then
uses the Go field names, so create and update drop the four resource
fields and a tenant provider's adapter pod gets the default resources
(`internal/eval_hub/runtimes/k8s/job_config.go:123-126`); responses say
`Image`, `CPURequest`, `Env[].Name` and so on, not the names of
`docs/src/components/schemas/K8sRuntime.yaml` and `EnvVar.yaml`; `PATCH
/runtime/k8s/cpu_limit` answers success and changes nothing. The ODH
dashboard's eval-hub BFF reads both spellings to work around it
(`ProviderK8sRuntime.UnmarshalJSON`, odh-dashboard #10141).

**Solution.** json tags as the schemas name the fields: `image` and
`entrypoint` required, the four resource fields and `env` with
`omitempty`, as `gpu` and `image_pull_policy` have. The comment's example
said `default_env`; it is `env`.

**Response change.** Provider responses (get, list, create, update,
patch) use the documented snake_case names and leave out unset optional
fields. A client that reads `CPURequest` and the other Go names must
switch. Go clients built on an older `pkg/api` still read `image`,
`entrypoint` and `env` (`encoding/json` matches keys without regard to
case) but not the resource fields. Stored providers keep their image,
entrypoint and env (tested).

**Tests.** `pkg/api`: the documented JSON decodes, the encoded keys are
exact (env items included), unset optional fields are left out, a provider
stored with the Go names still decodes. Handler: a POST with resources
returns them under the documented names. SQL storage: `PATCH
/runtime/k8s/cpu_limit` changes the value. All but the guard test fail on
`main`. The agent's sandboxed run of `flywheel-integration` `4856472`:
1478 Go tests pass (baseline 1472), the same 23 fail on both, all bound to
the hardcoded `/tmp/evalhub-jobs` and `/tmp/db_password`, Postgres tests
skipped. The subagent's run with those paths: 1500 pass, FVT 195/195, MCP
FVT 39/39. `pre-commit run --all-files` and golangci-lint clean.

**Issue text** (kind: bug). Title: `Provider runtime.k8s resource fields
are dropped by the API, and runtime fields come back with Go field names`.
Steps: POST a provider with `runtime.k8s.cpu_request: "250m"`; the
response holds `"CPURequest": ""` and `"Image": …`. Expected: the fields
as `docs/openapi.json` names them, the values kept. Cause: `K8sRuntime`
and `EnvVar` have no json tags. Impact: tenant provider resources never
reach the adapter pods; `PATCH /runtime/k8s/*` does nothing; clients need
workarounds, the dashboard BFF has one. Fix: json tags matching the
schema; responses change to the documented names. A PR follows.

## C12 — eval-hub `fix/local-runtime-exit` (`b60213e`)

Repo and clone as C10, made from `upstream/main` `3f7b173`; merges with
C10 without a conflict (`flywheel-integration` `7e94ad9`). Signed off,
with the `Generated with: Claude Code` trailer.

**Title:** `fix(runtime): fail a local benchmark whose provider exits without a result`

**Problem.** The local runtime ignores how a provider process ends
(`_ = cmd.Wait()` in `runtimes/local/local_runtime.go`). A provider that
crashes, is killed, or exits before it posts a terminal status leaves its
benchmark, and so the job, pending or running for ever. The API does not
say why; only `jobrun.log` holds the reason.

**Solution.** After the process ends, a cancelled job is left alone.
Otherwise the runtime reads the job and posts `failed` for the benchmark
only if the job is not terminal and the benchmark (same id, provider and
index) has no terminal status yet. The message names how the process
ended (`exit status 3`, `signal: killed`, from `ProcessState.String()`,
so it builds on Windows) and its log file. The read comes first because
storage replaces a terminal benchmark status with a later terminal event
(`storage/sql/evaluations_status.go:234-237`): a blind post would wipe a
reported result. If the job cannot be read, the status stays as it is,
with a warning in the log. `RuntimeStorage` gains `GetEvaluationJob`,
implemented by the handler's `runtimeStorage` through `scopedStorage()`;
every test fake already had the method. `localJobsBaseDir` becomes a
variable so the new tests can use `t.TempDir()`.

| Case | Before | After |
|:--|:--|:--|
| Exit ≠ 0, no report | ignored, job stays pending or running | one `failed` post with the exit status and log path |
| Exit 0, no report | ignored | the same post (`exit status 0`) |
| Killed by a signal, not cancelled | ignored | the same post (`signal: killed`) |
| Reported, then exit ≠ 0 | kept | kept: read, no post |
| Job already terminal | ignored | read, no post |
| Job cannot be read | ignored | no post, a warning |
| Cancelled | no post | no post, before the read |
| Launch error | `failed` post | unchanged |

**Tests.** `local_runtime_exit_test.go`: a non-zero exit, a zero exit and
a signal each get one `failed` post with the process end and log path, and
all three fail on `main`; a benchmark already completed or failed, a
terminal job, an unreadable job and a cancelled job with an open benchmark
get no post (with a blind post in place of the read, three of them fail).
The comment of `TestRunEvaluationJobProcessFailureNoCallback` stated the
old design and is rewritten. The agent's sandboxed run of
`flywheel-integration` `7e94ad9`: 1480 Go tests pass (1469 on `main`,
plus 6 of C10 and 5 of C12), the same 23 fail as on `main`, all bound to
the hardcoded `/tmp/evalhub-jobs` and `/tmp/db_password`. One more,
`pkg/mlflowclient` `TestUploadArtifactWithWorkspaceHeader`, failed once
with `http: CloseIdleConnections called`; that package is flaky on `main`
too (8 tests failed once each in 200 runs there, none in 200 on the
merge). The subagent's runs, with the jobs folder moved into the sandbox:
the 22 local-runtime tests pass, fuzz passes, MCP FVT 39/39; the FVTs
pass 187 of 195 on `main` and on the merge alike, the 8 bound to the same
jobs folder. `pre-commit run --all-files`, `gofmt`, `go vet` (also with
`GOOS=windows`) clean.

**Points a reviewer can raise:** it reverses a stated design ("the
subprocess itself is responsible for status reporting",
`local_runtime_test.go:805-806` on `main`), which CONTRIBUTING can count
as architectural; the post is safe only if a provider's report is stored
before the provider exits, which holds because the events handler stores
inside the request (`handlers/evaluations.go:727` on `main`) and the sidecar
proxies the POST (`internal/eval_runtime_sidecar/handlers/handlers.go:121`),
read, not tested end to end; the sidecar keeps its own
`DefaultJobsDir = "/tmp/evalhub-jobs"`
(`internal/eval_runtime_sidecar/proxy/job_cache.go:29`), which must stay
equal to `localJobsBaseDir`. The k8s runtime has the same gap; the
operator side is C14.

**Issue text** (kind: bug). Title: `Local runtime: a provider that exits
without reporting leaves its evaluation job pending forever`. Steps:
register a provider whose `runtime.local.command` is `exit 1`, then
create a job on it. Expected: the benchmark ends `failed`, with a message
naming the exit. Actual: the job stays `pending`; only
`/tmp/evalhub-jobs/<job>/…/jobrun.log` shows the exit. Cause:
`runBenchmark` ignores `cmd.Wait()`'s result by design, and a crashed or
killed provider never reports. Proposal: after the process ends, fail the
benchmark only if storage holds no terminal status for it and the job is
not terminal or cancelled; a provider that reported keeps its result. A
PR follows.

**On `flywheel-integration` `4315523`** (with C28, 2026-10-16), upstream
#1144 added `K8sRuntime.DRA` next to `Env`, on the line where C10 adds
`Env`'s json tag: the merge keeps both, with
`TestK8sRuntimeJSON_KeepsDRAAndEnvNames` (it fails if the tag is lost).
C10's rebase on `upstream/main` takes that, and C10's PR gets the test.

## C28 — eval-hub `feat/evalcard-test-data-ref` (`69fe00d`)

Repo and clone as C10, made from `upstream/main` `eec7581` (2026-10-16);
merged into `flywheel-integration` `4315523` with C10 and C12. Signed off,
with the `Generated with: Claude Code` trailer. No open PR or issue covers
it; issue #937 (open) proposes EvalCard storage references and a
provenance section, and PRs #1124, #1125 and #1127 are about OCI export
status, not the card's content.

**Title:** `feat(cards): name each result's test data on the evaluation card`

**Problem.** The evaluation card leaves `test_data_ref` out
(`CardBenchmarkConfig`: "Omits hardware_config and test_data_ref"), and
for a collection job its context lists no benchmarks at all. A card
exported to MLflow or OCI therefore does not say which data a score came
from, and the `resolved_sha` that eval-hub records once its init container
resolved a git or Hugging Face ref (#858, #996) never reaches the card.

**Solution.**

- Each `results.benchmarks[]` entry carries `test_data_ref`: the source
  (`s3`, `pvc`, `git` or `hf`), `type` and `resolved_sha`. It comes from
  the job's effective benchmark list (for a collection job, the collection
  merged with the job's overrides), taken by `benchmark_index` and checked
  against `id` and `provider_id`; a mismatch leaves the field out rather
  than naming the wrong data.
- The handler resolves that list as the container-log export does
  (`resolveJobBenchmarksForStorage`). If that fails (the collection was
  deleted), the card is exported without it, with a warning.
- `secret_ref` is left out of every source, as `CardModelRef` leaves out
  `auth`, and the git URL loses any user name and password typed into it
  (the API accepts such a URL today).
- `NewEvaluationCard(job)` becomes `NewEvaluationCard(job, benchmarks)`;
  a GitHub code search finds no caller outside the repo.
- The field is optional, so `card_version` and `schema_version` stay
  `1.0`, as with `metrics_schema` (#884). No OpenAPI change: the card's
  schema is not in `docs/src`.

```json
{"id": "validation", "provider_id": "agent_eval", "status": "completed",
 "metrics": {"reward": 0.82},
 "test_data_ref": {"git": {"url": "https://github.com/example/usecases.git",
                           "ref": "support-v3", "sub_path": "support"},
                   "resolved_sha": "4f1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c"},
 "test": {"primary_score": "0.82", "threshold": "0.7", "pass": true}}
```

**Tests.** 7 new: in `pkg/cards`, git with a SHA and s3 on a direct job,
hf with a SHA and pvc on a collection job, the results-only path,
mismatched and nil lists, no credentials in the card's JSON; in the
handlers, a collection job through `onEvaluationJobUpdated` with a
collection-defined s3 source and a job override carrying a git SHA, and
an export when the collection cannot be resolved. Before the fix they do
not compile; with the types and signature but nothing filled in, 5 fail
on their assertions. The subagent's runs of the branch: 1493 unit tests
pass (1486 on `eec7581`), the same 23 `/tmp`-bound failures; with the
jobs folder in the sandbox the local runtime's 52 pass; FVT 187 of 196
twice, the 9 bound to the same jobs folder (one, `standalone_post_processing.feature:97`,
is new upstream, #1146); MCP FVT 39/39; fuzz passes. `pre-commit run
--all-files` (with `SKIP=go-test`, since that hook runs the Postgres tests)
and `golangci-lint run ./...` are clean.

**Points a reviewer can raise:** `results` rather than `context`, since a
collection job has no context benchmarks and `resolved_sha` is an outcome
of the run; the changed exported signature (an option or a second
constructor are the alternatives); no `schema_version` bump (#937's open
question 3); leaving `secret_ref` out, and whether the API should refuse
credentials in a git URL instead; S3 and PVC sources have no content
identity; the list is resolved from the current collection at export
time, as score aggregation does; one more `GetCollection` read per
terminal transition of a collection job; duplicate (`provider_id`, `id`)
entries resolve to the first override, which is existing behaviour.

**Issue text** (kind: feature). Title: `EvalCard does not say which test
data a score came from (test_data_ref, resolved_sha)`. Problem: the card
built in `pkg/cards` omits `test_data_ref`, and for a collection job it
lists no benchmarks, so a published card cannot be traced to its data,
and the git or hf `resolved_sha` already stored on the job is lost.
Proposal: add `test_data_ref`, with `type` and `resolved_sha`, to each
benchmark result on the card, from the job's effective benchmark list,
without `secret_ref` or credentials in a URL. Alternatives: put it in
`context.benchmarks` and expand a collection job's context, or a separate
provenance section (#937, Part 2). Use case: compare scores across runs
only when they used the same data version; audit a published card. The
field is additive; S3 and PVC sources have no `resolved_sha`. A PR
follows.
