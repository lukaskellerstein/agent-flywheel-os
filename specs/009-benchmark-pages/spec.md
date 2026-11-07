---
status: planned
roadmap: standalone
step: 9
depends_on: [008-benchmarks]
source: ["docs/my-specs/03-standalone.md#3.4"]
---
# Benchmark Pages

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

A benchmark is readable only through the API and MLflow; the module's Benchmarks page is a placeholder.
Choosing a cell means reading JSON.

## What

- After a board Lukas approves: the list of benchmarks.
- New: the picks, the runs per cell, the estimate.
- One benchmark: its numbers, the matrix, score against cost, by judge, the leaderboard, its evaluations, Stop.

## Not this

- No API change beyond what step 8 serves.
- No editing a running benchmark.
- No export.

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
