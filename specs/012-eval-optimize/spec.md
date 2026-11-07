---
status: planned
roadmap: standalone
step: 12
depends_on: [010-adjust-checks]
source: ["docs/my-specs/03-standalone.md#3.3"]
---
# Eval Optimize

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

The harness's own skill `/eval-optimize` is a third way to adjust a brain.
On a paid model it cost 0.54 USD per Adjust step, ten times the Adjuster; on GLM 5.3 it costs nothing.

## What

- A backend that runs one headless Claude Code session per Adjust step: `/eval-optimize` with one iteration on the train run, the gateway as the Anthropic API.
- Permission mode `dontAsk`, project settings only, at most 40 turns, Read, Write and Edit, and Bash only for `ls`, `cat`, `head`, `grep`, `find`, `wc`, `test` and the skill's `state.py`.
- Before the session: the best brain's train run folder, the skill alone, and a config with the judges' names, types and ranges.

## Not this

- Not the whole plugin: no hooks, no other commands.
- No judge prompts in the session.
- No evaluation of its own inside the session.

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
