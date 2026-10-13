---
description: "Step 3: Implement — coding rules and this project's layout"
---

# Step 3: Implement

Write clean code from the start. Follow these rules during implementation:

- Every edit stays in the checkout assigned to this session. Claude Code uses
  `.worktrees/<name>`; Codex uses its active Local or managed Worktree checkout
  and Handoff. Never edit another checkout — [`worktree.md`](worktree.md)
- Do NOT commit via `git` unless explicitly instructed by the user
- When creating diagrams or graphs, use `mermaid`
- Write clean code from the start — don't plan to "clean it up later"
- Refactor continuously — improve code structure immediately when you see issues
- Remove dead code — delete unused functions, variables, imports, and commented code
- Before changing any signature, renaming, or deleting something shared, find
  every caller with `findReferences` where the `LSP` tool is available — grep
  misses the ones spelled differently and finds ones that are not calls.
  [`lsp.md`](lsp.md)
- After writing code: review comments, clean up imports, check for side effects

## Top level

- `PLAN.md` — the integrated plan and its status. Section 0 is the handover:
  keep it true. When a fact in it turns out wrong, fix it in the same turn and
  say so; when a phase's Definition of Done is checked, write the result into
  its status before the next phase starts (`PLAN.md` §0, §6). Section 2 holds
  Lukas's decisions — change one only when he does.
- `README.md` — the repo's front page; points at `PLAN.md` §0.
- **This repo holds only the glue.** A change to agent-eval-harness, EvalHub,
  eval-hub-contrib, the TrustyAI operator or the dashboard is a contribution:
  it is made in that fork's clone, in a session started there, on its own
  branch (`PLAN.md` §5). Never vendor or copy upstream code in here to work
  around a gap — the gap goes into the catalogue (`PLAN.md` §7).
- **No new top-level folder before the phase 4 layout is agreed** with Lukas
  (`PLAN.md` §6, phase 4). Once it is, add a section here for each folder: what
  belongs in it, and what must not.

## Repository structure

```text
agent-flywheel-os/
├── .claude/      agent instructions — CLAUDE.md, rules/, hooks/, settings.json
├── .mcp.json     the Playwright MCP server, playwright-agent-flywheel-os
├── PLAN.md       the integrated plan — read section 0 first
└── README.md
```
