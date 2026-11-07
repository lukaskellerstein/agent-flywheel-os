---
status: planned
roadmap: standalone
step: 6
depends_on: [003-import-checks]
source: ["docs/my-specs/03-standalone.md#3.2"]
---
# Llm Judge

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

Support's judges are all deterministic: none rates whether an answer is good.
A judge model inside the EvalHub job pod has no route to the gateway yet (`usecases/support/eval.yaml:8-11`).

## What

- The harness's judge in the job pod calls the cluster's gateway, with no key.
- Support's judge `quality`: a rubric for a senior support engineer, a score from 1 to 5, three samples and their median, weight 0.20, threshold 4.0, on GLM 5.3 first.
- Support version 2 carries it; a free evaluation shows `quality` with three samples per task.

## Not this

- No paid judge model by default.
- The judge never sees `hidden/`; it gets a short summary of the policies in its prompt.
- No `review` judge for `pyfix` (step 13).

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
