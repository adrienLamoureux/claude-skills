---
name: execute
description: Run one round of an approved campaign — Sonnet runners execute every lane's action in parallel within the brief's guardrails, then a Sonnet checker independently verifies the lanes and re-measures the done criteria. Use when the user runs /campaign-kit:execute, or asks to run, execute or advance the next round or the lanes of a campaign-kit campaign. /campaign-kit:campaign calls this step in its loop.
argument-hint: "<slug | run folder>"
---

# Execute lanes

Step 2 of the campaign family: the **Act** and **Observe** of one ReAct round. You dispatch and
collect; you do not read lane work in detail.

`TOOL` is `python3 <campaign-skill-dir>/scripts/campaign_tool.py` and `FORMATS` is
`<campaign-skill-dir>/references/formats.md`, where `<campaign-skill-dir>` is the base
directory shown when this skill loads with `execute` replaced by `campaign`.

## Agents and effort

| Role | `subagent_type` | Model | Effort |
|---|---|---|---|
| act on one lane | `campaign-kit:campaign-runner` | Sonnet | the action's `effort` (`medium` or `high`), from `TOOL next` |
| observe and measure | `campaign-kit:campaign-checker` | Sonnet | `medium` |

Do not pass `model`.

## Workflow

1. **Where are we.** `TOOL next <DIR>` (DIR from the slug: `.campaign-kit/<slug>/`).
   - `execute` → step 2 with its `lanes` and `efforts`.
   - `check` → step 3.
   - `approve-round` → if `needs_user`, show the round's Thought and actions (from
     `rounds/<n>/plan.md`, the manifest only) and ask; on yes or when `needs_user` is false,
     `TOOL approve <DIR> round <n>`, then `TOOL next` again.
   - anything else → say which step it is and which skill runs it (`interview`, `review`), and
     stop.
2. **Act.** Launch one `campaign-kit:campaign-runner` per lane in `lanes`, all in the same
   message so they run in parallel, each with its effort from `efforts`. Brief: `DIR`, the
   round, the lane, report path `<DIR>/rounds/<n>/<lane>.md`. `TOOL check` already proved code
   lanes' owned paths are disjoint.
3. **Observe.** When every runner has replied, launch `campaign-kit:campaign-checker` in
   `round <n>` mode with `DIR` and `FORMATS`. It writes `rounds/<n>/check.md`.
4. **Report** in at most 8 lines: lane statuses, each criterion's value versus last round,
   regressions, and any `needs-human` lane with what it needs. Next: `/campaign-kit:review
   <slug>` (or the loop continues if `campaign` called this).

## Rules

- A runner that reports `needs-human` is never re-launched to "just do it". Its request goes to
  the user through the judge's verdict.
- Do not re-run a lane yourself or edit lane outputs; a failed lane is information for the
  judge.
- Never launch lanes of two different rounds at once.
