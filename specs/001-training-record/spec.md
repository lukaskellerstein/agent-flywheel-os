---
status: ready
roadmap: standalone
step: 1
source: ["docs/my-specs/03-standalone.md#3.1"]
---
# Training Record

## Why

The loop logs every metric at step 0 (`flywheel/flywheel_loop/mlflow.py:63`), so MLflow draws no training curve, and no iteration records its cost or its time.
Score results carry no hash of the brain, nor of the rest that decides a score, so Brains and Benchmarks cannot reuse or compare them.

## What

- The parent run gets, at step N for iteration N: `train/score`, `validation/score`, `train/<judge>`, `validation/<judge>`, `loss` (1 minus the train score), `elapsed_s`, `<split>/cost_usd`, `best/train_score`, `best/validation_score`.
- Every evaluation the flywheel API starts is tagged `brain_hash` (a hash of the brain's files) and `recipe` (a hash of the rest that decides a score; its parts are the open question below); the loop's iteration run carries both too.
- Kept as they are: `decision` per iteration, `best_iteration` and `stop_reason` on the parent.

## Not this

- No Stop, no log, no live tasks (step 2).
- No traces (step 5).
- No change to the keep rule.

## Who

- Lukas, and a team that trains an agent on its use case: they read a training run's curve, cost and time in MLflow's own run view.
- The module's Training pages, which read the same runs through the flywheel API: they must keep showing every training run, old and new.
- Steps 7 (Brains) and 8 (Benchmarks), which find and reuse evaluations by `brain_hash` and `recipe`.
- Surfaces: the training Job (the loop), the flywheel API's evaluation start, MLflow.

## Constraints

- No change in a fork: the loop and the flywheel API only.
- MLflow through its REST API, as the loop and the API call it now; no MLflow client library.
- The proof run is free: support on GLM 5.3 through the gateway, one training run.
- Training runs made before this step have no curve and no tags; they stay readable as they are.
- The cluster `cluster-nm8mw` auto-destroys on 2026-11-12: the proof run must happen before that, or on its successor.

## Success

- One free training run of support on GLM 5.3, three iterations, shows in MLflow a curve on its parent run: one point per scored iteration (v0 at step 0) for `train/score`, `validation/score` and `loss`, with `elapsed_s` and `train/cost_usd` at each step.
- Every evaluation of that run, and one started from Start evaluation, carries `brain_hash` and `recipe`; two evaluations of the same brain on the same split carry the same two values, and a changed brain gets a new `brain_hash`.
- The module's Training pages show that run and the runs made before this step.
- The offline suites of the flywheel API and the loop pass.

## Alternatives

- **Keep the numbers on each iteration's child run only**, as now, and compare child runs in MLflow. No single chart with a step axis, and no cost or time. Not picked.
- **The loop computes both hashes and tags only its own runs.** Cheaper, but an evaluation from Start evaluation or a benchmark has no tags, so step 8 cannot reuse it. Not picked (round 1).
- **The EvalHub adapter writes the tags.** It sees every job too, but it is a fork change and a PR for a flywheel-only idea (`forks/eval-hub-contrib`). Not picked.
- **Picked:** the flywheel API tags every evaluation it starts; the loop copies the tags and logs the curve.

## Open questions

- ●●○ What `recipe` hashes. Spec 03 says "the use case version, the split's tasks, the judge model, the runner's settings". But the judge model sits in `eval.yaml`, so the version's hash covers it; and an agent is never changed (a new wiring is a new name, `.claude/rules/05-implement.md` § `deploy/`), so the agent's name covers its runner settings. Proposed: `recipe` = a hash of the use case version's `hash`, the split, and the sorted ids of the tasks scored (so step 4's subsets get their own recipe). The agent and the model stay their own tags, not part of `recipe`.

## Decisions

- **The flywheel API writes `brain_hash` and `recipe` on every evaluation it starts**, as EvalHub job and experiment tags; the loop copies both onto its iteration run. `brain_hash` hashes the brain folder's files read from MLflow; an empty brain (v0) has one fixed hash. Reason: step 8 reuses any evaluation, not only the loop's, and the API builds every job (`services/flywheel-api/flywheel_api/evaluations.py:313`). So this step's scopes are `loop` and `evaluations`. (Lukas, round 1)
- **`<split>/cost_usd` is the agent's cost of that split's evaluation**, the metric `cost_usd` the EvalHub adapter already reports (`forks/eval-hub-contrib/adapters/agent-eval-harness/main.py:383`), priced by the API's `runner.pricing` and returned in the evaluation's `metrics`. No judge has a cost until step 6 adds an LLM judge; its cost joins then. Reason: no fork change in this step. (Lukas, round 2)
