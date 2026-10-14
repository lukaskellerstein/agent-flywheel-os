---
description: "Step 4: Testing — define DoD, test, fix and repeat until passing"
---

# Step 4: Testing

**Every code change must be tested before reporting completion. No exceptions.**

## 4a. Define your Definition of Done

Before testing, **write out your DoD checklist in the conversation** so the user
can see what you intend to verify. Example:

> **Definition of Done for this task:**
>
> - [ ] The new button appears on the dashboard page
> - [ ] Clicking the button opens the modal
> - [ ] The modal displays the correct data
> - [ ] Browser closed after testing

## 4b. Test

**Glue, manifests and scripts** — this repo has no code and no test suite yet
(spec 02 §0). Until spec 02 phase 3 lands one:

- The current phase's Definition of Done in the active spec (spec 02 §6) is
  the test. Check every item, and write the result into that phase's status.
- A script is run, not read.
- A manifest reaches the cluster at least as
  `oc apply --dry-run=server -k <dir>`, after `oc whoami --show-server` shows
  the agent's own identity. The agent then applies it for real itself
  (cluster-admin, `CLAUDE.md` § Pre-approved mutations).

When spec 02 phase 3 lands a test command, it goes here.

**UI changes** — drive the dashboard with Playwright: the federated dev server
on `http://localhost:4010` (spec 01 phase 5 step 6), or the dashboard's route
on the cluster once phase 1 has installed it.

**The dashboard sits behind a login — read this before you open the browser.**
On the cluster it opens through ODH's Gateway login (spec 01 phase 1 step 4).
You have your own identity — the `claude-agent` ServiceAccount of spec 01
phase 0 step 4 — and nothing else. **Never fill in the sign-in form, never ask
the user for a password, and never read one out of SOPS.** A login page on your
screen means you took the human's path; back out. The Gateway is a reverse
proxy (kube-auth-proxy), and it accepts that ServiceAccount's Bearer token:
the dashboard's `/api/config`, `/api/status` and `/api/components` answered
200 with it on 2026-10-13, at `https://rh-ai.apps.cluster-nm8mw.dyn.redhatworkshops.io`.
So the first row of the table below applies. Whether the whole page renders
with the header alone is not checked yet; until it is, a page that does not
render is Lukas's to open — say so and hand him the click.
[`12-security.md`](12-security.md) § You have your own identity is the
authority, and it beats any memory that tells you otherwise.

How the token reaches the page depends on what does the gating:

| The gate | How you authenticate |
|:--|:--|
| A reverse proxy (OAuth2-Proxy, Access) in front of the app | `setExtraHTTPHeaders({ Authorization: 'Bearer …' })` **before** the first `goto` |
| The app's own browser login (an OIDC SPA, for example `keycloak-js`) | the header alone does nothing — the SPA holds its own token. Put a small local proxy in front of the API that injects the header, and let the app's ambient/pre-authenticated path take over |

The second row hides a real trap: injecting from `t=0` authenticates every
request, so it **masks** any bug where a view fetches before the app has its
token. If that timing is what you are testing, make the proxy start injecting
only once the app's auth probe has been served.

1. Confirm the dashboard is up (`curl -sI <url>` answers). If it is not, do not
   start it from here: the dev servers run in the `odh-dashboard` clone, and
   the federated one needs a cluster-admin login, so Lukas runs it (spec 01
   phase 5 step 6). Ask him.
2. Open a browser with the configured Playwright MCP `browser_navigate` tool, go to the
   relevant page, and verify the change is visible **and** functional — take a
   snapshot, don't just assert the page loaded.
3. **Close the browser (`browser_close`) when the test is finished.** Session-end
   cleanup is a safety net, not a substitute.

The browser is placed on its own desktop space by the shared Playwright hooks
(`.claude/hooks/` for Claude Code; linked from `.codex/hooks/` for Codex) —
never switch to it, focus it, or move it.

**Electron / CDP repos only:** start the app exclusively through
the current agent's `playwright-launch.sh <command...>` (for example,
`.codex/hooks/playwright-launch.sh npm run dev`) — never launch it directly.
The wrapper exports `PW_AGENT=1`; the app answers by tagging its window title
` [agent]`, which is what places the window on the `playwright` desktop at
birth. If the wrapper refuses because the CDP port already has a listener,
that instance is the user's: do not stop it and do not take the port — launch
on a free port if the app supports one, or ask the user.
If a `browser_*` call is denied because the instance on the CDP port was
started by the user: that instance is theirs. Do not touch it. Either launch
your own via the script above, or ask the user for permission and only after
an explicit yes run the `touch` command from the denial message.

**The no-touch rule covers every attach path, not just MCP tools.** A
`connectOverCDP` in your own script, a raw CDP request from `curl` — same
rule. The MCP gate cannot see inside a script, so before any script attaches
to the repo's CDP port, run `python3 <agent-hooks>/pw.py owns-port <port>`
yourself: exit 0 means proceed, exit 1 means the instance is the user's — ask.

**A headed browser your own script launches goes through the launch script
too** — `.claude/hooks/playwright-launch.sh npx tsx <script>` — so its window
is born on the scratch space like every other agent browser. Never launch a
headed browser bare: macOS creates new windows on whatever space the user is
looking at. A headless browser needs no placement — run that script directly.

**Every code change** — repo-wide lint / format / type check:

```bash
nvim-tools --json --all
```

Your change must not add findings, measured against the baseline you took in the
Understand step. How to read the output (including `gated-off`), and why this
never replaces the project's own suite: [`machine-tools.md`](machine-tools.md).

**Non-testable changes** (docs, config, IaC only): explicitly state why no
runtime test is needed.

## 4c. Fix and repeat

If a test fails: fix the issue, then retest. Repeat until all DoD items pass. If
you hit a problem you repeatedly cannot resolve, ask the user for help rather
than reporting partial success.

## 4d. Never report completion without testing

If you write code and stop without verifying it works, you have failed. Testing
is YOUR responsibility — the user should never need to ask you to test.
