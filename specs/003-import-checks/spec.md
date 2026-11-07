---
status: planned
roadmap: standalone
step: 3
source: ["docs/my-specs/03-standalone.md#3.8"]
---
# Import Checks

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

The import accepts a use case whose tasks lack the fields the UI shows, whose `eval.yaml` puts `hidden/` into the workspace, or whose weights name judges that do not exist.
Each shows up later, in a run, or never; `hidden/` in the workspace leaks the answer key to the agent.

## What

- The import refuses: a task without the fields the UI shows; `hidden/` among `eval.yaml`'s workspace files; a weight for a judge that does not exist; no weight above 0.
- `usecase.yaml` takes `judges: {<name>: {label, live}}`; the module shows the label.
- Each refusal names the file and the field.

## Not this

- No local judge overlay (`extends:`), no plural task label.
- No judge for support's `needs_version_question` and `needs_escalation`.
- No use of `live` yet: online evaluation is not planned.

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
