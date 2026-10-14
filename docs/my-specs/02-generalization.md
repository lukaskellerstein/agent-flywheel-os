# Spec 02: Generalization, one flywheel for any use case

Status: the active plan, written 2026-10-14. Decisions 10 to 15 are Lukas's
(section 2); everything marked **proposal** waits for his answer to the
open questions of section 9. This spec carries every open step of spec 01
([`01-initial-implementation.md`](01-initial-implementation.md)), which is
closed: its phases 0, 1 and 2 are done, and phase 2's open C5 and C19
moved here.

## 0. Read this first

**What this is.** Spec 01 put Agent Flywheel into Open Data Hub for one use
case, the support agent. This spec makes the flywheel general: a team
brings its own use case (a dataset of tasks, its judges, what its agent may
read, its gate) and evaluates, benchmarks and trains an agent on it, with
no code change. It also takes over every step spec 01 left open, planned
again for that (decision 14).

**Where things are.**

| What | Where |
|:--|:--|
| This spec, the active plan | `docs/my-specs/02-generalization.md` |
| Spec 01, closed | [`01-initial-implementation.md`](01-initial-implementation.md): what is done (phases 0, 1 and 2), decisions 1 to 9, the rules for every agent (its section 0), the lineup, the target architecture, repos and branches, the contribution catalogue C1 to C18 and C30 to C34, sandboxing, costs, the opening comments. All of it still holds unless this spec changes it |
| The evidence | [`../research.md`](../research.md). For this spec: section 4, "What the harness models for any use case"; section 5, "Use cases, data and gates in EvalHub"; section 7, the agent catalog's artifacts; section 8, the `openshift-eval` branch `generalization` |
| PR texts | [`../pr-drafts.md`](../pr-drafts.md) |
| The first version's generalization | `~/Projects/Github/lukaskellerstein/openshift-eval`, branch `generalization`, worktree `.worktrees/generalization`: its spec `docs/my-specs/03-generalization.md` and its phase 1 (`tasks/support/`, `flywheel/task.py`), built and checked on the laptop. Its "task" is our use case, its "case" our task. Not committed on 2026-10-14 |
| Forks, clones, the cluster | Spec 01, sections 0 and 5 |

**Done, in spec 01.** Phase 0, the agent's own identity, cluster-admin on
`cluster-nm8mw`. Phase 1, Open Data Hub 3.6.0-ea.2 with the dashboard,
EvalHub and MLflow, and the gateway on EnMaaS. Phase 2's C1 to C4, C6 to
C9 and C30 to C34 (the upstream bugs found on the way, fixed the same
evening), merged into the harness fork's `flywheel-integration` at
`e0e21d0` (2588 passed, twice). Phases 0 and 1 and C1 to C9 were
re-checked on 2026-10-14 between 19:10 and 19:25 CEST, before C30 to C34
merged at 21:40 CEST; the marks are in spec 01. The re-check found one
problem: the TrustyAI
operator restarts every few minutes, because KServe is `Removed` (C29,
section 7).

**How to start.** For an agent told "read this spec and implement it":

1. Work from this repo's main checkout, in a session started with
   `claude --no-worktree`. A `claude -w` session cannot run git in the
   fork clones (spec 01 section 0).
2. Read this section, the status table (section 5.1), the procedure and
   the phase you work on (section 6), and spec 01 sections 0 and 5 (the
   rules, the repos and branches). `.claude/CLAUDE.md` is loaded already.
3. Send Lukas one message first (rule `03-plan.md`): the open questions
   of section 9, each with its proposal as your pick, and the plan of the
   next step below, C19's design of section 4.7 included. Start on his ok
   to the plan; the answers to section 9 can come later, since the next
   step needs none of them. Ask, too, whether the cluster's auto-stop is
   far enough for the hour C29 needs on it (below, "The cluster").
4. Build each contribution by the procedure of section 6, "How a
   contribution is built".
5. After each contribution, write its state into the status table
   (section 5.1) and its PR text into `docs/pr-drafts.md`. This section's
   next step and `.claude/CLAUDE.md`'s State and Next step change only
   when the next step itself changes; a phase's status, when its DoD is
   checked.
6. Stop and ask Lukas before:
   - a push, a PR, an issue or a public comment (decision 15 times the
     issues);
   - a paid model run beyond one smoke call, with its cost (spec 01
     section 10);
   - creating or reading a Secret, the bucket's access key included;
   - an edit in `openshift-eval` (risk 2);
   - this repo's layout for phase 3 (question 6), or a sixth fork (spec 01
     section 5);
   - every other step marked "waits for" below.

**The next step.** It waits for no answer to section 9, only for
Lukas's ok to its plan. Side by side, one subagent per clone (spec 01
section 5):

- the TrustyAI operator: C29, then C14. C29 comes first, because the
  operator restarts every few minutes and slows every later change to the
  `EvalHub`. When C29 is merged, phase 2's cluster steps put it on the
  cluster.
- eval-hub: C10, then C12.
- the harness: C19, by the design of section 4.7 as Lukas approves it.

C10, C12 and C14 are spec 01's rows, with the notes in section 5.

Not next:

- C13 is skipped while ODH's MLflow works (spec 01 phase 3, and phase 1
  picked ODH's MLflow).
- C5 waits for Lukas to post the opening comment on PR #90 (spec 01
  section 13, not posted; its last comment is astefanutti's, of
  2026-06-10), then for astefanutti's answer.
- C11 waits for question 4. C20 to C28 wait for question 1. Phase 3 waits
  for questions 2, 5 and 6, and phase 5 for question 3.

**The cluster.** `cluster-nm8mw` auto-destroys on 2026-11-12. RHDP also
auto-stops it; the auto-stop read last was Thu 2026-10-15 02:23 CEST, and
only Lukas can move it (spec 01 section 0). Before cluster work that
takes hours, ask him whether the auto-stop is far enough. If the API times
out, ask him whether the cluster stopped before you debug anything.

**Rules for every agent.** Spec 01 section 0 holds, with decision 1's rule
for what is ours: "In the first place if it's possible, we should update
the upstream repos (whatever repo needs to be updated) and add the
functionality there. If it's not possible to add it there or if it needs
orchestration between two of these, then it belongs to our repo and to our
code."

## 1. Goal

Spec 01's goals 1 to 4 hold: evaluate, benchmark, train, a UI in the
dashboard. This spec adds the fifth:

5. **Any use case** (decision 10). A team brings its own use case, with
   its dataset of tasks, its judges and what its agent may read, and the
   flywheel evaluates, benchmarks and trains an agent on it. The support
   agent is the first use case, not the only one.

Done means the proof of phase 6: support end to end on the cluster, and a
second use case of another kind on the same code.

## 2. Decisions (10 on)

Decisions 1 to 9 are in spec 01 section 2 and still hold. 10 to 13 were
taken there on 2026-10-14 and moved here with this spec, word for word.

10. **Any use case, not only support** (2026-10-14). "It does not matter
    whether the agent should be trained or evaluated for a supporting use
    case, a lawyer use case, a kernel development use case, or any other
    given use case. We want to provide the platform for it so we have to be
    general." The support agent stays the first use case. The proof (phase
    6) includes a use case of another kind, after support runs end to end:
    the coding use case `pyfix` of `openshift-eval`'s generalization spec
    (section 0, "Where things are"), 12 small Python repositories with one
    bug each and hidden tests. If time runs short before the cluster's end
    (2026-11-12), that spec's text-only use case `copywriter` is the proof
    instead (Lukas, `ok`, 2026-10-14). Where use cases live and how they
    come in: decisions 11 and 13.
11. **Our own registry, the files in S3, import first** (2026-10-14). The
    flywheel API keeps the registry of use cases: "I would have our own
    API: the task register." Not a Kubernetes resource per use case ("there
    can be a lot of tasks") and no database of its own: the files sit in an
    S3 bucket ("I like the S3 bucket. It's fine with me."). The registry is
    the source; EvalHub collections are made from it ("Based on our tasks it
    would get propagated as Eval Hub collections"), and MLflow datasets when
    they are needed. Use cases and their tasks come in by import first: YAML
    files that people make elsewhere ("It's easier for users to generate
    the YAML files with some other agent somewhere else"), by upload and
    from git first, from Hugging Face datasets second (Lukas, `yes`,
    2026-10-14). The UI can create them too, but that is not the main way:
    "We should not force anyone to click so many times and do so much work
    to create all the tasks or items in the dataset." In these quotes, which
    came before decision 12, "task" means a use case, except in the last
    one.
12. **The words** (2026-10-14, Lukas's pick A). A **use case** is the
    whole: support, a lawyer's contract review, kernel development. Its
    **dataset** is its tasks, versioned with it (decision 13). A **task** is
    one item of the dataset: one support ticket, one contract clause, one
    bug to fix. The harness calls a task a "case" and keeps its own names
    (`cases/`, `per_case`, `annotations.yaml`). In this plan "ticket" stays
    for the tasks of the support use case. `openshift-eval`'s generalization spec says
    "task" for our use case and "case" for our task.
13. **One format for a task, and fixed versions** (2026-10-14, Lukas,
    `yes` and `A`). A use case is defined once: its judges, what its agent
    can read, its gate. Its tasks come in bulk: one YAML file per task, or
    the same fields as one JSONL line, one Hugging Face row or one file in a
    git folder.

    ```yaml
    id: sno-registry-removed      # unique; default: the file name
    split: train                  # optional; else the import picks one, balanced by tags
    tags: [plain-fix]             # optional
    input:                        # what the agent gets; any keys
      ticket: "Hi, I installed OpenShift 4.20.3 …"
    expected:                     # what only the judges see; any keys
      must_mention: [managementState, "oc patch"]
    files: [screenshot.png]       # optional: files for the agent
    ```

    Under decision 1 the harness gets a reader for this format (C19), so
    the import only checks, versions and stores. Every import makes a new,
    fixed version of the whole use case: its tasks, judges, resources and
    gate, because a judge change moves the scores as much as a new task
    does. An import with no change makes no new version. A run records the
    version's number and hash, nothing is overwritten, and old versions
    stay: "we will have some old runs and we need to still reference and
    show what the previous kind of dataset was."
14. **Specs instead of one plan** (2026-10-14). `PLAN.md` became spec 01,
    `docs/my-specs/01-initial-implementation.md`, with what is done marked;
    this spec 02 takes over every open step of spec 01 (Lukas, `yes` to "A:
    spec 02 takes over every open step"); there is no `PLAN.md` at the top
    any more (Lukas, `no` to keeping a short one). `.claude/CLAUDE.md` names
    the active spec. Decisions keep one numbering across the specs.
15. **Issues come with the PRs** (2026-10-14, Lukas, `ok` to "A: build
    now. Open the issues with the PRs in phase 7, and add the issue links
    to the commit messages then"). eval-hub asks for an issue before any
    work starts, and the TrustyAI operator for an issue linked from every
    `fix` and `feat` commit (`docs/research.md` section 5, "Issue rules").
    Under decision 2 each contribution is built on its fork branch first;
    its issue is opened in phase 7, with Lukas's go each time, and the
    commit messages get the link when the branch is rebased for its PR.
    For an architectural change in eval-hub, its PR is accepted only after
    the issue gets `status/accepted`, so the discussion can still change
    code already built.

## 3. What changes, and why

What spec 01 planned around the support agent, and the facts that shape
the change (`docs/research.md`, sections 4, 5 and 8):

- Spec 01 phase 4 ported `datasets/support/` from `openshift-eval` `main`,
  where the use case is hard-coded in every layer: the judges' weights in
  `run_eval.py`, the failure report in `adjust.py`, the adjuster's prompt,
  three backends, the release gate, the console's labels, the image's
  `COPY eval` (the table in section 2 of `openshift-eval`'s generalization
  spec). Its branch `generalization` moved most of it into a pack its code
  reads, but in its own code.
- Spec 01 planned C11 as `openshift-eval`'s provider: one EvalHub
  benchmark, `support`, with the dataset baked into the image. Every new use
  case would need a new image.
- Spec 01 phase 5's Dataset and One ticket boards show tickets, a knowledge
  base and policies.
- The harness reads a dataset only as a folder of case folders. It has a
  combined score (`reward:`) but writes it nowhere into `summary.yaml`, has
  no splits, and takes the brain from the project root without declaring
  it.
- EvalHub fetches test data from S3, git, a PVC or Hugging Face into
  `/test_data` and records `resolved_sha`; a collection entry carries a
  weight, a primary score, a pass threshold, parameters and the data
  reference; a job passes at a threshold that defaults to 0.5; there is no
  object for an agent under test.

## 4. The design

### 4.1 The objects

- **Use case**: what to do and how it is judged. Its definition (judges,
  what the agent may read, the gate) and its dataset, versioned together
  (decision 13).
- **Task**: one item of the dataset, in the format of decision 13.
- **Agent**: a harness × a brain × a model × its settings. A brain is
  trained on one use case but is not part of it.
- **Run**: an evaluation (an agent on a use case version), a benchmark (a
  grid on one use case version) or a training run (the loop on one use
  case version, which makes brains).

### 4.2 The files of a use case (proposal, question 5)

```text
<use case>/
├── usecase.yaml   ours: title, description, the input key that is the prompt, the
│                  task label for the UI ("ticket"), the input keys the UI shows,
│                  the brain's limits, the adjuster's slots (role, causes, hidden note)
├── eval.yaml      the harness's: the judges, the gate, the workspace files
├── tasks/         one YAML file per task (decision 13); tasks/<id>/ for a task's files
├── tasks.jsonl    instead of tasks/: one task per line
├── resources/     what the agent may read (support: the knowledge base)
└── hidden/        what only the judges see (support: the policies)
```

`usecase.yaml` holds only what no upstream project has a field for: the
words of the UI, the brain and the adjuster belong to our loop. Everything
the harness can hold goes into `eval.yaml` (decision 1).

### 4.3 The registry (decision 11; the layout is a proposal)

The flywheel API keeps it, in one S3 bucket:

```text
s3://<bucket>/usecases/<name>/
  usecase.json            the registry entry: title, source, current version, versions
  versions/<n>/           one fixed version
    version.json          number, content hash, source (repo and commit, or file
                          name), time, tasks per split, the diff to version n-1
                          (tasks added, removed, changed)
    usecase.yaml  eval.yaml  tasks/  resources/  hidden/
```

- **Import**: upload and git first, Hugging Face second (decision 11). A
  Hugging Face dataset needs a column mapping, since public datasets do not
  use our field names: for example `input.question: question`,
  `expected.reference: answer`.
- **Checks on import** (proposal): every task against the use case's JSON
  Schema of `input` and `expected` (C26); on any error the whole import is
  refused, with the file and the field named, so a version is never half
  written.
- **Versions** (decision 13): a new version only when the content hash
  changes; never deleted in the first build. Runs carry the MLflow tags
  `usecase`, `usecase_version`, `usecase_hash` (proposal; `openshift-eval`
  tags `task`, `task_version`, `task_hash` the same way). Benchmark reuse
  counts a run only for the same hash.
- **Projections**: one EvalHub collection per use case (proposal): per
  split one entry of the harness provider, with `test_data_ref.s3` at the
  version's folder, `parameters.split`, and `pass_criteria` from the gate.
  The API writes it on every import and tags it `managed-by:
  agent-flywheel`; an edit in EvalHub's UI is lost at the next import. An
  MLflow evaluation dataset when one is needed, through the harness's
  `/eval-mlflow` `sync_dataset.py`.

### 4.4 One Score step, end to end (proposal, question 4)

1. The controller creates one EvalHub job on the use case's collection,
   with one benchmark entry per split it scores (train, validation). Each
   carries `test_data_ref.s3` at the version and `parameters.brain`, a
   reference to the brain's MLflow artifact.
2. EvalHub's init container copies the version into `/test_data`.
3. The adapter (C11) runs the harness on the split, with the brain
   applied.
4. The harness writes `summary.yaml` with every judge, a reason per task,
   the combined score and the gate's verdicts (C20).
5. The adapter reports the combined score as the benchmark's
   `primary_score`, each judge as a metric, and the reasons to MLflow.
6. EvalHub sets `test.pass` from the use case's `pass_criteria`; our UI
   shows the per-judge and per-task rules beside it.

### 4.5 Where each part lives (decision 1's rule)

| Part | Home | Contribution | State |
|:--|:--|:--|:--|
| Reader for the task format | harness | C19 | decided (decision 13) |
| Combined score and gate in `summary.yaml` | harness | C20 | proposal |
| Splits | harness | C21 | proposal |
| Deterministic judges (contains, forbidden, cites, sections, regex, exact, numeric, JSON Schema, diff limits) | harness built-ins | C22 | proposal |
| Hidden tests after the agent | harness | C23 | proposal |
| One permission profile for every runner (edit, shell, web) | harness | C24 | proposal |
| The diff as output of a sealed workspace | harness | C25 | proposal |
| JSON Schema of a task, warning on unknown keys | harness | C26 | proposal |
| The adapter takes any use case version | eval-hub-contrib | C11, changed | proposal |
| The full `TestDataRef` in the dashboard's EvalHub module | odh-dashboard | C27 | proposal |
| `test_data_ref` and `resolved_sha` on the EvalCard | eval-hub | C28 | proposal |
| Registry, import, versions, the collection and the MLflow dataset | this repo, the flywheel API | — | decided (decision 11): it joins S3, EvalHub and MLflow |
| The adjuster's slots, the brain's limits, the UI's words | this repo, `usecase.yaml` | — | proposal: our loop and our UI only |
| What the agent reads, what only the judges see, the hint | harness `workspace.files`, judge `context:`, `execution.prompt` | none, exists | — |

### 4.6 The environment of a use case

The planned runner image (spec 01 section 4) holds the harness, the three
agent CLIs, git, Python and make: enough for support, `copywriter` and
`pyfix`. A use case with its
own toolchain registers its own tenant provider with its own image
(EvalHub's "Bring Your Own Provider") and asks for CPU and memory per
benchmark entry (`BenchmarkHardwareConfig`, or an ODH `HardwareProfile`);
that path needs C10. Kernel development (a 5 GB tree, many CPUs, root for
some tests) also needs the sandbox of EvalHub's ADR 0001 (spec 01 section
8), so it is out of scope while this cluster lives.

### 4.7 C19's design (proposal, for the plan step)

What the harness does today (`docs/research.md` section 4, "Where the
dataset is read"): thirteen files read `dataset.path` as a folder of case
folders, each in its own process, with no shared loader; `workspace.py`
deletes the run's temp folder when it starts; a case's other files reach
the agent only through `dataset.workspace.files`; the first design
principle is "scripts just move files", with no hardcoded field names.
The proposal, point by point; the plan step settles each with Lukas:

1. **Convert, do not rewrite the readers.** One converter writes the task
   format of decision 13 as case folders: `<id>/input.yaml` from `input`,
   `<id>/annotations.yaml` from `expected`, and the task's own YAML as
   `<id>/task.yaml`, which keeps `split` and `tags` for C21 to read. The
   names inside `input` and `expected` stay free, so the principle holds;
   the six task keys are the new contract, and the PR says so.
2. **What `dataset.path` names.** A folder whose top level holds task YAML
   files (`<id>.yaml`, a task's files in `<id>/` beside it, section 4.2),
   or one `.jsonl` file. A folder with both task files and case folders is
   an error. Case folders keep working.
3. **A task's files reach the agent.** The converter adds them to that
   case's workspace files, the same way `dataset.workspace.files` stages
   files, so the agent sees them.
4. **One helper, every site.** A `resolve_dataset(config)` in
   `agent_eval/` returns the case-folder path; every site that reads
   `dataset.path` (the thirteen files, the raw reads in `execute.py` and
   `adapter.py` included) calls it. The converted folder is a cache keyed
   by the content hash, under `<tmp>/agent-eval/datasets/<hash>/`, outside
   any run's folder, so `workspace.py`'s cleanup does not touch it and
   every process finds the same one.
5. **On EvalHub.** Both downloads end at the same helper: EvalHub's init
   container copies the version to `/test_data` (C11's path, section 4.4),
   and the harness's own `s3_dataset.py` downloads a prefix (its EvalHub
   adapter's path); `s3_dataset.py` also accepts task files at the
   prefix's top level instead of reading them as cases.
6. **Upstream's way.** A feature, so the branch carries a spec folder,
   `specs/015-task-format/` (spec, plan, tasks), as upstream's spec-driven
   work does. The docs go into `website/`, not `CLAUDE.md`: `AGENTS.md` is
   about 100 tokens under skillsaw's budget (`docs/pr-drafts.md`).
7. **Tests.** The same tasks in each format and written by hand as case
   folders give the same case folders, through `workspace.py`, `score.py`
   and both downloads; an existing case-folder dataset gives byte-equal
   results.

If question 5 moves a task's files elsewhere, only point 2 changes.

## 5. Contribution catalogue

C1 to C18 and C30 to C34 are in spec 01 section 7. Done there: C1 to C4, C6 to C9 and C30 to C34.
Still open from there, unchanged unless this section says so: C5, C10,
C12 to C18. The rows below are new or changed; the notes after the table
update spec 01's open rows, and section 5.1 holds the status of all of
them.
C19 and C29 are decided (C29: Lukas, `ok`, 2026-10-14); C11's new shape
is a proposal until question 4 is answered, C20 to C28 until question 1
is.

| Id | Repo | Gap today (source) | Change | Replaces |
|:--|:--|:--|:--|:--|
| C11 (changed) | eval-hub-contrib | Spec 01 planned one benchmark per use case, its dataset in the image | One benchmark of the harness provider for any use case: the version from `/test_data`, `parameters.split`, `parameters.brain`; the combined score as `primary_score`, each judge as a metric, a reason per task to MLflow | A new image per use case |
| C19 | harness | A dataset is a folder of case folders only: no reader for one file per task, JSONL or Hugging Face (`docs/research.md` section 4) | A reader for the task format of decision 13: one YAML file per task or one JSONL line per task, with `id`, `split`, `tags`, `input`, `expected`, `files`; the case folders keep working | Our own import writing case folders |
| C20 | harness | `reward:` exists but `summary.yaml` gets only `judges`, `per_case`, `judge_usage`; `thresholds` exit 1 and none targets the combined score (`score.py:3841-3910, 4066-4072`) | Write the combined score and the threshold verdicts into `summary.yaml`; a threshold on the combined score and a per-task minimum; a report-only mode | The weights and the release gate in our code |
| C21 | harness | No splits: `--cases` takes exact ids (`workspace.py:46, 69-71`); PR #73's `--split` is not merged and writes to `tmp/` | Named splits from the task's `split`, `--split <name>`, a summary per split; agreed with PR #73's authors | Our split loader |
| C22 | harness | Five built-in judges, none for the common text checks (`website/reference/builtin-judges.md`) | Built-ins with arguments: contains (any-of groups), forbidden (negation-aware, per clause), cites, sections and length, regex, exact, numeric, JSON Schema, diff limits | Python `check:` bodies copied from use case to use case |
| C23 | harness | Tests the agent never saw have no place to run after it (check first whether an `after_each` hook with a `check:` judge covers it) | Hidden files staged into the workspace after the agent exits, a command, its exit code and output tail as the verdict | Our runner scripts' verify step |
| C24 | harness | Each runner takes its own permissions (`runner.settings`, `permission_mode`, the raw `permissions` map) | `runner.permissions: {edit, bash, web}`, mapped by claude-code, codex, opencode (C5) and cursor | Per-runner switches in our scripts |
| C25 | harness | `_modified/` comes from the case workspace's git snapshot (`workspace.py:240-290`); a sealed workspace (C3) is to check | The diff and the changed files collected from a sealed workspace too, locally and in the EvalHub pod (with C7) | Our runner scripts' diff |
| C26 | harness | `dataset.schema` is prose, never parsed; unknown top-level keys are ignored (`config.py:1938-2620`) | A JSON Schema for a task's `input` and `expected`, checked by `validate_eval.py`; a warning on unknown keys | Our strict loader |
| C27 | odh-dashboard (`packages/eval-hub`) | Its BFF's `TestDataRef` holds S3 only, no `type`; the form sends no `bucket` (`evalhub_client.go:204-212`, `buildEvaluationRequest.ts:64-78`) | The full `TestDataRef`: S3 with `bucket`, git, PVC, Hugging Face, `type` | Collections made only through the API |
| C28 | eval-hub | The EvalCard leaves `test_data_ref` out (`pkg/cards/evaluation_card.go:64`) | `test_data_ref` and `resolved_sha` on the card | — |
| C29 | trustyai-service-operator | The TrustyAIService controller watches KServe's `InferenceService` with no check (`controllers/tas/trustyaiservice_controller.go:317`); with KServe `Removed` the manager, and the EvalHub controller in it, restarts every few minutes (`docs/research.md` section 5) | Watch `InferenceService` only when its API is served, as the EvalHub controller does for Kueue (`kueue_workloads_discovery.go:26`); reuse `isInferenceServiceCRDPresent` (`controllers/tas/inference_services.go:32`), which upstream PR #899 added without gating the watch. ✅ when the tests are green with and without KServe's CRD and it is merged; the hour on `cluster-nm8mw` with no new restart is phase 2's DoD | KServe `Managed` only to keep the operator up |

Notes on spec 01's open rows, read 2026-10-14 evening in the clones'
`upstream/main`: eval-hub `540676f` (upstream's `main` was `3f7b173` by
then, not fetched), operator `4fa5c74`. `git fetch upstream` first, and
check each line again:

- C5: the opening comment for PR #90 (spec 01 section 13) is not posted,
  and the PR's last comment is astefanutti's, of 2026-06-10. So C5 waits
  for Lukas to post it, then for astefanutti's answer.
- C10: `K8sRuntime` is at `pkg/api/providers.go:118-133`. Seven fields
  have no json tag: the four resource fields are dropped, and `image`,
  `entrypoint` and `env` come back as `Image`, `Entrypoint` and `Env`
  (`docs/research.md` section 5). Tag all seven to match
  `docs/openapi.json`, and say in the PR that the response changes.
- C12: `internal/eval_hub/runtimes/local/local_runtime.go:414`; the
  comment above it (`:403-413`) ignores the exit on purpose. How to tell
  "exited without a report" is the plan step's question: read the
  benchmark's stored status after `cmd.Wait()`.
- C13: skipped. Spec 01 phase 3 skips it if phase 1 picked ODH's MLflow
  and it works, and phase 1 picked it. It comes back only if ODH's MLflow
  refuses the `MLFLOW_WORKSPACE` header.
- C14: the file is
  `controllers/evalhub/evaluation_job_failure_reconciler.go`: the comment
  at `:113-114` and `terminatedAdapterNeedsOperatorReport` at `:950`.
  Upstream ignores the exit because an adapter often posts `failed` after
  a normal run. So post `failed` on a non-zero exit with no new GET: the
  server keeps the first terminal event and answers a later one with 409
  `job_can_not_be_updated` (`docs/research.md` section 4), which the
  reconciler treats as done.

### 5.1 Status

The one place a contribution's state is written. ⬜ not started, ▶️ in
progress, ✅ merged into its repo's `flywheel-integration`, its PR not
opened yet (phase 7); skipped, with the reason. "Head" is the branch's
head commit and, after the merge, `flywheel-integration`'s.
Spec 01's ✅ rows (C1 to C4, C6 to C9, C30 to C34) stay in spec 01
section 7.

| Id | Repo | Branch | Head | State | Waits for |
|:--|:--|:--|:--|:--|:--|
| C29 | trustyai-service-operator | — | — | ⬜ | Lukas's ok to the plan (section 0) |
| C19 | agent-eval-harness | — | — | ⬜ | Lukas's ok on section 4.7 in the plan step |
| C10 | eval-hub | — | — | ⬜ | Lukas's ok to the plan (section 0) |
| C12 | eval-hub | — | — | ⬜ | Lukas's ok to the plan (section 0) |
| C14 | trustyai-service-operator | — | — | ⬜ | C29 in the same clone |
| C13 | eval-hub | — | — | skipped | ODH's MLflow refusing the header |
| C5 | agent-eval-harness | — | — | ⬜ | Lukas's comment on PR #90, then astefanutti |
| C11 | eval-hub-contrib | — | — | ⬜ | question 4 |
| C20 to C26 | agent-eval-harness | — | — | ⬜ | question 1 |
| C27 | odh-dashboard | — | — | ⬜ | question 1 |
| C28 | eval-hub | — | — | ⬜ | question 1 |
| C15 to C18 | odh-dashboard | — | — | ⬜ | phase 5 (question 3); C16 to C18 as spec 01 phase 5 step 2 places them |

## 6. Phases

Each phase ends with its Definition of Done, checked and written into its
status. Phases 1 and 2 run side by side: they work in different repos, and
section 0's next step takes items of both. From phase 3 on, a phase starts
when the phases before it have their DoD checked. The phases continue
spec 01's:

| This spec | Spec 01 |
|:--|:--|
| Phase 1, harness contributions | Phase 2, the open rest |
| Phase 2, EvalHub, contrib, operator | Phase 3 |
| Phase 3, the registry and the glue | Phase 4 |
| Phase 4, Hugging Face import | new |
| Phase 5, the dashboard module | Phase 5 |
| Phase 6, the proof | Phase 6 |
| Phase 7, the PRs | Phase 7 |
| Phase 8, where the loop lives | Phase 8 |

### How a contribution is built

The way spec 01 phase 2 built C1 to C9 and C30 to C34, written down for
every repo. Spec 01 sections 0 and 5 hold.

1. **The clone.** `~/Projects/Github/lukaskellerstein/forks/<repo>`, then
   `git fetch upstream`. No worktrees: the branch is switched in the clone
   itself, never two subagents in one clone at a time, and between tasks
   the clone sits on its `flywheel-integration`, or on `main` before it has
   one. Subagents run in parallel only in different clones.
2. **The branch.** From the newest `upstream/main`, named like spec 01
   phase 2's branches (`fix/<what>`, `feat/<what>`). A branch that needs
   another one starts from it, as C7 started from C4.
3. **Upstream's rules.** Read the repo's `CLAUDE.md`, `AGENTS.md` and
   `CONTRIBUTING.md` first. They win, except for when issues are opened
   (decision 15): commit without an issue link, which phase 7 adds.
   Commits are conventional commits everywhere; eval-hub also wants
   `git commit -s` and, from Claude Code, the trailer
   `Generated with: Claude Code` (its `AGENTS.md`, "Git commits"). Search
   upstream's open PRs and issues for the same gap first
   (`gh pr list --search`, `gh issue list --search`); if one exists, tell
   Lukas before building.
4. **The baseline.** Run the repo's tests on `upstream/main` before any
   change, and write the counts into the phase's status. If the run
   changes tracked files (the operator's `make test` regenerates
   manifests), never commit that drift.
5. **The gap first.** A test that fails on `upstream/main` and shows the
   gap; for the harness, with a fake agent, as spec 01 phase 2 did.
6. **The fix.** The change, its tests, the repo's checks green. The agent
   reviews every subagent's diff and runs the suite itself.
7. **The merge.** Into the repo's `flywheel-integration`, as a plain merge
   commit; a repo without one gets it from `upstream/main` before its
   first merge. A conflict is resolved so that both changes hold, with a
   test for the result. Run the merged suite twice.
8. **The bookkeeping**, as section 0 step 5 says: the row in section 5.1
   and a section in `docs/pr-drafts.md` (repo, branch, head commit, PR
   text, and the issue text where the repo asks for one). A new folder
   in this repo gets its section in `.claude/rules/05-implement.md`.

A subagent's brief carries the repo and the branch, its row of section 5
(or of spec 01 section 7) with the notes, steps 1 to 7, and the rules: no
push, no PR, no issue, no comment, no commit on `main`, no change outside
its clone. It reports the head commit, the test counts and what it found
beyond the plan.

| Repo | Tests and checks | Known on 2026-10-14 |
|:--|:--|:--|
| agent-eval-harness | `make test` in the clone's `.venv` (Python 3.12, `uv pip install -e ".[all,test]"`); CI's skillsaw 0.10.0 `--strict`; `mkdocs build --strict` | `flywheel-integration` `e0e21d0`: 2588 passed (spec 01 phase 2 status) |
| eval-hub | `make clean test-all`, `pre-commit run --all-files` | Never run here. `go.mod` asks for Go 1.26.7, this Mac has 1.26.5; `pre-commit` is not installed |
| trustyai-service-operator | `make test` (`manifests generate fmt vet envtest`), `go mod tidy` | Never run here. envtest downloads its binaries from GitHub releases (`Makefile:59`, `:270-278`); the sandbox may refuse their host. Its `CLAUDE.md:5` names Go 1.23 and controller-runtime 0.17, but `go.mod` has Go 1.26.0 and 0.22.5: trust `go.mod` |
| eval-hub-contrib | `make test-<name>`, the adapter's offline `smoke_test.py` | Never run here |

A missing tool goes into the clone's own environment (its `.venv`, Go's
toolchain download), not onto the machine. If the sandbox refuses a
download, tell Lukas the host: `.claude/settings.json` holds the network
allowlist, and only he changes it.

### Phase 1: harness contributions

In the `agent-eval-harness` fork, by the procedure above. C19 first, with
the design of section 4.7; C5 when its wait ends (section 5.1); C20 to C26
once question 1 is answered.

DoD:

- [ ] every branch green on `make test`
- [ ] `flywheel-integration` merges them all and stays green, run twice

Status: not started.

### Phase 2: EvalHub, contrib, operator

Spec 01 phase 3, with C11 in its new shape and the notes of section 5:
C29 first, since the operator it fixes reconciles the `EvalHub` this phase
changes; then C14 in the same clone, and C10 and C12 in eval-hub; C13 is
skipped; C11 after question 4; C27 and C28 if question 1 takes them.

On the cluster:

1. Build our images on the cluster, from each clone's
   `flywheel-integration`, with binary BuildConfigs
   (`oc start-build --from-dir`), so nothing is pushed. The BuildConfigs
   go in `deploy/builds/`, a folder this phase names (rule
   `05-implement.md`).
2. Point ODH at them on the ODH operator, through the Subscription's
   `spec.config.env` in `deploy/platform/operator/`:
   `RELATED_IMAGE_ODH_TRUSTYAI_SERVICE_OPERATOR_IMAGE` and
   `RELATED_IMAGE_ODH_EVAL_HUB_IMAGE`. A patch on a lower level is
   overwritten by its owner (`docs/research.md` section 5, "What C29 can
   reuse"). Whether the env reaches the module is section 8's first check.
   The Subscription change restarts the ODH operator, which reconciles
   every module: apply it when nothing else runs on the cluster, and
   watch `default-dsc` come back.

DoD:

- [ ] each repo's tests green, with the baseline and the final counts here
- [ ] on the cluster, ODH runs our operator image (C29, C14) and our
      EvalHub server image (C10, C12); the operator has no new restart for
      an hour, and EvalHub answers `/api/v1/health`
- [ ] the adapter image (C11) builds on the cluster and passes its offline
      smoke test

The end-to-end check, an EvalHub job with our adapter on a use case
version read from S3, needs the bucket and the registry: it is phase 3's
DoD.

Status: not started.

### Phase 3: the registry and the glue

Spec 01 phase 4, on the registry of decision 11. The layout of this repo is
agreed with Lukas first (question 6). The port reads `openshift-eval`'s
branch `generalization`, which is not committed (risk 2): ask Lukas to
commit it there before the port starts; an edit in `openshift-eval` is
his.

1. The S3 bucket: verify first (section 8); its access key Secret is asked
   for before it is created.
2. The flywheel API (`services/flywheel-api/`, ported from `openshift-eval`
   `ui/server/`): the registry, import by upload and from git, versions,
   the EvalHub collection; then the API the dashboard module forwards to
   (spec 01 decision 6).
3. The loop (`flywheel/`), ported from `openshift-eval`: the controller,
   the Adjust backends, keep or revert in code; the generic parts from its
   branch `generalization` (the failure report, the adjuster's slots, the
   brain's limits); one Score backend, EvalHub with C11.
4. The runner image (`images/runner/`), the harness from the fork's
   `flywheel-integration` branch.
5. Support as the first use case: `openshift-eval`'s `tasks/support/` in
   the task format, imported from git.

DoD:

- [ ] support imported as version 1; the same import again makes no
      version 2
- [ ] a changed import makes version 2, and version 1 stays readable
- [ ] on the cluster, an EvalHub job with our adapter runs the harness on
      version 1, read from S3, and logs a reason per task to MLflow
- [ ] a free smoke loop on the cluster through EvalHub on version 1; its
      MLflow records have the shape spec 01 phase 4 asked for, plus the
      version tags

Status: not started.

### Phase 4: Hugging Face import

The second import source of decision 11: a dataset id, a revision and a
column mapping.

DoD:

- [ ] one public Hugging Face dataset imported as a use case version, its
      mapping checked task by task
- [ ] an evaluation runs on it through EvalHub

### Phase 5: the dashboard module

Spec 01 phase 5, steps 2 to 6 as written there (where it sits, the
package, the registration, the build, the dev loop). Step 1, design first,
changes: every screen goes on the Design canvas for Lukas's review before
it is built, with the words of decision 12 and the versions of decision 13.
New boards: Use cases (the list, an import), Use case (its versions and
their diff, its tasks, judges, gate, resources), Task. The Dataset and One
ticket boards of spec 01 become these. Question 3.

DoD:

- [ ] on the cluster, the dashboard shows Develop & train › Agent flywheel
      and its pages
- [ ] Lukas imports a use case from the dashboard, starts an evaluation and
      a smoke training run on it
- [ ] the pages show the same numbers as MLflow

### Phase 6: the proof

Spec 01 phase 6, on the `flywheel-integration` branches of every fork:

1. A record comparison like `openshift-eval`'s phase tests, with fakes for
   the agents and the gateway.
2. One free loop on the local Gemma with the local judge (laptop).
3. One paid smoke run on the OpenAI model of decision 9, through EnMaaS
   (asked for first, with its cost).
4. The same smoke run on the cluster, started from the dashboard module.
5. The second use case of decision 10, after steps 1 to 4 pass for
   support: a smoke training run of `pyfix` on the cluster, started from
   the dashboard module. `pyfix` needs C23 to C25; without them, or if time
   runs short, `copywriter`. A paid run is asked for first, with its cost.
   Neither use case exists yet: `openshift-eval`'s generalization spec
   describes them (its phases 2 and 3), and its `tasks/` holds only
   `support` (2026-10-14). This step writes the chosen one in the task
   format, next to support's source (question 6), and imports it.

Step 1's tests lived in `openshift-eval`'s gitignored `tmp/tests/`; they
are written again here, from what its `PLAN.md` section 0 says they
checked (spec 01 phase 6).

DoD:

- [ ] all five green, with the run ids written here

### Phase 7: the PRs

Spec 01 phase 7, for every contribution of both specs: one PR per branch,
rebased on `upstream/main`, in the order of the catalogues, each with its
own tests and evidence; the opening comments of spec 01 section 13 first.
Each PR's issue is opened with it, where the repo asks for one, and the
rebased commits link it (decision 15). The PR texts are in
`docs/pr-drafts.md`.

DoD:

- [ ] every PR opened with Lukas's go

### Phase 8: where the loop lives

Spec 01 phase 8, unchanged.

## 7. Risks

1. **Time.** A coding use case changes what the agent may do (edit files,
   run a shell) and how it is judged (hidden tests, a diff), and the
   cluster is deleted on 2026-11-12. `copywriter` is the smaller fallback
   (decision 10).
2. **The port's source is not committed.** `openshift-eval`'s branch
   `generalization` exists only in its worktree. Commit it there before
   phase 3 ports from it.
3. **The bucket dies with the cluster.** The git sources survive; a
   re-import rebuilds every version but its number. A lasting setup points
   the API at an S3 outside the cluster.
4. **EvalHub's default gate is 0.5.** Every collection the API writes sets
   its `pass_criteria`.
5. **The harness ignores unknown keys.** A typo in `eval.yaml` is silent
   until C26.
6. **The TrustyAI operator restarts every few minutes** on this cluster
   (C29; 204 restarts by 2026-10-14 21:55 CEST). It reconciles the
   `EvalHub` only between restarts, so a change to the `EvalHub` resource
   (phase 2: our server image) can take minutes to land, and `default-dsc`
   flips between Ready and `Not Ready`. Check the operator before reading a
   slow change as a fault of ours.
7. **The cluster stops when nobody moves its auto-stop.** RHDP stops
   `cluster-nm8mw` at its auto-stop time, and only Lukas can move it
   (section 0, "The cluster"). A stopped cluster looks like a timeout.
8. Spec 01 section 11 holds as well: early-access ODH, a module that may
   never merge, the single node's disk, the version lock, a newer harness
   moving the scores, EnMaaS as the one model service.

## 8. Verify first

- Phase 2: whether `RELATED_IMAGE_ODH_TRUSTYAI_SERVICE_OPERATOR_IMAGE` and
  `RELATED_IMAGE_ODH_EVAL_HUB_IMAGE` in the ODH Subscription's
  `spec.config.env` reach `trustyai-operator-module-controller-manager`'s
  env, and from there the operator and the `evalhub` pod
  (`docs/research.md` section 5, "What C29 can reuse"). Before the first
  build, compare the sources: ODH's EvalHub is built from
  `opendatahub-io/eval-hub` `stable`, 89 commits behind upstream `main`
  (`docs/research.md` section 5, "Versions"); read the operator image's
  `oc image info` labels the same way. The sandbox may refuse `quay.io`:
  then read them from a pod on the cluster, or ask Lukas. ODH may build the
  operator from an `opendatahub-io` fork the clone has no remote for;
  adding one is not pre-approved, so ask. If our build from upstream
  `main` does not run under ODH 3.6.0-ea.2, ask Lukas before basing
  `flywheel-integration` on the commit ODH built from.
- Whether EvalHub's S3 init container fetches a folder prefix or one object
  (`test_data_ref.s3` has `bucket`, `key` and `secret_ref`, all required,
  `pkg/api/evaluations.go:163-167`); if one object, each version is also
  kept as one archive. The `secret_ref` is the bucket's access key Secret:
  asked for before it is created.
- Whether an `ObjectBucketClaim` works on `cluster-nm8mw`: the storage
  class `openshift-storage.noobaa.io` and the claim CRD exist, NooBaa in
  `openshift-storage` is `Ready`, and no claim exists yet (2026-10-14).
- Whether ODH's MLflow, with workspaces on, serves MLflow evaluation
  datasets.
- Whether the cluster reaches Hugging Face (phase 4).
- Whether the real agents run clean through the gateway on EnMaaS (spec 01
  decision 9). Each agent's request shape is checked; a full run of Claude
  Code, Codex and OpenCode is not. Phase 6 step 3 is the first.
- Spec 01 section 12 holds as well.

## 9. Open questions

Each with the agent's proposal; the agent asks all six at the start, in
one message (section 0). Questions 1 and 4 block phases 1 and 2;
questions 2, 5 and 6 block phase 3; question 3 blocks phase 5.

1. **Which other gaps go to which project?** Proposal: the table of
   section 4.5, as C20 to C28 of section 5.
2. **The registry's API.** Proposal: `GET /api/usecases`,
   `GET /api/usecases/{name}`, `GET /api/usecases/{name}/versions/{n}` (the
   tasks, the judges, the diff to the version before), and
   `POST /api/usecases/{name}/imports` with an upload, `{git: url, ref,
   path}` or `{hf: dataset, revision, mapping}`, answering with the new
   version, "unchanged", or the errors by file and field. No delete in the
   first build. The module's BFF forwards to it (spec 01 decision 6).
3. **The screens.** Proposal: the boards of phase 5 on the Design canvas.
4. **C11's new shape.** Proposal: section 4.4.
5. **The files of a use case.** Proposal: section 4.2.
6. **This repo's layout for phase 3.** Proposal: `services/flywheel-api/`
   (the registry and the API), `flywheel/` (the loop), `images/runner/`,
   `usecases/support/` (the support use case's source in git, imported like
   any other), `deploy/` (the bucket claim, the API, the Jobs).

## 10. Sources

- `docs/research.md` sections 4, 5, 7 and 8, with file and line, read on
  2026-10-14 at agent-eval-harness `upstream/main` `175eed5`, eval-hub
  `540676f`, odh-dashboard `7140a4f`, trustyai-service-operator `4fa5c74`.
- `openshift-eval` branch `generalization`: `docs/my-specs/03-generalization.md`,
  `tasks/support/task.yaml`, `flywheel/task.py`, its `PLAN.md` row
  "Generalization, phase 1".
- The session of 2026-10-14 in this repo, where Lukas took decisions 10 to
  14.
