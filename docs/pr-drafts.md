# PR drafts for the fork branches

Drafts, not posted. Each PR is opened by Lukas, in his own voice, after his
go (`PLAN.md` §0). Each branch is in Lukas's fork clone of
`opendatahub-io/agent-eval-harness`, made from `upstream/main` `175eed5`
(2026-10-13), and checked out in
`~/Projects/Github/lukaskellerstein/forks/.worktrees/agent-eval-harness/<branch>`.
Before a PR, rebase the branch on the newest `upstream/main` (`PLAN.md` §5).

Written by the subagent that built each branch, checked by the agent
(2026-10-14). The test counts are the agent's own runs; the baseline on
`175eed5` is 2289 passed, 4 skipped, 2 deselected.

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

## C2 — `feat/runner-price-override` (`df9e57c`)

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

## C3 — `feat/isolated-case-workspace` (`658d3f4`)

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
