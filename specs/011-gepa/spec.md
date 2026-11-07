---
status: planned
roadmap: standalone
step: 11
depends_on: [010-adjust-checks]
source: ["docs/my-specs/03-standalone.md#3.3"]
---
# Gepa

<!-- The spec in words, shaped with /spex:new. The records in requirements.yaml are what the gates read. -->

## Why

The Adjuster is the only Adjust backend. GEPA reached train 0.998 and validation 1.000 from 0.282 and 0.353 on the full support set,
but on smoke it copied train facts into `AGENTS.md` and validation fell from 0.675 to 0.237.

## What

- A GEPA backend (`gepa` 0.1.4) behind the Adjust contract: one reflection call per brain file, its records from `failures.md`, its answer replaces the whole file; a cut-off, reasoning-only or empty answer is refused.
- Its model is its own setting, through the gateway; the backend writes `change.md` for it.
- The schedule "Adjuster then GEPA"; Start training gets a backend pick.

## Not this

- GEPA never creates a skill and never reads `history.md`.
- Not through Training Hub.
- No guard against its leak beyond the existing leak rules.

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
