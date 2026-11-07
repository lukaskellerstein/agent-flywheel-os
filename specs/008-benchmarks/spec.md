---
status: planned
roadmap: standalone
step: 8
depends_on: [001-training-record, 004-subsets, 007-brains]
source: ["docs/my-specs/03-standalone.md#3.4"]
---
# Benchmarks

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

Choosing what to release needs one validation split scored for each agent, model and brain, several times: v0's train score moved from 0.33 to 0.47 over four runs of the same tasks.
Today each evaluation is started by hand, and nothing compares them.

## What

- The flywheel API runs a grid of agent × model × brain on one use case version's validation split, 1 to 5 runs per cell (default 3), at most 3 agents, 8 models and 6 brains.
- An evaluation with the same agent, model, `brain_hash` and `recipe` is reused; a 16-token probe per model before the start; at most 12 evaluations at once; a failed evaluation fails its run, not the benchmark.
- A parent MLflow run `kind=benchmark` with `plan.json` and `result.json`: per cell the mean, the lowest and highest run, each judge's mean, USD per 1,000 tasks, seconds per task; an estimate before the start; Stop.

## Not this

- No pages (step 9).
- No variants as a fourth axis.
- No benchmark on the train split.

## Who

<!-- The users, and the surfaces they touch (CLI, UI, API, job). -->

## Constraints

<!-- Tech, time, cost, compatibility. -->

## Success

<!-- How we know it worked, with a number where one exists. -->

## Alternatives

<!-- Two or three other ways to get the same outcome, with sources, and why not. -->

## Open questions

<!-- One per line, each with its size first: ●●● big (the idea does not work without the answer) · ●●○ medium (changes scope, cost or a decision) · ●○○ small (wording, nice-to-have). -->

## Decisions

<!-- What was decided while shaping this, with the reason and the source. Grows over time. -->
