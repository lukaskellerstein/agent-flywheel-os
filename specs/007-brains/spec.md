---
status: planned
roadmap: standalone
step: 7
depends_on: [001-training-record]
source: ["docs/my-specs/03-standalone.md#3.5"]
---
# Brains

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

The module's Brains page is a placeholder, and a use case's brain v0 is always empty.
A brain a training run made is evaluated only by typing its `runs:/<run>/brain` path.

## What

- One catalog of every brain, v0 and every version a training run made: its lineage, its files, its train and validation scores per judge, how it was made, where it was used.
- "Evaluate this brain" starts an evaluation that names it; Start evaluation gets a brain pick.
- An optional `brain/` folder in a use case is its v0.

## Not this

- No editing a brain by hand.
- No deleting a brain.
- No brain shared between use cases.

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
