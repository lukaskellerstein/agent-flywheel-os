# Spec 02: Generalization, one flywheel for any use case

Status: the active plan, written 2026-10-14. Decisions 10 to 16 are Lukas's
(section 2); decision 16 (2026-10-15) answers the open questions of
section 9 and takes C19's design. What is still marked **proposal** is not
decided yet. This spec carries every open step of spec 01
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
merged at 21:40 CEST; the marks are in spec 01. The gaps C30 to C34's
subagents found on the way are C35 to C39 here (Lukas, 2026-10-14: they
belong in this spec, since none has to be done before it starts). The
re-check found one problem: the TrustyAI
operator restarts every few minutes, because KServe is `Removed` (C29,
section 7).

**How to start.** For an agent told "read this spec and implement it":

1. Work from this repo's main checkout, in a session started with
   `claude --no-worktree`. A `claude -w` session cannot run git in the
   fork clones (spec 01 section 0).
2. Read this section, the status table (section 5.1), the procedure and
   the phase you work on (section 6), and spec 01 sections 0 and 5 (the
   rules, the repos and branches). `.claude/CLAUDE.md` is loaded already.
3. Lukas answered section 9 on 2026-10-15 (decision 16), and the step
   he approved then is done. He gave his go for the next step below on
   2026-10-16 ("you can continue with the work"). Before cluster work
   that takes hours, ask him whether the auto-stop is far enough (below,
   "The cluster").
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
   - a top-level folder beyond the layout of decision 16, or a sixth fork
     (spec 01 section 5);
   - every other step marked "waits for" below.

**The step before, done.** Lukas said `ok` to its plan on 2026-10-15
(decision 16). It ran that day from 00:55 CEST until C39 merged in the
afternoon, one subagent per clone (spec 01 section 5):

- the TrustyAI operator: C29, then C14 (`flywheel-integration`
  `e4ddb1a`);
- eval-hub: C10, then C12 (`flywheel-integration` `7e94ad9`);
- both images on the cluster since 11:41 CEST, an hour with no restart
  (phase 2's DoD item 2);
- the harness, one item at a time: C35, C19, C38, C36, C37 and C39
  (`flywheel-integration` `ddfac7a`).

Each row is in section 5.1, each PR text in `docs/pr-drafts.md`.

**The next step** (Lukas's go, 2026-10-16; started 15:30 CEST with C20,
C28 and C27). Side by side, one subagent per clone, by section 6's
procedure; each new branch starts from the newest `upstream/main`, and
the harness's `flywheel-integration` first merges `upstream/main`
`b306e63` (the judge deny list, the move to fullsend-ai):

- the harness, one item at a time: C20 and C21 first, because C11
  reports the combined score and runs one split (section 4.4); then C26
  (the import's checks, section 4.3); then C22, C23, C24 and C25 (phase
  6's `pyfix` needs C23 to C25; C25 builds on C38's git snapshot in the
  pod). C24 maps OpenCode once C5 lands.
- eval-hub: C28, then a new EvalHub image on the cluster.
- odh-dashboard: C27.
- eval-hub-contrib: C11, when C20 and C21 are merged; its adapter image
  builds on the cluster (phase 2's DoD item 3).

All of it is merged, 2026-10-16 by 23:00 CEST: the harness's C20, C21,
C26, C22, C23, C24 and C25 (`flywheel-integration` `23f7690`, 3347
passed twice), eval-hub's C28, odh-dashboard's C27, and C11 with its
adapter image on the cluster. Each row is in section 5.1, each PR text
in `docs/pr-drafts.md`. The harness image on the cluster is older
(`flywheel-integration` `2137cdd`, the C21 merge; build
`agent-eval-harness-1`): a run that needs C22 to C25 in a pod needs the
base image and the adapter built again.

Not next:

- C13 is skipped while ODH's MLflow works (spec 01 phase 3, and phase 1
  picked ODH's MLflow).
- C5 waits for Lukas to post the opening comment on PR #90 (spec 01
  section 13, not posted; its last comment is astefanutti's, of
  2026-06-10), then for astefanutti's answer. The harness moved to
  `fullsend-ai/agent-eval-harness` on 2026-10-15; PR #90 is open there
  (`docs/research.md` section 4).
- Phase 4, Hugging Face import: after phase 3.

**Beside it, the fast path to our UI** (decision 17, 2026-10-16): phase 5
step 1, the new boards on the Design canvas for Lukas's review; phase 3
in this repo, the flywheel API with the registry, the bucket and support
as version 1; then phase 5's module in the odh-dashboard clone after
C27, built on the cluster. Phase 3's port of the loop reads
`openshift-eval`'s `generalization` once Lukas has committed it. Where
it stands (2026-10-16 18:35 CEST): our module runs in the dashboard on
the cluster, Develop & train › Agent flywheel with five placeholder
pages (phase 5's DoD item 1); the flywheel API runs on the cluster
behind the module's BFF, with the test use case `sample` (phase 3); the
boards are approved (decision 18), and the module's subagent builds
the Use cases, Use case and Task pages from them. At 22:56 CEST the
first evaluation with answers ran (decision 19): `smoke` version 2,
Codex on GLM 5.3 through EvalHub and our adapter, `reward` 0.667, each
task's reason in MLflow (phase 3 status). Next on this path: a run
route in the API, then "Start evaluation" on the Use case page.

**The cluster.** `cluster-nm8mw` auto-destroys on 2026-11-12. RHDP also
auto-stops it; the auto-stop read last was Thu 2026-10-15 02:23 CEST, and
only Lukas can move it (spec 01 section 0). It stopped after 2026-10-15
and ran again on 2026-10-16 (Lukas); the agent's token had expired and
was renewed at 15:15 CEST, until 2026-10-17 15:15 CEST. It stopped again
on 2026-10-16 about 21:15 CEST and ran again by 22:38 CEST. The new
auto-stop time is not read. A stop erases EvalHub's providers and jobs
(SQLite in the pod). Before cluster work that
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
16. **The answers to section 9, C19's design, the next step** (2026-10-15,
    Lukas, `ok` to every pick of the agent's first message):
    - question 1: the gaps of section 4.5 go to the projects named there,
      as C20 to C28;
    - question 2: the registry's API as section 9 proposes it;
    - question 3: the boards of phase 5 go on the Design canvas for his
      review before they are built;
    - question 4: C11 takes the shape of section 4.4;
    - question 5: the files of a use case as section 4.2 shows them;
    - question 6: this repo's layout for phase 3 as section 9 proposes it;
    - C19 by section 4.7, all seven points, with `specs/016-task-format/`
      and the cache beside `<tmp>/agent-eval/`, not in it;
    - the plan of section 0's next step, the cluster part included; he
      moves the cluster's auto-stop by at least a day.

    Section 4.3's layout, checks, tags and projections were not among
    the questions and stay proposals.
17. **The fast path to our UI** (2026-10-16, Lukas, `ok` to every pick of
    the agent's two messages that day; his goal: "as soon as possible,
    finally see our own UI in OpenShift ... and being able to start the
    flywheel"):
    - phases 3 and 5 start now, beside the contributions, not after
      phases 1 and 2 close (phase 1 holds C5, which waits for others):
      the boards on the Design canvas first, for his review; the flywheel
      API with the registry and support as version 1 in this repo; the
      module in the odh-dashboard clone after C27, built on the cluster;
      Evaluate and Train from the UI once C11 and the runner image land;
    - Lukas commits `openshift-eval`'s branch `generalization` himself
      (risk 2); the agent only reads it;
    - the agent creates the ObjectBucketClaim `flywheel-usecases` in
      `agent-flywheel`; the API pod reads its access key Secret as env,
      and the key is never printed and never enters a file;
    - Lukas moves the cluster's auto-stop to 2026-10-18 or later;
    - C27 is narrowed to what odh-dashboard's open draft #10012 leaves
      out (`pvc`, `git`, `hf`, `resolved_sha`, the collection entry's
      `test_data_ref`, a source picker), branched from `upstream/main`
      without #10012's code; its PR says it complements #10012.
18. **The UI's next steps** (2026-10-16 evening, Lukas, `ok` to every
    pick of the agent's report after our module first ran on the
    cluster):
    - the agent commits phase 3's code in this repo on `main`, in small
      commits, and never pushes, so the cluster builds the API from a
      commit;
    - the boards Use cases, Use case and Task on the Design canvas are
      approved: the module's pages are built from them;
    - the agent adds `AWS_DEFAULT_REGION` and `AWS_S3_ENDPOINT` to the
      claim's Secret `flywheel-usecases`, the two values EvalHub's init
      container needs beside the key; it never reads the key;
    - a task with no split stays in no split; the importer picks none
      for now;
    - Lukas deletes `services/flywheel-api/.venv` himself (the sandbox
      refuses its `*.pem`).
19. **The first evaluation, before support** (2026-10-16 evening, Lukas,
    `ok`): the first EvalHub job runs on a small smoke use case,
    `usecases/smoke/` (the API's test fixture with a `reward:` block and
    deterministic judges only), not on support, which waits for Lukas's
    commit of `openshift-eval`'s `generalization`. The agent is Codex on
    `enmaas-gpt-5-mini`, decision 9's agent model, about 0.04 USD for its
    three tasks; Lukas asked for "some cheap openai model" rather than
    GLM 5.3, which is free but slow. Changed the same night (Lukas, `ok`,
    22:50 CEST): EnMaaS stopped serving GPT (its `/v1/models` lists
    Claude and Gemini only, `docs/research.md`), so the agent is Codex on
    `enmaas-glm-5-3`, 0 USD, with a 900 s timeout per task; `smoke`
    version 2.

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

### 4.2 The files of a use case (decision 16, question 5)

```text
<use case>/
├── usecase.yaml   ours: title, description, the input key that is the prompt, the
│                  task label for the UI ("ticket"), the input keys the UI shows,
│                  the brain's limits, the adjuster's slots (role, causes, hidden note)
├── eval.yaml      the harness's: the judges, the gate, the workspace files
├── tasks/         one YAML file per task (decision 13); tasks/<id>/ for a task's files
├── tasks.jsonl    instead of tasks/: one task per line, a task's files in <id>/ beside it
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
  split one entry of the harness provider, each with a benchmark id of
  its own (EvalHub matches a collection's overrides by provider and
  benchmark id, so two entries with one id collide; `docs/research.md`
  section 5, C28), with `test_data_ref.s3` at the
  version's folder, `parameters.split`, and `pass_criteria` from the gate.
  The API writes it on every import and tags it `managed-by:
  agent-flywheel`; an edit in EvalHub's UI is lost at the next import. An
  MLflow evaluation dataset when one is needed, through the harness's
  `/eval-mlflow` `sync_dataset.py`.

### 4.4 One Score step, end to end (decision 16, question 4)

1. The controller creates EvalHub jobs on the use case's collection, one
   benchmark entry per split it scores (train, validation). Each carries
   `test_data_ref.s3` at the version, `parameters.split` and
   `parameters.brain`, a reference to the brain's MLflow artifact
   (`runs:/<run_id>/<path>`, C11). C11's provider has one benchmark,
   `eval-run`, and EvalHub matches a job's entries to a collection's by
   provider and benchmark id, so two entries `eval-run` in one job take
   the first one's overrides (`docs/research.md` section 5, read, not
   tested): until that is settled in phase 3, one job per split.
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
| Combined score and gate in `summary.yaml` | harness | C20 | decided (decision 16) |
| Splits | harness | C21 | decided (decision 16) |
| Deterministic judges (contains, forbidden, cites, sections, regex, exact, numeric, JSON Schema, diff limits) | harness built-ins | C22 | decided (decision 16) |
| Hidden tests after the agent | harness | C23 | decided (decision 16) |
| One permission profile for every runner (edit, shell, web) | harness | C24 | decided (decision 16) |
| The diff as output of a sealed workspace | harness | C25 | decided (decision 16) |
| JSON Schema of a task, warning on unknown keys | harness | C26 | decided (decision 16) |
| The adapter takes any use case version | eval-hub-contrib | C11, changed | decided (decision 16) |
| The full `TestDataRef` in the dashboard's EvalHub module | odh-dashboard | C27 | decided (decision 16) |
| `test_data_ref` and `resolved_sha` on the EvalCard | eval-hub | C28 | decided (decision 16) |
| Registry, import, versions, the collection and the MLflow dataset | this repo, the flywheel API | — | decided (decision 11): it joins S3, EvalHub and MLflow |
| The adjuster's slots, the brain's limits, the UI's words | this repo, `usecase.yaml` | — | decided (decision 16): our loop and our UI only |
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

### 4.7 C19's design (decision 16)

What the harness does today (`docs/research.md` section 4, "Where the
dataset is read"): thirteen files read `dataset.path` as a folder of case
folders, each in its own process, with no shared loader; `workspace.py`
deletes the run's temp folder when it starts; a case's other files reach
the agent only through `dataset.workspace.files`; the first design
principle is "scripts just move files", with no hardcoded field names.
The design, point by point, as Lukas took it on 2026-10-15:

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
   by the content hash, under `<tmp>/agent-eval-datasets/<hash>/`, beside
   the runs' folder `<tmp>/agent-eval/`, not in it: `workspace.py` deletes
   `<tmp>/agent-eval/<run-id>`, and `datasets` is a valid run id
   (`workspace.py:78, 89-95`). So its cleanup never touches the cache, and
   every process finds the same one.
5. **On EvalHub.** Both downloads end at the same helper: EvalHub's init
   container copies the version to `/test_data` (C11's path, section 4.4),
   and the harness's own `s3_dataset.py` downloads a prefix (its EvalHub
   adapter's path); `s3_dataset.py` also accepts task files at the
   prefix's top level instead of reading them as cases.
6. **Upstream's way.** A feature, so the branch carries a spec folder,
   `specs/016-task-format/` (spec, plan, tasks), as upstream's spec-driven
   work does. 015 is taken: astefanutti's open PR #251 adds
   `specs/015-judge-verdict-transport/` (2026-10-15); phase 7's rebase
   checks the number again. The docs go into `website/`, not `CLAUDE.md`: `AGENTS.md` is
   about 100 tokens under skillsaw's budget (`docs/pr-drafts.md`).
7. **Tests.** The same tasks in each format and written by hand as case
   folders give the same case folders, through `workspace.py`, `score.py`
   and both downloads; an existing case-folder dataset gives byte-equal
   results.
## 5. Contribution catalogue

C1 to C18 and C30 to C34 are in spec 01 section 7. Done there: C1 to C4, C6 to C9 and C30 to C34.
Still open from there, unchanged unless this section says so: C5, C10,
C12 to C18. The rows below are new or changed; the notes after the table
update spec 01's open rows, and section 5.1 holds the status of all of
them.
C35 to C39 are the second round of spec 01's C30 to C34: the gaps their
subagents found, fixed on the branch that already owns each area, as new
commits on top, so no new PR and no new dependency between PRs. Each gap
with file and line: `docs/research.md` section 4, "Found while C30 to C34
were built".
C19, C29 and C35 to C39 are decided (C29: Lukas, `ok`, 2026-10-14; C35 to
C39: Lukas, 2026-10-14, the round moved here from spec 01); C11's new shape
and C20 to C28 since 2026-10-15 (decision 16).

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
| C35 | harness, on C30's `fix/mlflow-traces` | MLflow 3.5.0 rejects the span status `STATUS_CODE_OK`; unlinked traces of an earlier run are reused; at most 500 traces read; a multi-step case's cost lands on its last step; a warning on every run from the snapshot search; a tool's output lost when its result has no timestamp; an ERROR from the flush on 3.5.0; judge feedback on the wrong trace (`find_run_traces` ignores its run id, `attach_feedback.py` attaches to every trace, the `main_trace_id` fallback, reused Harbor traces not registered) | Each fixed with a test that fails first, on MLflow 3.5.0 and 3.17.x | Wrong or missing MLflow records under the dashboard |
| C36 | harness, on C32's `fix/cost-figures` (each commit to PR A or B) | Multi-step and estimate costs rounded to 4 decimals, an unknown step cost counted as 0; `cost_usd_estimate` lost without a plan; a codex litellm estimate without `harness:estimate` (spec 014); a judge model `fable` sent to the OpenAI SDK; the cli contract silent on uncached `input`, `cache_read`, `cache_create` and `{config_dir}`; OpenCode's reasoning tokens (check first) | Exact, labelled figures, kept in `run_result.json` | Our own cost code |
| C37 | harness, on C34's `fix/anova-cells` and C8's `feat/anova-cell-reuse` | `{name}` unresolved for `input.yml` and `input.json` cases; `/eval-anova` skips them; run ids collide across factors; two evals overwrite each other's workspace; an override dropped in silence; a wrong log message and guide row; **a cell that misses a threshold counts as failed** (`score.py:4188-4189`, `orchestrate.py:155-160`, on `9bc9a8d`); C8's reuse checks the version, not the code | A grid whose every cell runs what it says and counts its result | — |
| C38 | harness, on C31's `fix/evalhub-pod` | The pod's judges see no annotations with S3 or ConfigMap delivery; the pod's defaults are 600 s and 5 USD (documented: 3600 s, 100 USD) and a 0 is dropped; pod cases are not git repositories, so no `_modified`; the Harbor verifier writes no `run_result.json`; `pass_rate` sent in metadata the SDK drops (C7 already delivers it); the pod's agent runs beside its answer key (`annotations.yaml`, with C19 `task.yaml`; found 2026-10-15, `docs/research.md` section 4) | A pod that scores as a local run does, and whose agent sees what a local run's sees | — (feeds C11) |
| C39 | harness, on C33's `fix/stop-handlers` and C9's `feat/optimize-no-verify` | A stopped run leaves hooks running; synthetic generation and the Harbor verifier install no stop handler; the optimize skill's judge types leave out `agent` | C1's stop handling for all of them | — |
| C29 | trustyai-service-operator | The TrustyAIService controller watches KServe's `InferenceService` with no check (`controllers/tas/trustyaiservice_controller.go:317`); with KServe `Removed` the manager, and the EvalHub controller in it, restarts every few minutes (`docs/research.md` section 5) | Watch `InferenceService` only when its API is served, as the EvalHub controller does for Kueue (`kueue_workloads_discovery.go:26`); reuse `isInferenceServiceCRDPresent` (`controllers/tas/inference_services.go:32`), which upstream PR #899 added without gating the watch. ✅ when the tests are green with and without KServe's CRD and it is merged; the hour on `cluster-nm8mw` with no new restart is phase 2's DoD | KServe `Managed` only to keep the operator up |

Notes on C35 to C39, from the round's work on 2026-10-14:

- C35: on `fix/mlflow-traces`, `2a48c71` holds 7 commits on top of
  `f63969a` (gaps: span status, a tool's output without a timestamp and
  its docs, the run's own traces and paging, the per-step model and one
  trace per step, the snapshot search). Its suite, `mkdocs`, `skillsaw` and
  the merge are not run yet. Open: the flush's ERROR on 3.5.0 (planned: a
  narrow logging filter on `mlflow.tracking.fluent`, not a check of the
  private `_async_queue`) and the four feedback gaps.
- C35's merge with C6 needs hand work: in `trace_builder.py`'s
  tool-result loop take C6's version, drop `keep_untimed` and its
  condition, and rewrite C6's comment (drop `STREAM_JSON` from the import
  if it is then unused); in log_results' case-mode loop add C6's
  `agent=runner_type` back to the `build_trace` call, which now passes
  `trace_key`. No marker shows two more: in both golden
  `expected-trace.json` files `STATUS_CODE_OK` becomes `OK`, and in the
  Harbor golden trace the Bash span gets the output
  `{"result": "Hello, World!"}`.
- C35 checks MLflow 3.5.0 in a venv of its own:
  `uv pip install -e ".[mlflow]" "mlflow[genai]==3.5.0" "sqlalchemy<2.1"`.
- C36 meets C2 in `codex.py`'s `_cost` and in five doc pages; C38 meets C7
  in `adapter.py` and `runner.py`; C37 meets C8 in the guide row
  `website/guides/eval-anova.md:166`. `docs/pr-drafts.md`'s order notes
  say how spec 01 resolved each, and the result must keep both rules.
- C38's git snapshot in the pod overlaps C25's pod part: build it once,
  in whichever comes first.
- C39 stays stacked on C1 (`fix/stop-on-sigterm`).
- Left out, on purpose: lm-eval on EnMaaS `/completions` (Lukas: leave
  it); the cost of Harbor's own Codex agent (Harbor's repo, no fork);
  `process_group.stop_all()` in C7's pool (it needs C1 and C7 together; the
  second of them to land adds it); the pod's PID 1 on a cluster (needs C11's
  image there); the rule `.skillsaw.yaml` names that skillsaw 0.21.0
  removed (CI pins 0.10.0).

Notes on spec 01's open rows, read 2026-10-14 evening in the clones'
`upstream/main`: eval-hub `540676f` (upstream's `main` was `3f7b173` by
then, not fetched), operator `4fa5c74`. Fetched 2026-10-15 00:50 CEST:
eval-hub `3f7b173`, operator `258b3a9`, eval-hub-contrib `0b4b4ea`, the
harness still `9bc9a8d`. The new commits leave the files of C10, C12, C14
and C29 alone (eval-hub: collections, config, docs; operator: the
EvalHub NetworkPolicy, NeMo, dependencies). `git fetch upstream` first, and
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
  Upstream ignores the exit because an adapter often posts its own result
  before it exits non-zero. A blind `failed` is not safe: the server keeps
  the first terminal state of a job, not of a benchmark, and while other
  benchmarks run a later terminal event replaces one benchmark's status
  and results (`docs/research.md` section 5). So C14 reads the job first
  and posts `failed` only while the benchmark is open; a 409
  `job_can_not_be_updated` ends the sync. (Fixed 2026-10-15: this note
  said "with no new GET".)

### 5.1 Status

The one place a contribution's state is written. ⬜ not started, ▶️ in
progress, ✅ merged into its repo's `flywheel-integration`, its PR not
opened yet (phase 7); skipped, with the reason. "Head" is the branch's
head commit and, after the merge, `flywheel-integration`'s.
Spec 01's ✅ rows (C1 to C4, C6 to C9, C30 to C34) stay in spec 01
section 7.

| Id | Repo | Branch | Head | State | Waits for |
|:--|:--|:--|:--|:--|:--|
| C29 | trustyai-service-operator | `fix/tas-watch-without-kserve` | `c724383`; `flywheel-integration` `e4ddb1a` | ✅ 2026-10-15: 249 Go tests, 255 Ginkgo specs (agent's run); on the cluster since 01:22 CEST, with `deploy/builds/trustyai-operator-rbac.yaml` | — |
| C35 | agent-eval-harness | `fix/mlflow-traces` | `a05e61e`; `flywheel-integration` `0084662` | ✅ 2026-10-15: 2617 passed twice (agent's run), 2335 on the branch; skillsaw, mkdocs clean; MLflow 3.5.0: 214 passed on the branch, C6's one test fails on the merge (`docs/pr-drafts.md`) | — |
| C19 | agent-eval-harness | `feat/task-format` | `f1cea07`; `flywheel-integration` `89cb326` | ✅ 2026-10-15: 2664 passed twice (agent's run), 2342 on the branch; skillsaw, mkdocs clean; `specs/016-task-format/`, the cache at `<tmp>/agent-eval-datasets/<hash>/` (section 4.7) | — |
| C38 | agent-eval-harness | `fix/evalhub-pod` | `a44eb8b` (6 commits on C31's `04d184e`); `flywheel-integration` `392baca` | ✅ 2026-10-15: 2704 passed twice (agent's run), 2341 on the branch; skillsaw, mkdocs clean; the pod's agent no longer sees its answer key; `pass_rate` left to C7, which delivers it | — |
| C36 | agent-eval-harness | `fix/cost-figures` | `a605864` (7 commits on C32's `4e21613`, to PR A or B); `flywheel-integration` `986153c` | ✅ 2026-10-15: 2736 passed twice (agent's run), 2342 on the branch; skillsaw, mkdocs clean; OpenCode's reasoning tokens counted as output | — |
| C37 | agent-eval-harness | `fix/anova-cells`, `feat/anova-cell-reuse` | `a4545ce` (7 commits on C34's `7931dca`), `5550792` (1 on C8's `5b5a3de`); `flywheel-integration` `3bb423c` | ✅ 2026-10-15: 2803 passed twice (agent's run of the merge `b62f9da`; `3bb423c` adds one line of docs), 2369 and 2366 on the branches; skillsaw, mkdocs clean; a cell that misses a threshold counts; reuse keyed on the code a cell runs | — |
| C39 | agent-eval-harness | `fix/stop-handlers`, `feat/optimize-no-verify` | `ce6eca8` (3 commits on C33's `7e59702`), `5641025` (1 on C9's `97817e7`); `flywheel-integration` `ddfac7a` | ✅ 2026-10-15: 2817 passed twice (agent's run), 2326 and 2315 on the branches; the 37 stop tests 3 of 3 runs on the branch, 38 on the merge; skillsaw, mkdocs clean; a stopped run stops its running hooks, the generator and the Harbor verifier | — |
| C10 | eval-hub | `fix/k8s-runtime-json-tags` | `86d4fcf`; `flywheel-integration` `4856472` | ✅ 2026-10-15: 1478 Go tests in the sandbox (baseline 1472), the same 23 `/tmp`-bound failures on both | — |
| C12 | eval-hub | `fix/local-runtime-exit` | `b60213e`; `flywheel-integration` `7e94ad9` | ✅ 2026-10-15: 1480 Go tests in the sandbox (agent's run; 1469 on `main`), the same 23 `/tmp`-bound failures; reads the job before it posts; on the cluster since 11:41 CEST | — |
| C14 | trustyai-service-operator | `fix/evalhub-adapter-exit` | `24e6886`; `flywheel-integration` `e4ddb1a` | ✅ 2026-10-15: 256 Go tests, 255 Ginkgo specs (agent's run); reads the job before it posts (section 5 note); on the cluster since 03:38 CEST | — |
| C13 | eval-hub | — | — | skipped | ODH's MLflow refusing the header |
| C5 | agent-eval-harness | — | — | ⬜ | Lukas's comment on PR #90, then astefanutti |
| C11 | eval-hub-contrib | `feat/agent-eval-harness-adapter` | `ef0fb5c` (4 commits on `78f01e4`); `flywheel-integration` `98d7683` (new, from `upstream/main` `78f01e4`) | ✅ 2026-10-16: 29 tests twice, the offline smoke test, ruff clean (agent's run of the merge, on the harness's `flywheel-integration` `2137cdd`); `make test-atif` 132 as on `main` (subagent's run); one benchmark `eval-run` for any use case version at `/test_data`, `parameters.split` and `parameters.brain` (`runs:/<run_id>/<path>`), `reward.mean` as the primary score, each judge's mean and pass rate as metrics, the run folder to MLflow; its image built on the cluster, smoke test passed (build `agent-eval-harness-adapter-2`) | — |
| C20 | agent-eval-harness | `feat/summary-reward-verdicts` | `f2ca79e` (9 commits on `b306e63`); `flywheel-integration` `2293963` (after `1bf99ae` merged `upstream/main` `b306e63`) | ✅ 2026-10-16: 2903 passed twice (agent's run; `1bf99ae` 2857 twice, subagent's run), 2381 on the branch; skillsaw, mkdocs clean; the reward per case and its mean, every threshold verdict, `thresholds.reward`, `--no-fail-on-regression` | — |
| C21 | agent-eval-harness | `feat/named-splits` | `39a2bcd` (12 commits on C19's `f1cea07`); `flywheel-integration` `2137cdd` | ✅ 2026-10-16: 2953 passed twice (agent's run), 2386 on the branch; skillsaw, mkdocs clean; `--split <name>`, `split` and `splits` in `summary.yaml`, the EvalHub adapter's `parameters.split`, the MLflow tag | — |
| C26 | agent-eval-harness | `feat/task-json-schema` | `5f3fbb0` (11 commits on C19's `f1cea07`); `flywheel-integration` `2c2173d` (after `2137cdd`) | ✅ 2026-10-16: 3089 passed twice, `mkdocs build --strict` exit 0, skillsaw 0 warnings (agent's run of the merge); 2464 on the branch (subagent's run); `dataset.json_schema` for a task's `input` and `expected`, checked by `validate_eval.py` and before any agent starts, every problem with its file, line and JSON path; `agent_eval.task_schema` (`check`, `validate`, `load_schemas`, `check_task`) for our registry; an `UnknownKeyWarning` on a key of `eval.yaml` no reader reads; `jsonschema>=4.18` a new extra | — |
| C22 | agent-eval-harness | `feat/builtin-text-judges` | `6c388f7` (7 commits on `upstream/main` `b306e63`); `flywheel-integration` `39153c8` (merges `640b9a3` and `39153c8` after `2c2173d`) | ✅ 2026-10-16: 3203 passed twice, `mkdocs build --strict` exit 0, skillsaw 0 warnings (agent's run of the merge); 2446 on the branch, 2336 on the base (subagent's runs); nine deterministic text builtins (`contains`, `forbidden`, `cites`, `sections`, `length`, `regex`, `exact`, `numeric`, `json_schema`) and `diff` on the agent's workspace change (`_diffstat.json`), each with arguments and `<name>_from` for a per-task value, a value and a one-sentence rationale per verdict | — |
| C23 | agent-eval-harness | `feat/hidden-tests-after-agent` | `92df98e` (8 commits on C22's `6c388f7`); `flywheel-integration` `0671a25` (merges `03f3b58` and `0671a25` after `39153c8`) | ✅ 2026-10-16: 3263 passed twice, `mkdocs build --strict` exit 0, skillsaw 0 warnings (agent's run of the merge); 2503 on the branch, 2446 on its base (subagent's runs); `execution.verify {command, files, timeout, output_limit}` runs after each case's agent on a copy of its workspace, hidden files staged only then, in its own process group with a timeout and a bounded output tail, locally and in the EvalHub pod; the `verify` builtin gives exit 0 a pass and quotes the last output line. An `after_each` hook with a `check:` judge did not cover it: its files counted as the agent's change, and the pod runs no hooks | — |
| C24 | agent-eval-harness | `feat/runner-permissions` | `82e1620` (3 commits on `upstream/main` `1a980e7`); `flywheel-integration` `1fcae5a` (merge after `0671a25`; it also brings upstream's fullsend files) | ✅ 2026-10-16: 3337 passed twice, `mkdocs build --strict` exit 0, skillsaw 0 warnings (agent's run of the merge); 2408 on the branch, 2336 on the base (subagent's runs); `runner.permissions: {edit, bash, web}`, each true, false or left out ("not set", today's behaviour), mapped by claude-code (disallowed and allowed tools, `acceptEdits`), codex (sandbox mode, `features.shell_tool`, `web_search`, the sandbox's network access) and cursor (deny rules, the allowlist); a key a runner cannot enforce warns at load, naming the runner; a contradiction with the runner's own settings is refused. OpenCode waits for C5. The Codex keys come from codex-cli 0.154.0's `--help`; our images have 0.147.0 | — |
| C25 | agent-eval-harness | `feat/sealed-workspace-diff` | `06e5815` (4 commits on C38's `fix/evalhub-pod` `a44eb8b`); `flywheel-integration` `23f7690` (merge after `1fcae5a`) | ✅ 2026-10-16: 3347 passed twice, `mkdocs build --strict` exit 0, skillsaw 0 warnings (agent's run of the merge); 2349 on the branch, 2341 on its base (subagent's runs); on `flywheel-integration` a sealed workspace and the pod already gave the local diff, but all three paths counted more than the agent's change: the harness's own `output/stdout.log` when no output is declared, files a `before_each` or `after_each` hook writes, and nothing at all for an agent that commits. Now the snapshot is the ref `refs/agent-eval/snapshot`, taken again after `before_each`, and `execute.py` records `_modified/` when the agent is done, where the pod already did. Stacked on C38, which creates `workspace_changes.py`; its PR opens after C38's. Not changed: the pod runs no lifecycle hooks, and files the agent's tools create (`__pycache__/`) count unless the case ships a `.gitignore`, so `pyfix` needs one | — |
| C27 | odh-dashboard | `feat/eval-hub-test-data-sources` | `2676e771e` (2 commits on `b4e406cb5`); `flywheel-integration` `7983bd799` (new, from `upstream/main` `b4e406cb5`) | ✅ 2026-10-16, narrowed to what upstream's open draft #10012 leaves out (decision 17): `packages/eval-hub` frontend 1475 tests in 88 suites, lint and type check clean, the BFF's Go tests green (agent's run of the merge; 1435 on `b4e406cb5`, subagent's run); git, PVC and Hugging Face sources, `resolved_sha` shown, a collection entry's `test_data_ref` kept, a source picker | — |
| C28 | eval-hub | `feat/evalcard-test-data-ref` | `69fe00d`; `flywheel-integration` `4315523` | ✅ 2026-10-16: 1503 Go tests twice in the sandbox (agent's run; 1484 on `upstream/main` `eec7581`), the same 23 `/tmp`-bound failures; each result on the card names its test data and `resolved_sha`, never a `secret_ref`; on the cluster since 15:52 CEST (build `eval-hub-2`) | — |
| C15 to C18 | odh-dashboard | — | — | ⬜ | phase 5; C16 to C18 as spec 01 phase 5 step 2 places them |

## 6. Phases

Each phase ends with its Definition of Done, checked and written into its
status. Phases 1 and 2 run side by side: they work in different repos, and
section 0's next step takes items of both. From phase 3 on, a phase starts
when the phases before it have their DoD checked, except that phases 3
and 5 run beside phases 1 and 2 (decision 17). The phases continue
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

| Repo | Tests and checks | Known |
|:--|:--|:--|
| agent-eval-harness | `make test` in the clone's `.venv` (Python 3.12, `uv pip install -e ".[all,test]"`); CI's skillsaw 0.10.0 `--strict`; `mkdocs build --strict` in a venv with `-e . -r website/requirements.txt`, as CI's `docs.yml` installs it (a venv in `$TMPDIR` is gone after a reboot) | `upstream/main` `9bc9a8d`: 2296 passed. In the sandbox `make test` needs `MPLCONFIGDIR=$TMPDIR/mplconfig` holding a copy of `~/.matplotlib/fontlist-v3.11.0.json`, else 5 collection errors (2026-10-15) |
| eval-hub | `make clean test-all`, `pre-commit run --all-files` | **Never outside the sandbox:** the Postgres tests run `tests/postgres/Makefile`, which on a Mac runs `brew install postgresql@18`, `initdb` and `brew services` (it did, 2026-10-15). In the sandbox: `HOMEBREW_NO_AUTO_UPDATE=1`, `-skip Postgres`, `CLEAN_OPTS="-r -testcache"` (plain `make clean` wipes the shared Go build cache), `GOPATH` under `$TMPDIR` (the sandbox refuses `~/go/pkg/sumdb`); 23 tests need the hardcoded `/tmp/evalhub-jobs` and `/tmp/db_password` and fail there, and 8 of the 195 FVT scenarios for the same jobs folder. **Block the cluster for the FVTs:** their GPU steps (`tests/features/gpu_step_definitions_test.go:208-340`) run `oc` with the session's `KUBECONFIG`, and can `oc apply`, `oc label node` and `oc delete` Kueue objects; on 2026-10-15 four `oc get crd clusterqueues.kueue.x-k8s.io` went out: the agent's two runs of C10 (02:20, 02:30) got NotFound, Kueue is not installed, and the steps skipped; the C12 subagent's two failed (a timeout, a 401). Nothing changed. Put `oc` and `kubectl` shims that exit 1 on `PATH` and set `KUBECONFIG=/dev/null`. `GOTOOLCHAIN=auto` fetches Go 1.26.7; pre-commit in a venv, with `GIT_HTTP_PROXY_AUTHMETHOD=basic` |
| trustyai-service-operator | `make test` (`manifests generate fmt vet envtest`), `go mod tidy` | `upstream/main` `258b3a9`: 247 Go tests and 255 Ginkgo specs pass, 1 Go test needs `python` on `PATH`. In the sandbox: `GOPATH`, `GOCACHE` and `HOME` under `$TMPDIR` (envtest writes port locks under `$HOME/Library/Caches`), a `mktemp` shim (macOS `mktemp` ignores `TMPDIR` without a template), a `python` link; `/tmp/claude-501/c14/env.sh` has them. `make test` rewrites 5 Go files and 2 `manager-rbac.yaml`: never commit that. Trust `go.mod` (Go 1.26.0, controller-runtime 0.22.5) over `CLAUDE.md:5` |
| eval-hub-contrib | `make test-<name>`, the adapter's offline `smoke_test.py` | Never run here |

A missing tool goes into the clone's own environment (its `.venv`, Go's
toolchain download), not onto the machine. If the sandbox refuses a
download, tell Lukas the host: `.claude/settings.json` holds the network
allowlist, and only he changes it.

### Phase 1: harness contributions

In the `agent-eval-harness` fork, by the procedure above, one item at a
time in its clone. C35 first, since it is half done; then C19, with the
design of section 4.7; then C38, C36, C37 and C39, each as new commits on
the branch named in its row; C5 when its wait ends (section 5.1); C20 to
C26 after them (decision 16).

DoD:

- [ ] every branch green on `make test`
- [ ] `flywheel-integration` merges them all and stays green, run twice

Status: started 2026-10-15 00:55 CEST with C35. C35, C19, C38, C36, C37
and C39 are merged (section 5.1): each branch green on `make test` (its
subagent's run), and `flywheel-integration` `ddfac7a` 2817 passed twice
(the agent's run). On 2026-10-16 `flywheel-integration` merged
`upstream/main` `b306e63` (`1bf99ae`), then C20 (`2293963`, 2903 passed
twice, the agent's run), C21 (`2137cdd`, 2953 passed twice, the
agent's run), C26 (`2c2173d`, 3089 passed twice, the agent's run) and
C22 (`39153c8`, 3203 passed twice, the agent's run), C23 (`0671a25`,
3263 passed twice, the agent's run), C24 (`1fcae5a`, 3337 passed twice,
the agent's run) and C25 (`23f7690`, 3347 passed twice, the agent's
run). The DoD stays open for C5 only.
`flywheel-integration`'s `CLAUDE.md` is about 5,995 of skillsaw's 6,000
tokens, so the next contribution that adds a line there must cut one.

### Phase 2: EvalHub, contrib, operator

Spec 01 phase 3, with C11 in its new shape and the notes of section 5:
C29 first, since the operator it fixes reconciles the `EvalHub` this phase
changes; then C14 in the same clone, and C10 and C12 in eval-hub; C13 is
skipped; C11 after the harness's C19 and C38; C27 and C28 (decision 16).

On the cluster:

1. Build our images on the cluster, from each clone's
   `flywheel-integration`, with binary BuildConfigs
   (`oc start-build --from-repo=<clone> --commit=<sha>`; it drops
   `--build-arg` for a binary build), so nothing is pushed. The BuildConfigs
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

- [x] each repo's tests green, with the baseline and the final counts here
      (2026-10-16, the agent's runs of each `flywheel-integration`; the
      baselines are each `upstream/main` the branches start from): the
      TrustyAI operator `e4ddb1a` 256 Go tests and 255 Ginkgo specs (247
      and 255 on `258b3a9`); eval-hub `4315523` 1503 Go tests in the
      sandbox (1484 on `eec7581`), the same 23 `/tmp`-bound failures on
      both; eval-hub-contrib `98d7683` the adapter's 29 tests and its
      smoke test (new; `make test-atif` 132 as on `78f01e4`, the
      subagent's run); odh-dashboard `7983bd799` `packages/eval-hub` 1475
      frontend tests and the BFF's Go tests (1435 on `b4e406cb5`)
- [x] on the cluster, ODH runs our operator image (C29, C14) and our
      EvalHub server image (C10, C12); the operator has no new restart for
      an hour, and EvalHub answers `/api/v1/health` (checked 2026-10-15
      12:43 CEST)
- [x] the adapter image (C11) builds on the cluster and passes its offline
      smoke test (2026-10-16: build `agent-eval-harness-adapter-2` of
      contrib `98d7683`, on our harness base `agent-eval-harness-1` of
      harness `2137cdd`; the smoke test runs inside the build and passed)

The end-to-end check, an EvalHub job with our adapter on a use case
version read from S3, needs the bucket and the registry: it is phase 3's
DoD.

Status: started 2026-10-15 00:55 CEST with C29 and C10. C29, C14, C10
and C12 are merged (section 5.1). On the cluster (`deploy/builds/`,
`deploy/platform/operator/`):

- The Subscription's env reached the ODH operator, the TrustyAI module and
  the operator deployment within 2 minutes (section 8's first check).
- Our operator image of upstream `main` exited after 2 minutes under
  ODH 3.6.0-ea.2's roles, which lack NetworkPolicies and Events
  (`docs/research.md` section 5); `deploy/builds/trustyai-operator-rbac.yaml`
  adds them, and all six controllers start.
- The image of `2a28e81` (C29) then ran 1 h 52 min with 0 restarts
  (01:26 to 03:38 CEST). The image of `e4ddb1a` (C29, C14) ran from
  03:38 CEST with 0 restarts, 5 h 48 min by 09:27 CEST: the DoD's hour
  holds for the operator. The agent's token expired meanwhile and was
  renewed with `scripts/agent-kubeconfig.sh` (until 2026-10-16 09:27 CEST).
- The EvalHub image of `7e94ad9` (C10, C12; build `eval-hub-1`) was
  applied at 11:39 CEST and reached the server and its job pods' init and
  sidecar images by 11:41 (`evalhub-config`). Through the Route,
  `/api/v1/health` answers `healthy`, and the provider API returns C10's
  documented names (`cpu_request`, `env[].name`). The env change also
  rolled the operator pod at 11:40, with the same image, so the operator's
  hour ran again from there. At 12:43 CEST the operator pod had run 63
  minutes and the EvalHub pod 62, both with 0 restarts, and
  `/api/v1/health` answered `healthy` at every check (every 10 minutes
  from 11:43): the DoD's second item holds. EvalHub's database is in memory
  (`deploy/platform/evalhub/`): each new image forgets its jobs.
- 2026-10-16: the EvalHub image of `4315523` (C10, C12, C28, and
  upstream up to `eec7581`; build `eval-hub-2`) was applied at 15:50 CEST.
  By 15:52 the server and its job pods' init and sidecar images had it,
  `/api/v1/health` answered `healthy`, `default-dsc` was Ready, and the
  operator pods rolled with our same operator image.
- 2026-10-16: our harness base image (build `agent-eval-harness-1` of
  harness `2137cdd`, the harness's `deploy/Containerfile`, 1 min 28 s)
  and the adapter image on it (build `agent-eval-harness-adapter-2` of
  contrib `98d7683`, 54 s, digest `3dd2ecff…`); the adapter's smoke test
  passed inside the build. The DoD is checked: phase 2 is done. The
  adapter image runs on the cluster once phase 3 registers its provider.

### Phase 3: the registry and the glue

Spec 01 phase 4, on the registry of decision 11. The layout of this repo is
agreed (decision 16, question 6). The port reads `openshift-eval`'s
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
- [x] a changed import makes version 2, and version 1 stays readable
      (on `smoke`, decision 19, 2026-10-16; support checks it again)
- [x] on the cluster, an EvalHub job with our adapter runs the harness on
      version 1, read from S3, and logs a reason per task to MLflow (on
      `smoke` version 2, decision 19, 2026-10-16 22:55 CEST)
- [ ] a free smoke loop on the cluster through EvalHub on version 1; its
      MLflow records have the shape spec 01 phase 4 asked for, plus the
      version tags

Status: started 2026-10-16 (decision 17). Step 1: the bucket claim
`flywheel-usecases` (`deploy/bucket/`) is Bound on NooBaa, bucket
`flywheel-usecases-e385d4d5-cf1c-46b4-bd69-c36e67d5c84a`; inside the
cluster its S3 answers on `http://s3.openshift-storage.svc:80` (the
ConfigMap names port 443, which serves the service CA's certificate).
Step 2's first slice, the registry and its API, is built in
`services/flywheel-api/` (2026-10-16): the four routes of decision 16
question 2 (Hugging Face answers 501 until phase 4), import by upload
(`.tar.gz` or `.zip`) or from git (https only, the commit recorded), every
problem refused at once with its file, field and line (422), a version
only when the content hash changes, nothing overwritten. 127 tests pass
twice (the agent's run, offline: S3 through `moto`). It runs on the
cluster since 2026-10-16 18:30 CEST (decision 18): commits `4befbc5` and
`637c9af` on this repo's `main`, not pushed; build `flywheel-api-1` of
`637c9af`; `c62e9bb` turns off the pod's service links, since the
Service `flywheel-api` injected `FLYWHEEL_API_PORT=tcp://…` and the pod
crashed. Through the dashboard (host, our module's BFF, the API, with
the agent's token): the list answered `[]`; the API's test fixture,
imported as `sample` ("Product questions", 3 tasks), answered 201
created (version 1), the same upload 200 unchanged, a broken copy 422
refused with its problem; NooBaa took boto3's writes. `sample` stays
as test data. The claim's Secret has `AWS_DEFAULT_REGION` and
`AWS_S3_ENDPOINT` (decision 18, `deploy/bucket/`), and NooBaa keeps
them. Two
choices made on the way: a JSONL dataset's task files sit in `<id>/`
beside `tasks.jsonl`, as C19 reads them, and a JSONL id may not be
`tasks`, `resources` or `hidden`; the diff also names the files that
changed outside the tasks, so a judge-only change shows. Open: decision
13's "else the import picks one, balanced by tags" is not built (stored
files stay as imported, so the hash matches the source); a task without
a split counts in no split. `version.json` sits in the version's folder,
so EvalHub copies it into `/test_data` too. Step 5 waits for Lukas's
commit of `openshift-eval`'s `generalization`.

The first evaluation (decision 19, 2026-10-16 19:35 to 19:47 CEST):
`usecases/smoke/` imported as `smoke` version 1 (hash `3c1a68745e78`, 3
tasks); C11's provider registered in EvalHub through its API (id
`3e9b9bf2-f31d-4b8d-ab03-a988bc0ecaa2`, our adapter image by digest);
`deploy/builds/evalhub-jobs-rbac.yaml` gives `evalhub-service` the
NetworkPolicy rights our EvalHub build needs (two jobs failed on it,
before any pod). Jobs `9c810364…` and `62f4fd86…` then ran the whole
path: the init container read the version from S3, the adapter ran the
harness, EvalHub got `reward` 0.0 with `test.pass` false, and MLflow
(experiment `agent-flywheel-smoke`, runs `22ef40a8…` and `01601f29…`)
holds the run folder with each task's Codex log. Codex itself got no
answer: about half of EnMaaS's backends answered 404 for every OpenAI
model from 17:38 UTC, a kept connection stays on its backend, and
LiteLLM's cooldown turned the first 404 into 429s (`docs/research.md`,
"EnMaaS's OpenAI models fail in bursts"). Cost 0 USD: no call reached a
model.

The first evaluation with answers (decision 19 as changed, 2026-10-16
22:55 to 22:56 CEST): `smoke` version 2 (hash `03205b0803b8`, its diff
only `eval.yaml`; version 1 still answers) with Codex 0.147.0 on
`enmaas-glm-5-3`. EvalHub had lost the provider in the cluster's restart
(SQLite in the pod, `docs/research.md`), so it is registered again as
`b63ce249-faa2-4663-89b4-3f20078b0e0f`. Job `6bbcc140…` completed in 70
s: all 3 tasks answered, every gateway call 200; `reward` 0.667 against
the 0.5 threshold, `test.pass` true. MLflow run `dd5a8caa…` holds each
task's answer and reason: `pricing` and `reset-password` "mentions every
expected fact"; `export-data` "missing: CSV" (it named the 10,000-row
limit and the fix, not the format), so validation scores 0.0 and train
1.0. Tokens: 24,680 input, 90,112 cache read, 1,880 output, 3 turns;
cost 0 USD, GLM 5.3 is free. DoD items 2 and 3 are checked on `smoke`;
items 1 and 4 wait for support.

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

- [x] on the cluster, the dashboard shows Develop & train › Agent flywheel
      and its pages (2026-10-16 18:11 CEST, placeholders: Use cases,
      Evaluations, Benchmarks, Training, Brains; checked with Playwright
      as `claude-agent`)
- [ ] Lukas imports a use case from the dashboard, starts an evaluation and
      a smoke training run on it
- [ ] the pages show the same numbers as MLflow

Status: started 2026-10-16 (decision 17). Step 1: the boards Use cases
(the list and the import with its three answers), Use case (versions
and their diff, tasks, judges and gate, resources and hidden files) and
Task (input, expected, results across runs) are on the Design canvas,
version 23, in the Dataset row, with a note beside Dataset and Ticket
that they replace them once Lukas agrees; the menu item reads "Use
cases" on the new boards only. Support's tickets, judges, gate,
articles and policies are measured from `openshift-eval`'s
`tasks/support`; versions, hashes, the diff and the pyfix and
copywriter rows are illustrative. They wait for Lukas's review.
Steps 2 to 6, the plumbing, started 2026-10-16 in the odh-dashboard clone
on `feat/agent-flywheel-module`, from upstream commit `37dc648`, the one
ODH 3.6.0-ea.2's host and dashboard-operator run (`docs/research.md`
section 7), so our module and our dashboard-operator run beside ODH's
host; every page a placeholder until the boards are reviewed. That
branch is not merged into `flywheel-integration`, which is on
`upstream/main`.

- 2026-10-16, the branch: the `agentFlywheel` feature flag (off by
  default, declared as `agentOps` is), the package
  `packages/agent-flywheel` (placeholder pages, a Go BFF that forwards
  `/api/*` to `http://flywheel-api.agent-flywheel.svc:8080` with the
  user's token), the module in `modules.go` with its manifests (port
  9343), and a fork-only commit that points the bundle's `params.env` at
  our ImageStream `agent-flywheel-ui:latest`. ODH passes the
  dashboard-operator a fixed list of image keys, and the operator lays
  only non-empty ones over `params.env`, so the default there is what
  runs: no change to opendatahub-operator. The subagent's runs, twice:
  the package's type check, lint and 11 unit tests; the BFF's 25 Go
  tests under `-race`; the operator's 377 Go tests; golangci-lint 0
  issues. Not run: envtest and e2e (the sandbox, a cluster), and the dev
  server (the sandbox stops its file watcher, `EMFILE`).
- 2026-10-16, on the cluster: build `dashboard-operator-2` of
  `e98380b86` (`dashboard-operator:agent-flywheel`, digest `9c4f2797…`;
  the first build was killed for memory at 2 GiB, 8 GiB holds it) and
  build `agent-flywheel-ui-2` of `0d8575068` (the first failed: the Go
  stage ran as UID 1001 in a root-owned folder; `0d8575068` builds it as
  root, the final stage still runs as 65532). The Subscription's
  `RELATED_IMAGE_ODH_DASHBOARD_OPERATOR_IMAGE` points at our
  dashboard-operator since 18:06 CEST; it applied the CRD with
  `agentFlywheel`, the module's Deployment `agent-flywheel-ui` and its
  entry in `federation-config`, and `default-dsc` stayed Ready. Then
  `agentFlywheel: true` on `odh-dashboard-config`
  (`deploy/platform/dashboard`). The host serves our `remoteEntry.js` at
  `/_mf/agentFlywheel/remoteEntry.js`; `/agent-flywheel/api/*` reaches
  our BFF, which answers 503 until the flywheel API runs (phase 3,
  question 7). DoD item 1 is checked.
- 2026-10-16, the real pages (decision 18: the boards approved):
  `bae799cf6` (the BFF's mock in the API's exact shapes, made from
  support with the API's own registry code) and `3fbdc402a` (the Use
  cases, Use case and Task pages; `@patternfly/react-table` ~6.5.1, as
  eval-hub uses it). The subagent's runs, twice: type check, lint, 35
  unit tests, the BFF's 40 Go tests under `-race`, golangci-lint 0, the
  standalone bundle against the mock 28 of 28. Build
  `agent-flywheel-ui-3` of `3fbdc402a`; with the pod restarted, the agent
  opened all three pages on the cluster as `claude-agent` (18:25 CEST):
  `sample`'s version 1, its three questions by split, `reset-password`'s
  input and expected, 0 console errors. Start evaluation and Start
  training are disabled until the API has runs. The API gaps the pages
  show as one plain sentence each: no `reward` or `thresholds` (the
  gate), no runs or per-task results (MLflow), no source or diff per
  version in the list, no file contents or sizes, no EvalHub
  collection; a ref is a branch or a tag, and an upload is one archive.

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
  (`docs/research.md` section 5, "What C29 can reuse"). Checked for the
  operator on 2026-10-15 (phase 2 status); the `evalhub` pod waits for
  our EvalHub image. The sources are
  compared (2026-10-15, `docs/research.md` section 5, "Versions"): both
  ODH images are upstream code at a merge base plus CI files only, so a
  build from upstream `main` carries ODH's code and upstream's newer
  commits, and no `opendatahub-io` remote is needed. If our build from
  upstream `main` still does not run under ODH 3.6.0-ea.2, ask Lukas
  before basing `flywheel-integration` on the commit ODH built from.
- Checked 2026-10-16: EvalHub's S3 init container fetches a folder prefix
  (`ListObjectsV2` with `Prefix`, `cmd/eval_runtime_init/main.go`), so a
  version is read as its folder, with no archive. Its `secret_ref` Secret
  needs four keys, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
  `AWS_DEFAULT_REGION` and `AWS_S3_ENDPOINT`, each non-empty; the bucket
  claim's Secret holds only the first two (`docs/research.md` section 5).
  So the job's Secret is still to settle, and asked for before it is
  created or changed.
- Checked 2026-10-16: an `ObjectBucketClaim` works on `cluster-nm8mw`;
  `flywheel-usecases` (`deploy/bucket/`) was Bound within 6 seconds.
- Whether ODH's MLflow, with workspaces on, serves MLflow evaluation
  datasets.
- Whether the cluster reaches Hugging Face (phase 4).
- Whether the real agents run clean through the gateway on EnMaaS (spec 01
  decision 9). Each agent's request shape is checked; a full run of Claude
  Code, Codex and OpenCode is not. Phase 6 step 3 is the first.
- Spec 01 section 12 holds as well.

## 9. Open questions

Answered 2026-10-15: Lukas took every proposal below (decision 16). They
stay here as the text he said `ok` to.

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
