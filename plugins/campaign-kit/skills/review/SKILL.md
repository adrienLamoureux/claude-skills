---
name: review
description: Judge a campaign-kit round — an Opus judge weighs the measurements against the brief, chooses continue / pivot / stop, and writes the next round's plan or the final report. Use when the user runs /campaign-kit:review, or asks to review, judge, assess or iterate on a campaign round, or for a campaign's progress or final report.
argument-hint: "<slug | run folder> [final]"
effort: medium
---

# Review and iterate

Step 3 of the campaign family: the **Reason** of the ReAct loop. The judge turns observations
into the next Thought. You relay its verdict and hold the checkpoints.

`TOOL` is `python3 <campaign-skill-dir>/scripts/campaign_tool.py` and `FORMATS` is
`<campaign-skill-dir>/references/formats.md`, where `<campaign-skill-dir>` is the base
directory shown when this skill loads with `review` replaced by `campaign`.

## Shell commands

Headless runs match each part of a chained command against the Bash allow-list separately. So
run one plain command per Bash call from the project root (no `&&`, `||`, `;`, pipes, `$(...)`
or shell variables such as `T=...`), run `TOOL` by its full path, and look at files with Read,
Grep and Glob, not `ls`, `cat` or `find`. A denial means that one command matched no rule, not
that Bash is off: retry it plainly or with Read, Grep or Glob. Stop only if a plain `TOOL` call
is denied, and name the rule it needs.

Give agents `DIR` as an absolute path (the project root joined with `.campaign-kit/<slug>/`),
so they never resolve it against another folder.

## Agent and effort

| Role | `subagent_type` | Effort |
|---|---|---|
| judge, plan next round, report (Opus) | `campaign-kit:campaign-judge` | `judge_effort` from `TOOL next`: `medium` routine round · `high` a lane failed or came back partial, or a metric regressed · `xhigh` criteria look met, last round, or final report |

Do not pass `model`. Use the effort the tool gives; it is computed from the checker's manifest
so routine rounds stay cheap.

## Workflow

1. **Where are we.** `TOOL next <DIR>`.
   - `review` → step 2 with `judge_effort`.
   - `report` → step 2 in final mode (effort `xhigh`), stating `final` = the tool's `final`
     and the output path = the tool's `write` (`<DIR>/outcome.md`).
   - `plan-round` → a round plan is missing. Round 1: launch
     `campaign-kit:campaign-strategist` (effort `high`) asking only for `rounds/1/plan.md`.
     Later rounds: relaunch the judge for round `n-1` asking only for `rounds/<n>/plan.md`
     (effort `medium`).
   - anything else → say which skill runs it and stop.
2. **Judge.** Launch `campaign-kit:campaign-judge` with: `DIR`, round `n`, rounds left
   (`max_rounds - n`), `FORMATS`, the check command `TOOL check <DIR>`, and final mode if
   asked or routed.
3. **Relay** (skip on a stop verdict or in final mode: step 5's recap replaces it) in at most
   10 lines: verdict and reason; each criterion `baseline → now → target`
   (`TOOL status <DIR>` gives the table cheaply); next round's actions, or the stop reason;
   anything the user must decide or do.
4. **Checkpoint.** `TOOL next <DIR>` again:
   - `approve-round` with `needs_user: true` (a pivot, or autonomy `checkpoint-each-round`) →
     ask the user with a decision card (below) to approve the next round; on yes,
     `TOOL approve <DIR> round <n>`.
   - `approve-round` with `needs_user: false` → approve it and say so.
   - `done` → step 5 first. Then, with `final: stop-blocked`, put each `needs_user` item from
     the review manifest to the user, one decision card each; once resolved, the campaign
     continues with a new round plan (judge) or a brief change (interview). Otherwise offer
     to publish a status page if the project-artifact plugin is installed.
5. **Recap.** The judge's reply ends with a recap block (`## recap.md` in `FORMATS`, at most
   eight lines). Check its criteria line against `TOOL status <DIR>` and its delivered paths
   against the `outcome` file (`outcome.md`; `report.md` in older runs), and correct anything
   that disagrees. If the reply has no block, build it from those two. Write it yourself, not
   through an agent, to the tool's `recap` path (`<DIR>/recap.md`, replacing an older one),
   and show it as is.

## Resume block and decision card

Before your first stop, read `<campaign-skill-dir>/references/stop-blocks.md` and follow it: at every stop write `<DIR>/resume.md`,
and end every stop that waits for the user's choice with its five-line decision card.
Where examples for this skill: brief · ready, round 2 · plan ready, round 3 · stop-blocked, done

## Rules

- The judge decides; do not override its verdict with your own reading. If it looks wrong,
  send it the specific doubt (SendMessage) and let it re-decide.
- The final report is `outcome.md`, never `report.md`: a subagent cannot write `report*.md`.
- Only the user changes the objective or the criteria. A judge proposal to do so arrives as
  `stop-blocked`; on the user's yes, edit the brief through the strategist
  (`/campaign-kit:interview`), not by hand.
