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
(the project, the related repos, the cluster), [`rules/09-code-quality.md`](rules/09-code-quality.md),
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
  glue (`README.md`).
- **Plan**: the plan lives in `docs/my-specs/`. `.claude/` holds
  instructions only: no plan, no phase, no status, no dates, no spec,
  decision or contribution numbers. Those belong in `docs/my-specs/`; never
  add them here.
- **Evidence**: `docs/research.md` holds every upstream fact behind the plan,
  with file and line; `README.md` indexes every file.
- **Other repos**: the fork clones in
  `~/Projects/Github/lukaskellerstein/forks/` are worked on from this
  session — `.claude/settings.json` opens that folder to
  the sandbox, and the agent here orchestrates subagents there. No git
  worktrees: one checkout per repo, the branch switched in the clone
  itself, never two subagents in one clone, and nothing created at the
  `forks/` level. That work needs a session started
  with `claude --no-worktree` in this repo's main checkout: a `claude -w`
  session cannot run git in another folder. Inside a fork,
  upstream's own `CLAUDE.md`, `AGENTS.md` and contribution rules win.
  The reference checkouts
  `~/Projects/Github/redhat/agent-eval-harness` and
  `~/Projects/Github/eval-hub/eval-hub` stay read-only — never branch there.
  `rules/worktree.md` is about this repo's own checkout, not the fork
  clones. Table:
  [`rules/01-project-config.md`](rules/01-project-config.md).
- **Pushes**: branches to Lukas's forks only — never to `upstream`, never to
  `main`, never `--force`. A PR, a fork, an issue or a public comment needs his
  explicit go each time. A push is a plain `git push` run in
  the fork folder: the ask rule matches only a command that starts with
  `git push`, so `git -C <dir> push` would run without a prompt.
- **Cluster**: RHDP single node `cluster-nm8mw`, OpenShift 4.22.16, namespace
  `agent-flywheel`. RHDP auto-stops it at a time only Lukas can move, and
  auto-destroys it at a date only he can move: an API that times out is
  that first, so ask him before debugging. Agents
  use their own ServiceAccount `claude-agent`, cluster-admin, never
  `~/.kube/config`. A SessionStart hook points
  `KUBECONFIG` at `~/.config/agent-kube/agent-flywheel-os.yaml`, so every
  `oc` runs inside the sandbox, without a prompt. When that file is missing,
  its token expired (`401 Unauthorized`) or the cluster is new, run
  `scripts/agent-kubeconfig.sh` yourself — alone (no pipe, no chain, no
  `bash` prefix) and with the sandbox disabled, the one command allowed
  unsandboxed. If it fails on Lukas's own login, ask him to `oc login`. If it
  refuses the server, his current context is another cluster (for
  example `kind-agentic`): ask him for the RHDP context's name and pass
  it as `ADMIN_CONTEXT`. While the token still works, renew it inside the
  sandbox instead, with no login of his:
  `ADMIN_KUBECONFIG=~/.config/agent-kube/agent-flywheel-os.yaml scripts/agent-kubeconfig.sh`.
- **Money**: one smoke call is fine; anything beyond is asked first, with its
  cost. A run on a model that is free on the gateway costs nothing.
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
  `start-build`, `adm`, operator installs, cluster-scoped objects: the agent
  runs the cluster on its own. Run `oc whoami --show-server` first and
  name the cluster and namespace in the report, not in a question.
- `scripts/agent-kubeconfig.sh`, to mint or renew the agent's own login.
- Fixing a wrong fact in the plan in `docs/my-specs/`, and writing a checked
  Definition of Done into the plan's status — in the same turn, and say so.
- Work in the fork clones: edits, branches from
  `upstream/main`, switching the branch in the clone
  `~/Projects/Github/lukaskellerstein/forks/<repo>` itself (no worktrees),
  and commits on the contribution branches and on
  `flywheel-integration` — never on `main`. Subagents the agent starts get
  the same rules in their brief.

### Requires confirmation — always ask first

- Any `oc` with `~/.kube/config` (Lukas's own login) — the agent never needs
  it beyond `scripts/agent-kubeconfig.sh`.
- An edit to `scripts/agent-kubeconfig.sh` or `deploy/agent-access/`: they
  run with Lukas's login, and the permission rules ask for them.
- A paid model run beyond one smoke call, with its cost.
- A PR, a fork, an issue or a comment on any upstream project or fork — each
  time. Drafted comments and PR texts are posted by Lukas, in his own voice.
  Issues come with the PRs, not before the work.
- Any edit in the reference checkouts, and a commit on a fork's `main`.
- A new top-level folder, beyond the layout in
  [`rules/05-implement.md`](rules/05-implement.md).
- Creating or reading a model key Secret. `enmaas` is Lukas's; `cerebras`
  and `openrouter` stay unread until he deletes them. A key never enters a
  file.
- `git push`, `git push --force`, branch deletes — **never commit in this repo
  unless the user explicitly asks** (fork commits: § Pre-approved mutations).
- Anything touching secrets, TLS material, tokens, or credential files. A secret
  never enters this repo in plaintext; if one must be versioned at all it is
  SOPS+age — [`rules/12-security.md`](rules/12-security.md).

When in doubt: ask. The forks and the upstream projects outlive this repo,
and a push or a comment lands where other people see it — check
`oc whoami --show-server` before any cluster command.
