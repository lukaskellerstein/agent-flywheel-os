# PR drafts for the fork branches

Drafts, not posted. Each PR is opened by Lukas, in his own voice, after his
go (spec 01 §0). Each branch is in Lukas's fork clone of
`opendatahub-io/agent-eval-harness`, made from `upstream/main` `175eed5`
(2026-10-13; C1 to C4) or `9bc9a8d` (v1.56.2, 2026-10-14; C6, C8, C9,
C30, C31, C32, C34), C7 from C4, C33 from C1. All branches live in the
clone `~/Projects/Github/lukaskellerstein/forks/agent-eval-harness`, with no
worktrees; check one out there with `git switch <branch>`.
Before a PR, rebase the branch on the newest `upstream/main` (spec 01 §5).
The branches of the other forks (spec 02 §5) get their sections here
too, each naming its repo, its base commit and its clone; their issues
are opened with the PRs (spec 02 decision 15).

Written by the subagent that built each branch, checked by the agent
(2026-10-14). The test counts are the agent's own runs; the baseline is
2289 passed on `175eed5`, 2296 on `9bc9a8d`, 2291 on C4, each with 4
skipped and 2 deselected.

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
  new test covers a price behind a gateway. The second of the two to land
  takes that.
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
- C8 and C34: they merge clean, but C8 rewrites the guide row on
  overrides (`website/guides/eval-anova.md:166`), which still says "merged
  into the case's `input.yaml`". The second of the two to land aligns it
  with C34: the case's input file, or every `batch.yaml` entry in batch
  mode.
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

## C8 — `feat/anova-cell-reuse` (`5b5a3de`)

Stacked on `feat/anova-runner-factor`: the reuse key hashes the per-cell
runner block, and both rewrite `fan_out`.

**Title:** `feat(eval-anova): reuse a finished cell instead of running it again`

**Problem.** The run id is the date plus the levels
(`skills/eval-anova/scripts/orchestrate.py:111-123`), and `fan_out` runs
every cell on every call (`orchestrate.py:192-244`). Nothing records what
a run measured, so adding a level or a replication, or going on after a
crash, pays for the whole matrix again.

**Solution.**

- Each cell gets a recipe: a SHA-256 over the harness version, the cell's
  resolved config (`extends:` and the runner level merged, every key but
  `matrix`), its factor levels, and every file in each case's dataset
  directory.
- The recipe and the replication are stamped into `condition.json` only
  after all four eval-run steps succeed.
- A cell whose recipe and replication match a finished run is skipped, and
  that run reused; `--force` re-runs every cell.
- `--dry-run` reports `Reused: N of M cells` and estimates the rest only.
- A restarted cell loses its stamp until it finishes again.
- Files the config only points at (the skill under test, `plugin_dirs`,
  prompt files) are not hashed; the docs say so, and say to use `--force`
  after changing them.

**Tests.** `tests/test_anova_reuse.py`, 18 tests: reuse, `--force`, the
stamp; only the new replications or the new level run; changes that must
not re-run a cell (analysis settings) and changes that must (judges,
arguments, effort, case files, a case subset, a runner block); failed and
restarted cells; two identical runner blocks under two names; the dry-run
count and estimate; old stamps without a recipe; an end-to-end run through
the real eval-run scripts, called twice: 2 runs, then 0. `pytest tests/`:
2344 passed. `mkdocs build --strict` and skillsaw clean.

## C9 — `feat/optimize-no-verify` (`97817e7`)

Made from `upstream/main` `9bc9a8d` (v1.56.2). Clear of #73 (astefanutti's
optimize rewrite, the only open optimize PR): the default loop gets two
table rows and one routing paragraph, and the mode lives in new files. If
both land, the Step 0 table takes both sets of rows, and one line says
`--strategy` has no effect with `--no-verify`.

**Title:** `feat(eval-optimize): add --no-verify, one proposed edit for a caller that scores it`

**Problem.** `/eval-optimize` always verifies its own edits: Step 1 runs
`/eval-run` when no results exist (`skills/eval-optimize/SKILL.md:44-52`),
Step 5 re-runs it with `--baseline` (`:142-154`), and Step 6 keeps or
reverts (`:167-174`), for up to `--max-iterations` (`:20`), with
`AskUserQuestion` among its tools (`:5`). A caller that scores edits itself
(a training loop with a held-out set, a CI job) cannot ask for one proposal
and keep the decision; today it copies the skill, rewrites its
`allowed-tools` and prompts it to skip Steps 1 and 5.

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

**Tests.** `tests/test_eval_optimize_no_verify.py`, 17 tests: the skill
text contract (the flags in Step 0, the route before Step 1, the `## Never`
rules, every `${CLAUDE_SKILL_DIR}` path resolves, the documented keys match
the script's output) and `proposal.py` (a valid write, a file created in a
directory artifact, `no-change`, three ways to lie outside the artifact, an
unknown judge or case, a missing case, `--no-change` with `--file`, an
unscored run, the script run by path). `pytest tests/`: 2314 passed, 4
skipped, 2 deselected (baseline 2296). skillsaw strict and `mkdocs build
--strict` clean. Not tested: what a model does with the text; no model
calls were made.

## C30 — `fix/mlflow-traces` (`f63969a`)

Made from `upstream/main` `9bc9a8d`.

**Title:** `fix(eval-mlflow): link case-mode traces, attach their feedback, and give them a model`

**Problem.** `skills/eval-mlflow/scripts/log_results.py:592-593` imports
`AsyncExportQueue`, which no supported MLflow has (it is
`AsyncTraceExportQueue` since at least 3.5.0), so the flush before linking
and feedback is a no-op that prints a warning. Linking (`:603`) and
`log_feedback` (`:660`) then race MLflow's background trace writer: on a
sqlite store with MLflow 3.17.1 every case-mode run failed both, the link
with `FOREIGN KEY constraint failed`, the feedback with `Trace … not
found`. Separately, `log_results.py:527` builds each case trace from the
case's `per_case` entry, which `skills/eval-run/scripts/execute.py:1432`
writes without a `model`, so LLM spans get no `mlflow.llm.model` and the
`per_model_usage` cost is never spread over them.

**Solution.**

- Flush through the public `mlflow.flush_trace_async_logging()` (in MLflow
  3.5.0 already).
- A case entry without a model takes the run's model in log_results.
- `execute.py` records each case's model, the runner's reported one else
  the requested one, as batch mode does, so a run started with an alias
  gets per-span cost.
- The tracing and runs-directory pages say where a span's model comes
  from.

**Tests.** `tests/test_log_results_sqlite.py` runs `log_results.py`
against a temporary sqlite store for a two-case run: no trace warnings,
every trace linked, each trace with its judge feedback, LLM spans with the
model and the case's cost. `TestCaseRunResult` for the fallback; a
parametrized `execute.py` test for the per-case model. Checked by hand on
MLflow 3.5.0, the oldest the package allows, after the span status codes
were rewritten: 3.5.0 rejects the builder's `STATUS_CODE_OK`
(`agent_eval/mlflow/trace_builder.py:56,648`), a separate bug. `pytest tests/`: 2306 passed
(baseline 2296). skillsaw and `mkdocs build --strict` clean.

## C31 — `fix/evalhub-pod` (`04d184e`)

Made from `upstream/main` `9bc9a8d`. Meets C7 in `adapter.py` and
`runner.py` (see "The order matters").

**Title:** `fix(evalhub): score pod cases as a local run does; bound the runner's job wait`

**Problem.** `agent_eval/evalhub/adapter.py:116` calls `score_cases`
without a run id, and nothing in the pod wrote `stdout.log`, `events.json`
or `run_result.json`, so `load_case_record` (`skills/eval-run/scripts/score.py:316,428`)
gave every judge an empty record: a judge on `outputs["exit_code"]` got
its default, 1, on every case; turns, cost, stdout, stderr and the
conversation were missing. Under an OpenRouter plan the pod also scored
before the run's end, with each case's cost still pending.
`agent_eval/evalhub/runner.py:125,277`: `--timeout` defaults to `None`, so
the runner polls forever on a job that never ends (EvalHub sets no
deadline), and a given timeout escaped as a traceback without the job's
state.

**Solution.**

- The adapter leaves what a local run leaves: each case's `stdout.log`,
  `stderr.log`, `events.json` and `run_result.json`, and the run's
  `run_result.json` with `per_case`. It replaces a file the agent planted
  there rather than writing through it.
- `score_cases` takes `runs_dir` and passes it to `load_case_record`; the
  default is unchanged.
- Under a plan, the pod closes the run before its judges score it.
- The runner waits up to 7200 s by default, `--timeout 0` for no limit;
  on a timeout it exits 1, naming the job, its last state and the server's
  message. The job keeps running on the server.

**Tests.** `tests/evalhub/test_pod_scoring.py`: exit code, turns, stdout,
stderr and conversation reach the judges; the file layout matches a local
run's; `traces.events: false`; a planted symlink is not written through;
the settled cost under a plan; `score_cases(runs_dir=)`. They pass on the
stubs and on the real SDK 0.4.4 and 1.0.6. `tests/evalhub/test_runner_wait.py`,
with a fake SDK module: the default bound, a timeout, `0`, an unreadable
last state, the CLI defaults. `pytest tests/`: 2307 passed (baseline
2296). skillsaw and `mkdocs build --strict` clean.

## C32 — `fix/cost-figures` (`4e21613`), two PRs

Made from `upstream/main` `9bc9a8d`; each commit also applies alone. PR A
is `754b037`, `3480586` and `4e21613`; PR B is `e244129`, which meets C2
(see "The order matters").

**PR A — Title:** `fix: keep sub-cent run costs, OpenCode cache tokens and the fable alias intact`

**Problem.** `skills/eval-run/scripts/execute.py:2055` rounds the
case-mode run `cost_usd` to cents: two cases at $0.002 record `0.0`, and
MLflow's `cost_usd` metric, logged only when truthy, disappears.
`eval/opencode-smoke/scripts/run-opencode.sh:85,88` writes `input =
tokens.input + cache_read` and a `cache_write` key, but OpenCode's
`tokens.input` is already uncached and the harness reads cache writes as
`cache_create` (`report.py:1307`, `score.py:4024`, `trace_builder.py:1089`,
`log_results.py:357`), so cache reads count twice and cache writes are
lost. `agent_eval/agent/claude_code.py:802-826` forwards the opus, sonnet
and haiku alias variables but not `ANTHROPIC_DEFAULT_FABLE_MODEL`, which
the plan also sets (`agent_eval/providers/env.py:30-33`); without a plan a
host mapping of the fable alias never reaches the CLI.

**Solution.** The run total keeps 6 decimals, as reconcile does; only the
`COST:` line rounds to cents. The wrapper passes `tokens.input` through
and writes `cache_create`; the cookbook says what `input` means. The fable
variable joins the allowlist and the docs.

**Tests.** An end-to-end workspace.py and execute.py run with the `cli`
runner; the wrapper against a fake `opencode` event stream; an allowlist
test that reads the alias slots from the plan's own env block. `pytest
tests/`: 2310 passed for the branch. skillsaw and `mkdocs build --strict`
clean.

**PR B — Title:** `fix(codex): report a gateway run's cost as unavailable instead of a name-matched list price`

**Problem.** `agent_eval/agent/codex.py:590-592` prices a run by looking
its model name up in `litellm.model_cost`. Behind a gateway the name is an
alias the operator chose; a name that matches a litellm key (`gpt-5`,
`cerebras/gpt-oss-120b`) gets that model's list price whatever was served,
a wrong figure that looks right, which `cost_budget` then judges. The
report's `unavailable` banner (`skills/eval-run/scripts/report.py:1079-1081`)
always named the OpenRouter sources.

**Solution.** When codex does not talk to OpenAI's API (a `model_provider`
other than `openai`, or an `openai_base_url` / `OPENAI_BASE_URL` host
other than `api.openai.com`), the runner returns `cost_usd: null` with
`cost_source: unavailable`, the spec 014 label for a cost no source could
establish. The check reads the codex process's own env, hook values
included; on OpenAI's API nothing changes. A run reconcile never touched
gets its own banner. Runners, providers, report, runs-directory and
environment-variables pages updated.

**Tests.** Five gateway set-ups, the hook env and the timeout path report
`unavailable`; no gateway, an explicit `api.openai.com` URL and
`model_provider: openai` keep the litellm figure; the banner for a run
without a plan.

## C33 — `fix/stop-handlers` (`7e59702`)

Stacked on C1 (`fix/stop-on-sigterm`): open it after the C1 PR lands.

**Title:** `fix: stop the agents of a stopped score.py and of a cancelled EvalHub job`

**Problem.** Agent judges and runner-backed LLM judges start their agent
through the CLI runners (`skills/eval-run/scripts/score.py:3212`,
`agent_eval/prompt_backends.py:309`), each in a process group of its own
(`agent_eval/agent/process_group.py:53`). `score.py` installs no stop
handler (`:4289`): SIGTERM or SIGHUP exits without a `finally`, SIGKILL
too, and the judge's agent keeps running; Ctrl-C reaches `score.py` alone,
and `score_cases` leaves its pool through the `with` block (`:2657`),
which first scores every queued case. The EvalHub provider runs cases and
judges in-process, and `deploy/evalhub/entrypoint.py:63` installs no
handler: EvalHub's local runtime cancels with `Kill(-pid, SIGKILL)` to the
provider's group (eval-hub `internal/eval_hub/runtimes/local/process_unix.go:12`),
which the agents are not in. On Kubernetes the provider is the
container's PID 1, which gets no signal it has no handler for.

**Solution.** `score.py` and `entrypoint.py` install
`process_group.install_stop_handler()` at their script entry, as
`execute.py` does: a SIGTERM/SIGHUP handler and a SIGKILL watchdog.
`score_cases` leaves its pool as `execute.py`'s parallel loop does: it
cancels the queued cases, kills the running judges' groups and re-raises.
No new machinery. The runners page's "Stopping a run", the agent-judge
docs, the EvalHub guide and the cli runner contract are updated.

**Tests.** `tests/test_stop_agents.py`, with a fake agent that starts a
child: SIGTERM to `score.py` with an agent judge on `cli`, `codex` and
`claude-code`; SIGTERM, Ctrl-C and SIGKILL with two judges, and no second
agent starts; Ctrl-C cancels the cases not yet scored; SIGTERM and
group-SIGKILL to `entrypoint.py` while a case's and a judge's agent run.
All 11 fail before the change. `pytest tests/`: 2314 passed (C1's head
2303); the 25 stop tests 3 of 3 runs. skillsaw and `mkdocs build
--strict` clean.

## C34 — `fix/anova-cells` (`7931dca`)

Made from `upstream/main` `9bc9a8d`; merges clean with C8.

**Title:** `fix(eval-anova): apply non-model factors in batch mode and to input.yml/input.json cases, and give every level its own run id`

**Problem.** `/eval-anova` passes every factor but `model`, `effort` and
`subagent` to eval-run as `--input-override`. `execute.py` merged those
only in case mode (`skills/eval-run/scripts/execute.py:1815-1822`) and
only into `input.yaml` (`:1822`); the batch path (`:559-617`) ignored them,
and so did a case whose input is `input.yml` or `input.json`, both of which
`workspace.py:567-573` accepts. The factor silently did nothing, and the
ANOVA compared identical cells. Separately, `_safe_id_segment`
(`agent_eval/anova/matrix.py:179-182`) mapped every unsafe character to
`_`, so `a/b` and `a_b`, or `""` and `factor`, gave one run id
(`skills/eval-anova/scripts/orchestrate.py:111-123`), and one cell
overwrote the other's run directory.

**Solution.** Batch mode merges the overrides into every `batch.yaml`
entry before `{prompt}` is resolved, and stops before the agent starts
when an entry is not a mapping. Case mode merges into the case's own input
file, in `workspace.py`'s order; JSON stays JSON. `_safe_id_segment` keeps
every value that already is a valid segment, so existing run ids still
match; any other value is cleaned as before and gets 8 hex digits of its
SHA-256 (`a/b` → `a_b-c14cddc0`). `matrix-schema.md` and the matrix
reference say where an override lands and how run ids are made.

**Tests.** `tests/test_input_overrides.py` runs the real `workspace.py`
and `execute.py` with a `cli` runner, batch and case mode, `.yaml`, `.yml`
and `.json` inputs, a non-mapping batch entry, and an end-to-end
`/eval-anova` batch cell. `TestSafeIdSegment`: safe values kept, distinct
values distinct, every segment a valid run id. A two-level fan-out lands
in two run directories. `pytest tests/`: 2327 passed (baseline 2296).
skillsaw and `mkdocs build --strict` clean.
