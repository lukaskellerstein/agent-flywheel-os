# Outreach: the Slack post to Red Hat colleagues

Written 2026-10-13 with Lukas, after his talk at Red Hat Innovate Together in
Prague (2026-10-06). Goal: find a sponsor who gives time, a cluster and a
model budget, and the person who decides about agent evaluate, benchmark and
train in OpenShift AI. Not posted when this file was written. Lukas decides
where and when.

Three parts: a short main post in a channel, a thread reply with the
details, and DMs. Send the DMs to the EvalHub and agent-eval-harness
maintainers a day before the channel post: the thread names their projects,
and they should not read it there first.

## 1. Main post (final draft)

```
Hi all 👋

Last week at Innovate Together in Prague I gave a talk on how to evaluate, benchmark and train AI agents on OpenShift. I built a working system for it. It is a proof of concept, not a product yet, but the core works end to end, and I think it can be more than a conference demo.

*The short version:* same model, same weights, one changed text file, and a support agent went from *0.649 to 0.910* on held-out tickets that training never used. The training run took under 20 minutes on OpenShift, with no GPU in the cluster (the model ran on a hosted API).

*What it does*
• *Evaluate*: runs an agent on a set of tasks, and 6 judges score every answer
• *Benchmark*: compares agents (OpenCode, Claude Code, Codex) on different models. A grid of 3 agents × 4 models × 5 runs took 21 minutes and 5.39 USD of agent model calls
• *Train*: a second agent rewrites the first agent's instructions and skills from the judges' feedback. A new version that scores worse is thrown away

Video (6 min): https://www.youtube.com/watch?v=VQWUJKX87vI
Write-up: https://www.kellerstein.org/blog/projects/agent-flywheel/

I think it fits on top of what we already have (EvalHub, agent-eval-harness, Training Hub, MLflow), and it can be generalized beyond support agents. Do you see value in it? And who would be the right person to talk to? Any reply or DM helps 🙏
```

## 2. Thread reply (final draft)

```
More detail, for those who want it 🧵

*Where it fits in what we already have*
• *EvalHub* (GA in Red Hat AI 3.5) runs and records evaluations. Today an EvalHub job evaluates a model endpoint, or agent traces that were already recorded. The flywheel puts a whole agent harness under test: OpenCode, Claude Code or Codex, with its instructions and skills, doing real tasks with tools. That could become an EvalHub provider. My scoring already runs as EvalHub jobs.
• *agent-eval-harness* (opendatahub-io) is the scoring engine I use. Several of my changes belong upstream there: an OpenCode runner, a held-out set with score-based keep or revert for its optimize step, and agents as a benchmark axis.
• *Training Hub* has GEPA, which optimizes prompts without a GPU. The flywheel already runs GEPA as one of its improve steps, so it could switch to Training Hub's.
• *MLflow* keeps every score and every trace.
• What stays on top is thin: the loop that joins them (score, improve, keep or revert; every step a Job, every agent version a ConfigMap), the agent × model benchmark grid, and a UI for it.

*Why it matters*
• This training does not touch the weights. It improves the agent's instructions and skills (AGENTS.md). So the loop runs in plain CPU pods, and the model can live anywhere behind a gateway. Every cluster has CPU. Not every cluster has GPUs.
• It works with the agents people already use, through one LiteLLM gateway. I ran it on hosted models and on local ones. A model served on OpenShift AI should plug in the same way (OpenAI-compatible API). I have not tested that yet.
• *Laptop to cluster.* The same loop runs on a laptop with Podman and on OpenShift, built from the same Containerfile. With a local model as agent and judge, a laptop run costs nothing in API fees.

*What is missing:* it is a proof of concept
• *Generic use cases.* Today the tasks, the judges and the knowledge base are about one support use case. A team cannot yet bring its own without code changes. That is the main work.
• *Sandboxing.* Agents under test must be treated as untrusted code. EvalHub has a proposed ADR for exactly this: a namespace per evaluation, then OpenShell, then Kata. My design points the same way, so I would rather help there than build a second one.

*What I would like to do next:* move these pieces into EvalHub and agent-eval-harness where they belong, and keep only the thin loop on top. For that I would need some time, a cluster and a small model budget (a training run cost 2 to 6 USD of model calls in my tests, judge not counted). If this sounds interesting, or you know who decides about it, please ping me.
```

After 2026-10-13 the plan went further than this text: the UI is now a
module of the OpenShift AI dashboard on Open Data Hub (`PLAN.md`). If the
post goes out later, say that in the last paragraph.

## 3. Direct message

To the people who own the pieces (agent-eval-harness, EvalHub and TrustyAI
maintainers; their commit history shows who they are), or to an OpenShift AI
product manager:

```
Hi <name> 👋 For my Innovate Together talk I built an evaluate / benchmark / train loop for AI agents on OpenShift, on top of agent-eval-harness and EvalHub. I think it could grow into an OpenShift AI feature. Would you have 5 minutes for the video? https://www.youtube.com/watch?v=VQWUJKX87vI
I would value your honest view. And if it is not your area, who should I ask?
```

For the EvalHub maintainers, add: `Your sandbox ADR (eval-hub PR #1059)
matches my design, and I would like to help there.`

## 4. Fact-check

Every claim was checked on 2026-10-13. The numbers come from
`openshift-eval` (`CLUSTER.md`, `PLAN.md`, the blog posts).

| Claim | Source |
|:--|:--|
| 0.649 → 0.910 on held-out tickets | `openshift-eval` `CLUSTER.md`, run `flywheel-8l25r`, 10 validation tickets |
| Training never used them | Keep or revert uses the train score only (`controller.py` `decide()`) |
| Under 20 minutes | 19 min 48 s, 6 CPU, 6 GiB |
| No GPU in the cluster | The plain RHDP OpenShift item; no GPU request in any template; the model ran on Cerebras |
| 6 judges | `eval/support/eval.yaml` |
| 3 × 4 × 5 grid, 21 min, 5.39 USD | `bench-4j9l7`, 21 min 21 s; 59 evaluations ran, 1 was reused; agents only, the judge is not priced |
| 2 to 6 USD per training run | 1.69 (`flywheel-ctpt6`), 1.92 (`phase6-cerebras-full-1`), 6.10 (`flywheel-8l25r`), judge not counted |
| Three agents, one LiteLLM gateway | `deploy/gateway/config/litellm.yaml` |
| Local models, free | The Unsloth routes with `EVAL_JUDGE=local` |
| Not generic yet | `eval/support` is hard-coded (`run_eval.py:173`, `:202`, `adjust.py:163`) |
| Sandboxing is a design only | `docs/my-specs/XX-sandboxing.md`, status "proposal" |
| EvalHub GA in Red Hat AI 3.5, agents included | The 3.5 press release; the IBM CLEAR article |
| OpenShift AI fine-tunes models | Kubeflow Trainer and Training Hub, from 3.3 |
| Training Hub has GEPA, no GPU | Its `gepa.py` (added 2026-06-05), its docs: "no local GPU" |
| EvalHub ADR for sandboxing | eval-hub PR #1059: namespace, then OpenShell (P1), then Kata (P2) |
| Video 6 min | 5:39 |

**Corrections made to the first drafts** (do not bring them back):

- "Agents need the same: evaluate, benchmark, train" ignored that EvalHub
  already evaluates agents. The text now pitches only what was not found.
- "A model served on OpenShift AI plugs in" was never tested. Now "should",
  and "not tested yet".
- "Keeps a version only if it scores better" was wrong: a tie is kept too.
  Now "a version that scores worse is thrown away".
- "60 evaluations … 5.39 USD": 59 ran, 1 was reused, the judge is not in the
  cost. Now it names the grid and "agent model calls".
- "A training run costs a few dollars" hid the 6.10 USD headline run. Now "2
  to 6 USD, judge not counted".
- "No Red Hat tool optimizes agent prompts" was wrong: Training Hub has had
  GEPA since 2026-06-05.
- "Far fewer clusters have GPUs" had no data. Now "Not every cluster has
  GPUs".
- "Same container image" is now "same Containerfile"; "free with a local
  model" needs the local judge too.

**Searched for and not found:** an OpenShift AI feature that improves an
agent's instructions automatically (the CLEAR article says prompts are
changed by hand), and one that compares coding-agent harnesses across
models. "I have not found" is the honest wording, not "it does not exist".

**Do not write:**

- That GEPA is part of OpenShift AI. Training Hub is in the 3.5 Ray image,
  but the 3.5 images pin 0.9.2 without the `[gepa]` extra.
- That "no operator release ships EvalHub". True only for the upstream
  TrustyAI operator; OpenShift AI ships it from 3.4, GA in 3.5.

## 5. Fixes for the blog

The post links to `https://www.kellerstein.org/blog/projects/agent-flywheel/`.
Two sentences there need a fix before the post goes out:

1. "Nothing here is special": "no operator release ships EvalHub yet" →
   "no upstream operator release". (`openshift-eval`
   `docs/my-specs/01-new-design.md` line 7 has the same wording.)
2. "Closer than the spread is a tie": "Sixty evaluations … ran in 21 minutes
   for 5.39 USD" → 59 ran and 1 was reused, and the cost does not include the
   judge.

## 6. Notes

- The repo `lukaskellerstein/openshift-eval` is private, so the drafts do not
  link it. People will ask for the code: decide the answer first ("happy to
  give access, DM me").
- Slack can show `*bold*` as plain stars after a paste. Turn on Preferences →
  Advanced → "Format messages with markup", or set bold by hand.
- Why the text is built this way: the result first, the technology second;
  two asks, an easy one ("do you see value?") and the one that matters ("who
  should I talk to?"); a short post, the detail in the thread; no "just a
  side project", no "sorry for the long post".
- Sentences for calls and meetings:
  - "Same model, same weights, one text file changed: 0.649 to 0.910."
  - "Training without a GPU: it changes the agent's instructions, not the
    model's weights."
  - "Evaluation, benchmark and training are one measurement, used three
    ways."
  - "Every step is a Job, every agent version is a ConfigMap, every score is
    an MLflow run."
  - "Who would be the right person to talk to about this?"
