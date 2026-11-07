---
status: planned
roadmap: standalone
step: 13
depends_on: [006-llm-judge]
source: ["docs/my-specs/03-standalone.md#3.10"]
---
# Pyfix

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

Support is the only use case, so nothing shows that the flywheel works for any use case (spec 02 phase 6).
`pyfix` exists nowhere as data and must be written.

## What

- `usecases/pyfix/`: 12 small Python repositories with one bug each, 8 train and 4 validation; a task describes the bug as a user would.
- Judges: the hidden `pytest` passes (0.5), diff limits of at most 3 files and `tests/` untouched (0.1), an LLM judge `review` on the diff (0.4), the exit code (0).
- The agent may edit and run a shell, each task in its own sandbox; its output is the diff.

## Not this

- No `copywriter`.
- No real-world repositories.
- No paid run without asking first.

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
