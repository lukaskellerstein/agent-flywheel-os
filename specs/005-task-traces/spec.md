---
status: planned
roadmap: standalone
step: 5
depends_on: [001-training-record]
source: ["docs/my-specs/03-standalone.md#3.2"]
---
# Task Traces

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

A Score result in MLflow holds only numbers: to see why a task failed, one reads files.
The Adjust step leaves no trace either, so its backends cannot be compared by what they did.

## What

- Every Score result writes one MLflow trace per task: the agent's steps as spans, each judge's verdict and reason as feedback, tagged with the use case, its version, the task, the brain and `kind=task`.
- Every Adjust step writes one trace, `kind=adjuster`, with the session's steps.
- MLflow's own trace view shows both.

## Not this

- No traces of online conversations.
- No trace page in the module.
- No change to the scores.

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
