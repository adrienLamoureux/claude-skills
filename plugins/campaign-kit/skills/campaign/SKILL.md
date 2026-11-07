---
name: campaign
description: Run an open-ended objective as a resumable ReAct campaign — rounds of parallel lane runners, measured done criteria and an Opus judge deciding continue / pivot / stop. Use when the user runs /campaign-kit:campaign, or has a goal measured over many steps (raise coverage, cut latency or cost, migrate many call sites, clear a backlog, research and prototype options) that cannot be planned up front. For one ticket use /dev-kit:plan; for one condition a single session can reach, /goal is cheaper.
argument-hint: "<objective | slug | run folder>"
effort: medium
---

# Campaign

The campaign family in one command: **interview → execute lanes → review and iterate**, looped.
Use it when the right next step depends on what the last one revealed. When the whole change
can be specified up front, plan-and-execute (`/dev-kit:plan`) is cheaper.

`<skill-dir>` is the base directory shown when this skill loads. `TOOL` is
`python3 <skill-dir>/scripts/campaign_tool.py`.

## Shell commands

Headless runs match each part of a chained command against the Bash allow-list separately. So
run one plain command per Bash call from the project root (no `&&`, `||`, `;`, pipes, `$(...)`
or shell variables such as `T=...`), run `TOOL` by its full path, and look at files with Read,
Grep and Glob, not `ls`, `cat` or `find`. A denial means that one command matched no rule, not
that Bash is off: retry it plainly or with Read, Grep or Glob. Stop only if a plain `TOOL` call
is denied, and name the rule it needs.

Give agents `DIR` as an absolute path (the project root joined with `.campaign-kit/<slug>/`),
so they never resolve it against another folder.

## Before you start

Each step skill names its agents and their effort. You, the main session, orchestrate only:
you read `TOOL` output, agents' short replies and manifests, never lane work. That is what
keeps a long campaign affordable.

Unless the user asked for a campaign by name, when the objective is one checkable condition a single session can reach (a test suite
passes, a file covers every item) and needs no lanes, guardrails or rounds, say that a plain
`/goal <condition>` is cheaper (no strategist, checker or judge) and ask whether to run a
campaign anyway.

## The loop

Resolve `DIR`: an existing run folder or slug → `.campaign-kit/<slug>/`; otherwise the
argument is a new objective. Then repeat:

1. `TOOL next <DIR>`, write its `status` line on a line of its own, as is (a `/goal`
   condition reads it), and act on its `step`:

| `step` | Do |
|---|---|
| `interview`, `baseline`, `approve-brief`, `fix-brief` | follow the **interview** skill (`<skill-dir>/../interview/SKILL.md`) from that step |
| `approve-round`, `execute`, `check` | follow the **execute** skill (`<skill-dir>/../execute/SKILL.md`) |
| `review`, `report`, `plan-round` | follow the **review** skill (`<skill-dir>/../review/SKILL.md`), including its checkpoint |
| `fix-round`, `fix-check`, `fix-review` | send the tool's `errors` to the agent that wrote the file (judge for plans and reviews, checker for checks) and ask it to fix them |
| `done` | final recap (below) and stop |

2. After each review, give the user a two-line progress note (verdict; criteria now vs
   target), then go on unless a checkpoint needs them.
3. Stop and wait for the user whenever a step has `needs_user: true`, a verdict is
   `stop-blocked`, or a lane is `needs-human`. When you stop on a blocker you cannot clear (a
   denied `TOOL` call, a step that keeps failing), end with the line
   `campaign <slug>: blocked — <what would clear it>`.

Read each sub-skill file once per session, when its step first comes up; you do not need to
re-read it every round.

## Final recap

Every campaign ends with a résumé of at most eight lines, as `## recap.md` in
`references/formats.md` describes. When the loop reached `done` through the review skill, its
step 5 already wrote and showed `<DIR>/recap.md`: stop there. When the loop starts at `done` (a
finished campaign, resumed), show `recap.md` if `recap_written` is true; otherwise build it
from the `outcome` file `TOOL next` names (`outcome.md`, or `report.md` before 0.2.0) and
`TOOL status <DIR>`, write it to the tool's `recap` path, and show it.

If the project-artifact plugin is installed, offer a shareable status page. Do not commit
anything; the user decides what of the work to keep.

## Rules

- If the conversation is interrupted, `/campaign-kit:campaign <slug>` resumes from the files:
  `TOOL next` is the source of truth, not your memory.
- Long campaigns: keep your own messages short; the ledger is the narrative.
- Guardrails in the brief bind every agent. Never widen them yourself; a wider guardrail is a
  brief change the user approves.
- A blocked step stays blocked, even when a `/goal` keeps asking you to continue: never
  measure criteria, write a check or approve a round yourself to get past it. Report the
  blocker and what would clear it, and stop.

## Bundled files

- `references/formats.md` — the run folder, every manifest, verdicts, the ledger.
- `scripts/campaign_tool.py` — `next` (state machine and judge effort), `check`, `approve`,
  `status`.
