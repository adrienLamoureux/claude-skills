---
name: review
description: Review a campaign round and decide what happens next — an Opus judge weighs the checker's measurements against the brief, chooses continue / pivot / stop, keeps the ledger, writes the next round's plan or the final report; its effort scales with the round (routine, failing, final). Use when the user runs /campaign-kit:review, or asks to review, judge, assess or iterate on a campaign-kit round, or for a campaign's progress or final report. /campaign-kit:campaign calls this step in its loop.
argument-hint: "<slug | run folder> [final]"
---

# Review and iterate

Step 3 of the campaign family: the **Reason** of the ReAct loop. The judge turns observations
into the next Thought. You relay its verdict and hold the checkpoints.

`TOOL` is `python3 <campaign-skill-dir>/scripts/campaign_tool.py` and `FORMATS` is
`<campaign-skill-dir>/references/formats.md`, where `<campaign-skill-dir>` is the base
directory shown when this skill loads with `review` replaced by `campaign`.

## Agent and effort

| Role | `subagent_type` | Model | Effort |
|---|---|---|---|
| judge, plan next round, report | `campaign-kit:campaign-judge` | Opus | `judge_effort` from `TOOL next`: `medium` routine round · `high` a lane failed or a metric regressed · `xhigh` criteria look met, last round, or final report |

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
     ask the user to approve the next round; on yes, `TOOL approve <DIR> round <n>`.
   - `approve-round` with `needs_user: false` → approve it and say so.
   - `done` → step 5 first. Then, with `final: stop-blocked`, put each `needs_user` item from
     the review manifest to the user, one question each; once resolved, the campaign
     continues with a new round plan (judge) or a brief change (interview). Otherwise offer
     to publish a status page if the project-artifact plugin is installed.
5. **Recap.** The judge's reply ends with a recap block (`## recap.md` in `FORMATS`, at most
   eight lines). Check its criteria line against `TOOL status <DIR>` and its delivered paths
   against the `outcome` file (`outcome.md`; `report.md` in older runs), and correct anything
   that disagrees. If the reply has no block, build it from those two. Write it yourself, not
   through an agent, to the tool's `recap` path (`<DIR>/recap.md`, replacing an older one),
   and show it as is.

## Rules

- The judge decides; do not override its verdict with your own reading. If it looks wrong,
  send it the specific doubt (SendMessage) and let it re-decide.
- The final report is `outcome.md`, never `report.md`: Claude Code refuses a subagent's Write
  to `.md` files named `report*`, `summary*`, `findings*` or `analysis*`.
- Only the user changes the objective or the criteria. A judge proposal to do so arrives as
  `stop-blocked`; on the user's yes, edit the brief through the strategist
  (`/campaign-kit:interview`), not by hand.
