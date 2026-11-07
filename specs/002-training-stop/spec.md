---
status: planned
roadmap: standalone
step: 2
depends_on: [001-training-record]
source: ["docs/my-specs/03-standalone.md#3.1"]
---
# Training Stop

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

A running training run cannot be stopped from the module, and on SIGTERM the loop marks the parent run FAILED.
While a run goes, nobody sees its log or which tasks are done.

## What

- Stop on the training run's page ends it within 30 seconds; its state reads "stopped" and its best brain so far is the result.
- The loop's log and each step's log are readable on the page; during a Score step the page shows the done tasks and their verdicts, refreshed every 5 seconds.
- A training run's id is checked new in its experiment before the start.

## Not this

- No pause or resume.
- No Score step page of its own (spec 03 section 3.9).
- No change to the keep rule.

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
