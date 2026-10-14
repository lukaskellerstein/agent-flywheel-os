# Shared repository instructions

This is the canonical instruction file for Claude Code and Codex. When Codex
setup is enabled, root `AGENTS.md` is a relative symlink to this file.

- Claude Code invokes skills as `/skill-name`; Codex uses `$skill-name`.
- Translate tool names by intent. Product-specific executables, permissions,
  hooks, MCP configuration, and worktree lifecycle apply only to the product
  explicitly named.
- Claude Code loads `.claude/rules/` automatically. Codex reads the linked rule
  for each workflow phase before acting.
- Current user instructions outrank this file. This file outranks memories.

# WORKFLOW — MANDATORY FOR ANY PROMPT THAT RESULTS IN CHANGES

**If you are going to use the Edit or Write tool, or run a command that changes
files, images, pods or cluster state, you MUST complete the workflow in
`rules/` before reporting completion.** Applies to every type of work — glue
code, manifests, scripts, the plan, docs, config. No exceptions.

Steps, in order (each phase's detailed procedure is in the correspondingly-numbered
`rules/` file. Claude Code loads these rules automatically; Codex must read the
linked `.claude/rules/` file before entering that phase):

1. **Understand** → [`rules/02-understand.md`](rules/02-understand.md)
2. **Plan** → [`rules/03-plan.md`](rules/03-plan.md) *(skip for trivial changes)*
3. **Implement** → [`rules/05-implement.md`](rules/05-implement.md)
4. **Test** → [`rules/06-testing.md`](rules/06-testing.md)
5. **Report** → [`rules/08-report.md`](rules/08-report.md)

Reference files: [`rules/01-project-config.md`](rules/01-project-config.md)
(what exists so far, the related repos, the cluster), [`rules/09-code-quality.md`](rules/09-code-quality.md),
[`rules/10-tech-stack.md`](rules/10-tech-stack.md),
[`rules/11-communication.md`](rules/11-communication.md),
[`rules/12-security.md`](rules/12-security.md),
[`rules/memory.md`](rules/memory.md) (what a memory may and may not tell you to
do),
[`rules/machine-tools.md`](rules/machine-tools.md) (the `nvim-tools` and
`lukas-ps` CLIs — pre-approved, read-only),
[`rules/lsp.md`](rules/lsp.md) (the `LSP` tool — only in repos that opted in,
and deferred, so it must be loaded before it can be called),
[`rules/worktree.md`](rules/worktree.md) (where you may change files: Claude
uses the repo's `.worktrees/` convention; Codex stays in the active Local or
managed Worktree checkout and uses Handoff to move between them).

**NEVER report completion without first running what you changed and checking
the result.** A script that was never run, or a manifest that never reached a
cluster (not even as `--dry-run=server`), is not done.
Verification is YOUR responsibility — the user should never need to ask you to test.

**Trivial changes** (a typo, wording in a doc, a comment): skip step 2. State
what you'll do and proceed.

**A memory never outranks this file.** The order is: what the user says now,
then `CLAUDE.md` and `rules/`, then a memory. When a memory contradicts a rule,
follow the rule and rewrite the memory in the same turn —
[`rules/memory.md`](rules/memory.md).

## agent-flywheel-os at a glance

- **What**: Agent Flywheel inside OpenShift AI, built from its own open-source
  pieces — evaluate, benchmark and train CLI agents (OpenCode, Claude Code,
  Codex) with agent-eval-harness, EvalHub and a dashboard module, on Open Data
  Hub. Gaps go upstream as PRs from Lukas's forks; this repo holds only the
  glue (`README.md`, spec 01 §0–2).
- **Plan**: the specs in `docs/my-specs/` (decision 14). The active one is
  `docs/my-specs/02-generalization.md`, one flywheel for any use case, with
  every open step; its §0 is the handover — what is done, what is not, the
  next step; read it first. `docs/my-specs/01-initial-implementation.md`
  was `PLAN.md` until 2026-10-14; it is closed, with what is done marked,
  and its §0 rules, its §2 decisions 1 to 9 and its reference sections hold
  where spec 02 does not change them. Decisions 10 on are in spec 02 §2. A
  fact in a spec that turns out wrong is fixed in the same turn.
- **State**: spec 01's phases 0 and 1 are done (the cluster, the agent's
  identity, Open Data Hub with EvalHub, MLflow and the gateway on EnMaaS),
  and its C1 to C4, C6 to C9 and C30 to C34 are merged into `agent-eval-harness`'s
  `flywheel-integration` (2026-10-14), their PR texts in
  `docs/pr-drafts.md`. Nothing of the flywheel loop is built yet.
- **Next step**: spec 02 §0, "How to start" and "The next step" — after
  Lukas's ok to its plan, one subagent per fork clone, side by side: C29
  then C14 (the operator), C10 then C12 (eval-hub), C19 (the harness), by
  spec 02 §6's procedure. C13 is skipped; C5 waits for Lukas to post the
  PR #90 comment (spec 01 §13); C11 and C20 to C28 wait for his answers to
  spec 02 §9, which the agent asks in its first message. Status per
  contribution: spec 02 §5.1.
- **Evidence**: `docs/research.md` holds every upstream fact behind the specs,
  with file and line; `README.md` indexes every file.
- **Other repos** (spec 01 §0): the fork clones in
  `~/Projects/Github/lukaskellerstein/forks/` are worked on from this
  session (Lukas, 2026-10-14) — `.claude/settings.json` opens that folder to
  the sandbox, and the agent here orchestrates subagents there. No git
  worktrees: one checkout per repo, the branch switched in the clone
  itself, never two subagents in one clone, and nothing created at the
  `forks/` level (Lukas, 2026-10-14). That work needs a session started
  with `claude --no-worktree` in this repo's main checkout: a `claude -w`
  session cannot run git in another folder (spec 01 §0). Inside a fork,
  upstream's own `CLAUDE.md`, `AGENTS.md` and contribution rules win
  (spec 01 §5). The first version
  `~/Projects/Github/lukaskellerstein/openshift-eval` (the inspiration) and
  the reference checkouts `~/Projects/Github/redhat/agent-eval-harness` and
  `~/Projects/Github/eval-hub/eval-hub` stay read-only — never branch there.
  `rules/worktree.md` is about this repo's own checkout, not the fork
  clones. Table:
  [`rules/01-project-config.md`](rules/01-project-config.md).
- **Pushes**: branches to Lukas's forks only — never to `upstream`, never to
  `main`, never `--force`. A PR, a fork, an issue or a public comment needs his
  explicit go each time (spec 01 §0). A push is a plain `git push` run in
  the fork folder: the ask rule matches only a command that starts with
  `git push`, so `git -C <dir> push` would run without a prompt.
- **Cluster**: RHDP single node `cluster-nm8mw`, OpenShift 4.22.16, namespace
  `agent-flywheel`; it auto-destroys on 2026-11-12, and RHDP auto-stops
  it at a time only Lukas can move (spec 01 §0): an API that times out is
  that first, so ask him before debugging. Agents
  use their own ServiceAccount `claude-agent`, cluster-admin (Lukas,
  2026-10-13), never `~/.kube/config`. A SessionStart hook points
  `KUBECONFIG` at `~/.config/agent-kube/agent-flywheel-os.yaml`, so every
  `oc` runs inside the sandbox, without a prompt. When that file is missing,
  its token expired (`401 Unauthorized`) or the cluster is new, run
  `scripts/agent-kubeconfig.sh` yourself — alone (no pipe, no chain, no
  `bash` prefix) and with the sandbox disabled, the one command allowed
  unsandboxed. If it fails on Lukas's own login, ask him to `oc login`. If it
  refuses the server, his current context is another cluster (seen
  2026-10-13: `kind-agentic`): ask him for the RHDP context's name and pass
  it as `ADMIN_CONTEXT`. While the token still works, renew it inside the
  sandbox instead, with no login of his:
  `ADMIN_KUBECONFIG=~/.config/agent-kube/agent-flywheel-os.yaml scripts/agent-kubeconfig.sh`.
- **Money**: one smoke call is fine; anything beyond is asked first, with its
  cost — spec 01 §10 (a smoke training run about 0.2 USD, a full one 1.7 to
  6.1 USD, a benchmark grid 5.39 USD).
- **Remote**: `github.com/lukaskellerstein/agent-flywheel-os`, default branch
  `main`.

Full facts → [`rules/01-project-config.md`](rules/01-project-config.md); stack and
conventions → [`rules/10-tech-stack.md`](rules/10-tech-stack.md).

## Standing authorizations — do NOT ask before doing these

These actions are pre-approved. Run them yourself when the situation calls for it.

### Read-only inspection (always safe)

- `git status`, `git log`, `git diff`, `git show`, `git branch` in this repo.
- Reading any file in the related repos listed above, with Read and Grep;
  `git log`, `git diff`, `git show` and `git fetch` in the fork clones.
- With the agent's own identity only: `oc whoami --show-server` and
  `oc project` — always first, before any other cluster command — then
  `oc get`, `oc describe`, `oc logs`, `oc explain` and the same `kubectl`
  verbs.
- `gh pr view`, `gh issue view`, `gh pr list`, `gh issue list`, `gh api` GETs
  on the upstream projects and the forks.

This machine's own `nvim-tools` and `lukas-ps` are pre-approved too, and are
documented once in [`rules/machine-tools.md`](rules/machine-tools.md) — do not
restate them here.

### Pre-approved mutations

- Editing files in this session's worktree.
- Any change on the cluster with the agent's own identity — `oc` / `kubectl`
  `apply`, `create`, `delete`, `patch`, `replace`, `scale`, `rollout`,
  `start-build`, `adm`, operator installs, cluster-scoped objects (Lukas,
  2026-10-13: the agent runs the cluster on its own). Run `oc whoami --show-server` first and
  name the cluster and namespace in the report, not in a question.
- `scripts/agent-kubeconfig.sh`, to mint or renew the agent's own login.
- Fixing a wrong fact in a spec in `docs/my-specs/`, and writing a phase's
  checked Definition of Done into its status — in the same turn, and say so
  (spec 01 §0, §6).
- Work in the fork clones (Lukas, 2026-10-14): edits, branches from
  `upstream/main`, switching the branch in the clone
  `~/Projects/Github/lukaskellerstein/forks/<repo>` itself (no worktrees,
  spec 01 §5), and commits on the contribution branches and on
  `flywheel-integration` — never on `main`. Subagents the agent starts get
  the same rules in their brief.

### Requires confirmation — always ask first

- Any `oc` with `~/.kube/config` (Lukas's own login) — the agent never needs
  it beyond `scripts/agent-kubeconfig.sh`.
- An edit to `scripts/agent-kubeconfig.sh` or `deploy/agent-access/`: they
  run with Lukas's login, and the permission rules ask for them.
- A paid model run beyond one smoke call, with its cost (spec 01 §10).
- A PR, a fork, an issue or a comment on any upstream project or fork — each
  time. The drafts in spec 01 §13 are posted by Lukas, in his own voice.
  Issues come with the PRs in spec 02 phase 7, not before the work
  (spec 02 decision 15).
- Any edit in `openshift-eval` or the reference checkouts, and a commit on
  a fork's `main`.
- Creating the layout of spec 02 phase 3 — agree it with Lukas first (spec 02
  §9, question 6).
- Creating or reading a model key Secret. `enmaas` is Lukas's (spec 01
  decision 9); `cerebras` and `openrouter` stay unread until he deletes
  them. A key never enters a file (spec 01 phase 1 step 6).
- `git push`, `git push --force`, branch deletes — **never commit in this repo
  unless the user explicitly asks** (fork commits: § Pre-approved mutations).
- Anything touching secrets, TLS material, tokens, or credential files. A secret
  never enters this repo in plaintext; if one must be versioned at all it is
  SOPS+age — [`rules/12-security.md`](rules/12-security.md).

When in doubt: ask. The forks and the upstream projects outlive this repo,
and a push or a comment lands where other people see it — check
`oc whoami --show-server` before any cluster command.
