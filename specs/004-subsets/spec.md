---
status: planned
roadmap: standalone
step: 4
depends_on: [003-import-checks]
source: ["docs/my-specs/03-standalone.md#3.2"]
---
# Subsets

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

Every evaluation and every training run scores the whole split, so a check of the whole loop costs a full run.
Nobody can score only the tasks they want to look at.

## What

- A task tag `smoke` marks a fixed small part of each split; support gets 4 train and 2 validation smoke tasks, of the same kinds as the full splits.
- Start evaluation and Start training take `subset: smoke`; Start evaluation also takes a list of picked task ids.
- A training run on `smoke` scores 6 tasks per iteration and reports only the tasks it scored.

## Not this

- No random sampling.
- No subset saved under a name of its own.
- No check that a full split is complete (step 10).

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
