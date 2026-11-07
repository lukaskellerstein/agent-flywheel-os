---
status: planned
roadmap: standalone
step: 10
depends_on: [005-task-traces]
source: ["docs/my-specs/03-standalone.md#3.3"]
---
# Adjust Checks

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

The Adjust step lacks four checks: a session runs even when no train task fails, a missing train task goes unnoticed, edits outside the brain vanish silently, and a paid adjuster's cost reads 0.
So a backend's cost and behaviour cannot be compared.

## What

- No failing train task: no session, the brain stays as it is.
- A train task missing from a full split fails the step; edits and deletions outside the brain are counted as `adjuster/ignored_edits`.
- Tags `adjust_backend`, `adjust_schedule`, `adjuster_model`, and the session's priced cost (0 USD on GLM 5.3).

## Not this

- No new backend (steps 11 and 12).
- No change to the leak rules.
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
