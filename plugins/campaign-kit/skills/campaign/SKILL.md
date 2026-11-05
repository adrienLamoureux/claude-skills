---
name: campaign
description: Run an open-ended, multi-lane objective as a ReAct campaign — interview the user, then loop rounds of parallel Sonnet lane runners, a Sonnet checker that measures done criteria, and an Opus judge that decides continue / pivot / stop and plans the next round — until the criteria are met, the user is needed, or the budget runs out. Resumable from its run folder. Use when the user runs /campaign-kit:campaign, or has a goal measured over many steps (raise coverage, cut latency or cost, migrate many call sites, clear a backlog, research and prototype options) that cannot be fully planned up front. For one well-defined ticket, use /dev-kit:plan instead.
argument-hint: "<objective | slug | run folder>"
---

# Campaign

The campaign family in one command: **interview → execute lanes → review and iterate**, looped.
Use it when the right next step depends on what the last one revealed. When the whole change
can be specified up front, plan-and-execute (`/dev-kit:plan`) is cheaper.

`<skill-dir>` is the base directory shown when this skill loads. `TOOL` is
`python3 <skill-dir>/scripts/campaign_tool.py`.

## Model routing (the whole family)

| Step | Agent | Model | Effort |
|---|---|---|---|
| brief, round 1 | `campaign-kit:campaign-strategist` | Opus | medium / high / xhigh by scope |
| baselines, observation | `campaign-kit:campaign-checker` | Sonnet | medium |
| lane actions | `campaign-kit:campaign-runner` | Sonnet | medium / high per action, set by the judge |
| judgement, next round, report | `campaign-kit:campaign-judge` | Opus | medium / high / xhigh, computed by `TOOL next` |

You, the main session, orchestrate only: you read `TOOL` output, agents' short replies and
manifests, never lane work. That is what keeps a long campaign affordable.

## The loop

Resolve `DIR`: an existing run folder or slug → `.campaign-kit/<slug>/`; otherwise the
argument is a new objective. Then repeat:

1. `TOOL next <DIR>` and act on its `step`:

| `step` | Do |
|---|---|
| `interview`, `baseline`, `approve-brief`, `fix-brief` | follow the **interview** skill (`<skill-dir>/../interview/SKILL.md`) from that step |
| `approve-round`, `execute`, `check` | follow the **execute** skill (`<skill-dir>/../execute/SKILL.md`) |
| `review`, `report`, `plan-round` | follow the **review** skill (`<skill-dir>/../review/SKILL.md`), including its checkpoint |
| `fix-round`, `fix-check`, `fix-review` | send the tool's `errors` to the agent that wrote the file (judge for plans and reviews, checker for checks) and ask it to fix them |
| `done` | final summary (below) and stop |

2. After each review, give the user a two-line progress note (verdict; criteria now vs
   target), then go on unless a checkpoint needs them.
3. Stop and wait for the user whenever a step has `needs_user: true`, a verdict is
   `stop-blocked`, or a lane is `needs-human`.

Read each sub-skill file once per session, when its step first comes up; you do not need to
re-read it every round.

## Final summary

From the final report (the `outcome` path that `TOOL next` gives: `outcome.md`, or `report.md`
in a run started before campaign-kit 0.2.0) and `TOOL status <DIR>`: each criterion
`baseline → final` (met or not), rounds used of the budget, what each lane delivered, open
items and the user's to-dos. If the
project-artifact plugin is installed, offer a shareable status page. Do not commit anything; the
user decides what of the work to keep.

## Rules

- If the conversation is interrupted, `/campaign-kit:campaign <slug>` resumes from the files:
  `TOOL next` is the source of truth, not your memory.
- Long campaigns: keep your own messages short; the ledger is the narrative.
- Guardrails in the brief bind every agent. Never widen them yourself; a wider guardrail is a
  brief change the user approves.

## Bundled files

- `references/formats.md` — the run folder, every manifest, verdicts, the ledger.
- `scripts/campaign_tool.py` — `next` (state machine and judge effort), `check`, `approve`,
  `status`.
