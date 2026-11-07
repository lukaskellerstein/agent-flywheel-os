# Spec 03: What this repo still lacks

Status: a proposal, written 2026-11-07. Nothing in it is decided: each
feature waits for Lukas's go. Decisions 1 to 22 (specs 01 and 02) hold. It
was written from a full read of this repo's `main` at `0dae3af`.

## 0. Read this first

**Why it exists.** Lukas, 2026-11-07, asked for one spec of what this repo
still lacks, so that no step depends on anything outside this repo
(decision 22). This spec writes down every such feature as behaviour,
rules and measured numbers. Nothing here is code to copy.

**How it relates to spec 02.** Spec 02 stays the active plan for what it
covers: the registry, the contributions, the module, the proof. This spec
adds what spec 02 leaves out or names only in passing. Section 1 says where
spec 02 stands, section 2 lists every gap, section 3 describes each gap as
something to build, section 4 proposes an order, section 5 keeps the
numbers a plan needs.

**Words.** This spec uses this repo's words: use case, task, training
run, online evaluation (decision 12).

**The numbers.** The numbers below that were measured before this repo's
loop existed are estimates to plan with; section 5 says when the main ones
were measured.

## 1. Where spec 02 stands (2026-11-07, `main` at `0dae3af`)

| Part of spec 02 | State | What is left |
|:--|:--|:--|
| Phase 1, harness contributions | done but C5 | C5 waits for Lukas's PR #90 comment, then astefanutti |
| Phase 2, EvalHub, contrib, operator | done | — |
| Phase 3 step 1, the bucket | done | — |
| Phase 3 step 2, the flywheel API | partly | the EvalHub collection per use case (section 4.3), the MLflow evaluation dataset |
| Phase 3 step 3, the loop | partly | the Adjust backends GEPA and `/eval-optimize`; MLflow traces (DoD item 4) |
| Phase 3 step 4, the runner image | done | — |
| Phase 3 step 5, support version 1 | done, by upload | the import from git; the LLM judge `quality` |
| Start training from the API | done in code (`16429c3`, `0dae3af`) | the status in spec 02; the Start training page |
| Phase 4, Hugging Face import | not started | everything |
| Phase 5, the module | partly | Benchmarks and Brains are placeholders; Start training's page |
| Phase 6, the proof | not started | all five steps; a second use case exists nowhere as data |
| Phase 7, the PRs | waits for Lukas's go, each time | all |
| Phase 8, where the loop lives | waits for the maintainers | — |

Contributions: C10 to C12, C14 and C19 to C39 are merged into each fork's
`flywheel-integration`; C13 is skipped; C15, the module, stays on its own
branch on purpose; C16 to C18 are replaced by decision 20; C5 is not
started.

## 2. The gaps

| # | Feature | This repo now | Spec 02 | Here |
|:--|:--|:--|:--|:--|
| 1 | The training loop: keep at ≥, patience, the best brain as the result | yes, `flywheel/flywheel_loop/` | phase 3 | — |
| 2 | The training run's record: a curve per iteration, cost, time, brain hash, recipe | partly | no | 3.1 |
| 3 | Stop a training run, its log, live tasks | no | no | 3.1 |
| 4 | Smoke and picked subsets of tasks | no | no | 3.2 |
| 5 | An LLM judge (support's `quality`) | no | named only | 3.2 |
| 6 | An MLflow trace per task and per Adjust step | no | DoD item only | 3.2 |
| 7 | The Adjust backend Adjuster (OpenCode) | yes | phase 3 | — |
| 8 | The Adjust backends GEPA and `/eval-optimize`, the schedule Adjuster then GEPA | no | "not built" | 3.3 |
| 9 | The Adjust step's checks and its cost | partly | no | 3.3 |
| 10 | Benchmarks: the grid, reuse, the comparison, the pages | no | a goal only | 3.4 |
| 11 | Brains: one catalog, evaluate a brain, brain v0 | partly | placeholder page | 3.5 |
| 12 | Online evaluation | no | "left out" | 3.6 |
| 13 | OpenCode as the agent under test | no, only as the adjuster | waits for C5 | 3.7 |
| 14 | The use case's missing checks and fields | partly | partly | 3.8 |
| 15 | Console features: a use case's file text, estimates, Home, the Score step page | no | "left out" | 3.9 |
| 16 | A second and a third use case, `pyfix` and `copywriter` | no | phase 6 | 3.10 |
| 17 | The Harbor Score backend, the laptop mode, variants, authoring, images | no | no | 3.11 |

## 3. The features

Each feature says what it is, how it behaves, where it lives by decision
1's rule, what was measured, and when it is done.

### 3.1 The training run's record and its control

**What this repo does not record yet.**

- A curve: the parent run gets, at step N for iteration N, the metrics
  `train/score`, `validation/score`, `train/<judge>`, `validation/<judge>`,
  `loss` (1 minus the train score), `elapsed_s` and `<split>/cost_usd`, and
  `best/train_score` and `best/validation_score`. MLflow then draws the
  training curve by itself. This repo logs every metric at step 0
  (`flywheel/flywheel_loop/mlflow.py:63`), so no curve, and no cost or time.
- Two tags on every Score result: `brain_hash`, a hash of the brain's
  files, and `recipe`, a hash of everything else that decides a score: the
  use case version, the split's tasks, the judge model, the runner's
  settings. Section 3.4's reuse needs both.
- Already here and kept: `decision` per iteration (baseline, kept,
  reverted, no change), `best_iteration` and `stop_reason` on the parent.

**Control.**

- Stop: a training run stops on request. The step that runs ends at once,
  the run's result is its best brain so far, and its state reads
  "stopped", not failed. This repo marks the parent run FAILED on SIGTERM.
- The loop's log and the log of each step, readable on the training run's
  page.
- Live tasks: while a Score step runs, the page shows which tasks are done
  and their verdicts, refreshed every 5 seconds.
- A training run's id is new in its experiment, checked before the start.

**The keep rule.** A candidate is kept when its train score is at least
the best one's, a tie keeps, validation never decides, two reverts in a
row stop the run, three iterations by default. A "no change" candidate
could be scored (one more measurement of the best brain); this repo skips
it. Proposal: keep this repo's rule, it is cheaper. Noise to know: v0's
train score moved between 0.33 and 0.47 over four runs of the same 20
tasks, so a keep at ≥ with no margin can keep noise.

**Where.** `flywheel/flywheel_loop/` (the metrics, the tags, the stop), the
flywheel API (a stop route that ends the Job), the module's training run
page (Stop, the log, live tasks).

**Done when.** One free training run on GLM 5.3 shows a three-point curve
in MLflow with the cost and the time of each iteration and `brain_hash` on
each Score result; Stop on the page ends a running training run within 30
seconds, with its best brain kept and the state "stopped".

### 3.2 Scoring: an LLM judge, traces, subsets

**The LLM judge.** Support's sixth judge, `quality`:

- a rubric for a senior support engineer, a score from 1 to 5, three
  samples and their median;
- it sees the task's input, its answer key and the answer, and a short
  summary of the policies written into its prompt, not the hidden files;
- weight 0.20, threshold 4.0; model `gpt-oss-120b` (paid) or a local Gemma.

Support version 1 here leaves it out, because a judge model inside the
EvalHub job pod has no route to the gateway yet (`usecases/support/eval.yaml:8-11`).
To build:

1. The harness's judge in the job pod calls the cluster's gateway, as the
   agent there already does, with no key (the gateway takes none inside the
   cluster).
2. A judge model: GLM 5.3 first, since it is free; check that its scores
   are stable over three samples before support uses it.
3. Support version 2 with `quality`, its weights 0.25, 0.25, 0.15, 0.15
   and 0.20 (`kb_citation`, `must_mention`, `policy`, `format`,
   `quality`), or kept as now with `quality` added; Lukas picks.

**Traces.** One MLflow trace per task of every Score result: the agent's
steps as spans, each judge's verdict and reason as feedback, tagged with
the use case, its version, the task, the brain and `kind=task`. One trace
per Adjust step, `kind=adjuster`, with the session's steps. This is
spec 02 phase 3's open DoD item 4. Where: the harness or C11's adapter
first (decision 1), since both already write to MLflow; the loop only for
the Adjust step's trace.

**Subsets.**

- `smoke`: a fixed small part of each split, for a cheap run of the whole
  loop. Support's was 4 train and 2 validation tasks, of the same kinds as
  the full splits. Proposal: a task tag
  `smoke`, and a start request that takes `subset: smoke`.
- `picked`: a list of task ids picked on Start evaluation.
- A training run on `smoke` reports only the tasks it scored; on a full
  split a missing train task fails the Adjust step.

**Done when.** A free evaluation of support version 2 shows `quality` with
three samples per task and a trace per task with every judge's feedback in
MLflow; a training run with `subset: smoke` scores 6 tasks per iteration.

### 3.3 The Adjust step: its checks, its cost, two more backends

**The contract, the same for every backend.** In: the best brain, the
train results of that brain as `failures.md` (every train task with a judge
below its top: the shown fields, the answer key, every verdict with its
reason, the answer) and `history.md` (per brain: its base, the files it
changed, the hypothesis, the change, the train score and its delta, the
decision; never a validation number). Out: the next brain and `change.md`
with the lines `Hypothesis:` and `Change:`.

**Checks this repo has, and the ones it lacks.**

| Check | Here |
|:--|:--|
| Only changed brain files are kept; a skill's frontmatter is repaired; a new skill beyond `max_skills` is dropped; an empty file fails the step | yes |
| One retry when a session changed no brain file | yes |
| No failing train task: no session, the brain stays as it is | no, the session runs |
| A train task missing from a full split fails the step | no |
| Deletions and edits outside the brain are counted as `adjuster/ignored_edits` | no |
| Tags `adjust_backend`, `adjust_schedule`, `adjuster_model`; the session's cost | no; the cost reads 0 for a paid model |

**Leak rules, for every backend.** `hidden/` never enters a workspace; the
task text says the policies are absent; no backend ever sees a validation
number. A known leak: `failures.md` carries the answer key and the judges'
reasons, so a policy id reached the adjuster as if it were a KB id.

**GEPA** (the `gepa` library, 0.1.4).

- One reflection call per brain file that exists, with GEPA's default
  prompt. Its records come from `failures.md`: the task as the input, the
  answer as the output, the answer key and the verdicts as the feedback.
- Its answer replaces the whole file. An answer that is cut off, only
  reasoning, or empty is refused.
- It never creates a skill and never reads `history.md`; the backend
  writes `change.md` for it.
- Its model is its own setting, called through the gateway.
- The schedule "Adjuster then GEPA" runs the Adjuster in the first Adjust
  step and GEPA in every later one.
- Measured risk: GEPA copied train facts into `AGENTS.md`; on two smoke
  validation tasks the validation score fell from 0.675 to 0.237. On the
  full support set it reached train 0.998 and validation 1.000 from 0.282
  and 0.353, in 11 minutes, 1.83 USD of which GEPA's own calls were 0.05;
  its third brain had 1,672 words, and the agent's cost per Score step
  rose from 0.18 to 0.54 USD.

**`/eval-optimize`** (the harness's own skill).

- One headless Claude Code session per Adjust step: `/eval-optimize` with
  one iteration on the train run, talking to the gateway as the Anthropic
  API.
- Settings: permission mode `dontAsk`, project settings only, at most 40
  turns, the tools Read, Write and Edit, and Bash only for `ls`, `cat`,
  `head`, `grep`, `find`, `wc`, `test` and the skill's `state.py`.
- Before the session: the best brain's train run folder in the workspace,
  the skill alone (not the plugin, so no hooks and no other commands), and
  a config with the judges' names, types and ranges but not their prompts.
  The prompt tells it to skip its own evaluation.
- Measured: 540,000 tokens in 34 turns, 0.54 USD per Adjust step, about
  ten times the Adjuster's 0.051 USD. On GLM 5.3
  through the gateway it costs nothing.

**Where.** `flywheel/flywheel_loop/`, one module per backend behind the
contract; the runner image adds `gepa`; Start training gets a backend pick.

**Done when.** One free one-iteration training run per backend and the
schedule, each with its tags, its priced cost (0 USD on GLM 5.3) and a
trace of its Adjust step; the four missing checks covered by tests.

### 3.4 Benchmarks

**What.** A grid of agent × model × brain on one use case version's
validation split, with N evaluations per cell (1 to 5, default 3), to
choose what to release. Limits on the start form: at most 3 agents, 8
models and 6 brains.

**Rules.**

- A brain is v0 or a brain a training run made.
- Reuse: an evaluation with the same agent, model, `brain_hash` and
  `recipe` (section 3.1) counts as a run of its cell, the newest first.
  Without those two tags nothing can be reused.
- Before the start, one call of 16 tokens per model that still has runs to
  make; a model that fails it skips its cells.
- At most 12 evaluations at once on the cluster, and a cap per model for
  models with a rate limit; models take turns.
- A failed evaluation fails its run, not the benchmark.

**Record.** A parent MLflow run `kind=benchmark` with the tags `state`,
`recipe` and `judge_model`, and the artifacts `plan.json` (the cells and the
runs to make) and `result.json`. Each evaluation is tagged
`source=benchmark`, the benchmark's id and its run number.

**The comparison.** Per cell: the mean, the lowest and highest run, the
mean of each judge, USD per 1,000 tasks and seconds per task. Before the
start an estimate of time and cost from the measured means of earlier
runs, with reuse counted.

**Pages.** The list; New (the picks, runs per cell, the estimate); one
benchmark: its numbers, the matrix, score against cost, by judge, the
leaderboard, its evaluations, Stop.

**Measured.** The v0 grid cost 2.87 USD. With three runs per cell the
best cell scored 0.670 (0.65 to 0.69), the top six lay within 0.04 of each
other, OpenCode scored 0.24 to 0.41, and the cheapest of the top six cost
3.0 USD per 1,000 tasks. So three runs per cell are the minimum to tell
cells apart.

**Where.** The flywheel API: it already starts evaluations as EvalHub jobs
and reads AI hub's agents and models, and a benchmark joins those with
MLflow (decision 1: orchestration between projects is ours). The module's
Benchmarks pages, after a board.

**Done when.** A free benchmark of 2 agents × GLM 5.3 × 2 brains × 1 run on
support's smoke validation tasks shows its matrix; run again, it reuses
every evaluation and starts none.

### 3.5 Brains

**What.** One catalog of every brain: v0 and every version every training
run made. Per brain: its lineage (its parent, the training run, the
iteration), its files, how it scored (train and validation, per judge), how
it was made (the Adjust step's hypothesis, change and backend), and where
it was used (evaluations, benchmarks). Action: "Evaluate this brain".

**Brain v0.** A use case's own agent file can be its v0; support's held
one line: "You are a helpful assistant for Red Hat customers. Answer
their questions." Here v0 is empty. Proposal: an optional `brain/` folder
in a use case, v0 when present.

**Where.** The flywheel API reads brains from the training runs' MLflow
artifacts (it already takes `brain` on an evaluation, as
`runs:/<run>/brain`); the module's Brains pages; Start evaluation gets a
brain pick.

**Done when.** The Brains page lists support's v0 and `training-jhqlf`'s
v1 with their scores, and "Evaluate this brain" starts an evaluation that
names the brain.

### 3.6 Online evaluation

**What.**

- A conversation page: pick an agent, a model and a brain; each turn the
  agent answers with the whole conversation as its prompt.
- The judges that need no answer key, marked `live`, score each answer;
  support's were `exit_success`, `format` and `quality`. A conversation
  opened from a task ("Continue as the customer") gets every judge with
  that task's key on its first answer.
- A turn's score is the weighted live judges rescaled to sum to 1, shown
  as "not comparable" with an offline score.
- Each answer is an MLflow trace (`kind=talk`, the conversation, the turn,
  the model, the judge) with the verdicts as feedback; the history is read
  back from the traces, and a conversation reopens.
- An answer is flagged when `quality` is below its threshold. Never
  built: "Add to the use case", a draft task from a conversation whose key
  a person writes.

**What it needs here.** A `live` mark per judge (section 3.8); a way to run
one agent turn on demand, which is open: an EvalHub job per turn is slow,
so a small runner service or a Job per turn; the history in MLflow. With
support's key-free judges of version 1 (`format`, `short`, the exit code) no
judge model is needed.

**Done when.** A board first, then Lukas's go (decision 18's way). Not
planned further here.

### 3.7 OpenCode as the agent under test

OpenCode as an agent under test: a config per use case, with edit, shell,
web fetch and sub-agents denied, 15 steps, temperature 0, the gateway as
its provider with prices; a quota error retried four times after 30 to 45
seconds. Here OpenCode runs only as the adjuster: the evaluation pods
use the harness image, which has no OpenCode, and the harness maps
OpenCode's permissions only once C5 lands (C24). To build: OpenCode in
the harness image (a C11 or base image build arg), an AI hub agent
`opencode`, C5. Measured: OpenCode scored 0.24 to 0.41 in the v0
benchmark, against 0.67 for the best cell.

### 3.8 The use case format: what it lacks

| Field or check | Here | Proposal |
|:--|:--|:--|
| Every task has the fields the UI shows | only the prompt field | check on import |
| `hidden/` never in `eval.yaml`'s workspace files | not checked | refuse on import: it is the leak guard |
| Every weighted judge exists, one weight above 0 | judge names unique only | check on import |
| A judge's short label and its `live` mark | none | `usecase.yaml`: `judges: {<name>: {label, live}}` |
| Brain v0 | empty | section 3.5 |
| The smoke subset | none | section 3.2 |
| A local judge overlay (`extends:`) | none | not needed: the cluster is the target |
| `plural` of the task label | none | not needed |
| Support's `needs_version_question`, `needs_escalation` in a task's key | in the data | read by no judge; a judge or nothing |

### 3.9 Console features the module lacks

Each needs a board first, as the module's other pages had.

- **A use case's files as text**: the knowledge base articles and the
  policies, with a product filter and Formatted/Raw. The module lists the
  paths only; the API serves no file's content yet.
- **Estimates** of time and cost on Start evaluation and Start training,
  from the measured means of earlier runs of the same agent, model and
  use case version.
- **Home**: an overview with counts, use cases to evaluations to
  benchmarks and training runs.
- **A Score step's page** in a training run: its scorecard and tasks per
  split, its log, live tasks.
- **The experiment**: here each use case has its own experiment,
  `agent-flywheel-<use case>`, with no picker and no "New experiment".
  Proposal: keep that, with a link.

### 3.10 The second and third use cases (spec 02 phase 6)

Neither exists as data anywhere; both must be written. Spec 02 phase 6
picks one (decision 10).

**`pyfix`**, code: 12 small Python repositories with one bug each, 8 train
and 4 validation. A task describes the bug as a user would ("the CLI
prints the wrong total when ..."). The hidden `pytest` checks the fix after
the agent has exited (C23). Judges: the tests pass (weight 0.5); diff
limits, at most 3 files and `tests/` untouched (0.1, C22); a rubric judge
`review` on the diff, is the fix minimal and right (0.4, an LLM judge,
section 3.2); the exit code (0). The agent may edit and run a shell, each
task in its own sandbox, and its output is the diff (C25).

**`copywriter`**, text: 15 product briefs (the product's facts and the
audience), no resources, so everything the agent learns lands in its
brain. Judges: `accuracy` against the brief's facts (LLM), `tone` against
`hidden/brand-guide.md` given to the judge as context (LLM), the sections,
and forbidden phrases.

### 3.11 Out of scope, or later (proposal)

- **The Harbor Score backend**: each task in a restricted Harbor trial pod
  with no ServiceAccount token, about 10 seconds more per task. EvalHub's
  job pod is the sandbox here. Out.
- **The laptop mode** (MLflow, the gateway and a local model in Compose):
  the cluster is the only target. Spec 02 phase 6 step 2's laptop run
  becomes a run on GLM 5.3 on the cluster. Out.
- **Variants** (named runner overrides as a fourth benchmark axis),
  **authoring** (a use case drafted from a one-page description by an
  LLM, and a check of it), **images** (attachments to the agent and a
  vision judge): later, each after a board and a go.

## 4. A proposed order

All free on GLM 5.3 through the gateway, unless a step says otherwise.

| Group | Sections | Why first |
|:--|:--|:--|
| A | 3.1 record and Stop; 3.2 traces, the LLM judge, support version 2; 3.8 import checks | small, and every later group reads these records |
| B | 3.5 Brains and "Evaluate this brain" | the page exists as a placeholder; the API already takes `brain` |
| C | 3.4 Benchmarks | needs A's `brain_hash` and `recipe` |
| D | 3.3 GEPA, `/eval-optimize`, the schedule | needs A's traces to compare backends |
| E | 3.10 `pyfix` | spec 02 phase 6; needs A's LLM judge |
| F | 3.6 online evaluation, 3.7 OpenCode, 3.9 the console's rest | each after a board |

## 5. Measured facts to keep

| What | Number | When |
|:--|:--|:--|
| A training run on the cluster, 30 tasks, 3 steps (`flywheel-ctpt6`) | 10 min 59 s; train 0.293 to 0.898, validation 0.448 to 0.869; agent 1.36 USD, adjuster 0.33 USD, judge not priced | 2026-10 |
| Another (`flywheel-dkqsz`) | 7 min 49 s; 1.04 + 0.38 USD | 2026-10 |
| v0's noise on 20 train tasks | 0.33 to 0.47 over four runs | 2026-10 |
| A training run scored through EvalHub | 8 min 8 s, 8 jobs; train 0.315 to 0.909, validation 0.325 to 0.891; 1.92 USD | 2026-10 |
| A Score step's CPU | 140 s at 6 CPU, 240 s at 2 | 2026-10 |
| GEPA on the full set | 11 min 2 s; 1.83 USD (GEPA 0.05); train 0.282 to 0.998, validation 0.353 to 1.000 | 2026-10 |
| GEPA's leak on smoke | validation 0.675 to 0.237 | 2026-10 |
| `/eval-optimize`, one Adjust step | 540,000 tokens, 34 turns, 0.54 USD | 2026-10 |
| The Adjuster, one Adjust step | 0.051 USD | 2026-10 |
| The v0 benchmark grid | 2.87 USD; best cell 0.670 (0.65 to 0.69); top six within 0.04; OpenCode 0.24 to 0.41 | 2026-10 |
| This repo's first training run (`training-jhqlf`) | about 12 min, 0 USD on GLM 5.3; v0 train 0.630, validation 0.680; v1 0.769 and 0.783, kept | 2026-11-07, spec 02 phase 3 status |

## 6. Sources

This spec is complete on its own: every feature, rule and number it needs
is written here.
