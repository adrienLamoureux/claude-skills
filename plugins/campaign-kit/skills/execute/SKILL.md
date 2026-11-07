---
name: execute
description: Run one round of an approved campaign-kit campaign — Sonnet runners act on every lane in parallel within the brief's guardrails, then a checker verifies the lanes and re-measures the done criteria. Use when the user runs /campaign-kit:execute, or asks to run, execute or advance the next round or the lanes of a campaign.
argument-hint: "<slug | run folder>"
effort: medium
---

# Execute lanes

Step 2 of the campaign family: the **Act** and **Observe** of one ReAct round. You dispatch and
collect; you do not read lane work in detail.

`TOOL` is `python3 <campaign-skill-dir>/scripts/campaign_tool.py`, where
`<campaign-skill-dir>` is the base directory shown when this skill loads with `execute`
replaced by `campaign`.

## Shell commands

Headless runs match each part of a chained command against the Bash allow-list separately. So
run one plain command per Bash call from the project root (no `&&`, `||`, `;`, pipes, `$(...)`
or shell variables such as `T=...`), run `TOOL` by its full path, and look at files with Read,
Grep and Glob, not `ls`, `cat` or `find`. A denial means that one command matched no rule, not
that Bash is off: retry it plainly or with Read, Grep or Glob. Stop only if a plain `TOOL` call
is denied, and name the rule it needs.

Give agents `DIR` as an absolute path (the project root joined with `.campaign-kit/<slug>/`),
so they never resolve it against another folder.

## Agents and effort

| Role | `subagent_type` | Effort |
|---|---|---|
| act on one lane (Sonnet; Opus for a lane in `models`) | `campaign-kit:campaign-runner` | the action's `effort` (`medium` or `high`), from `TOOL next` |
| observe and measure (Sonnet) | `campaign-kit:campaign-checker` | `medium` |

Pass `model: opus` only for a lane that `TOOL next` lists under `models` (the judge escalated it
after a failure, and `TOOL check` allowed it); otherwise do not pass `model`.

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
   message so they run in parallel, each with its effort from `efforts` (and its model from `models`). Brief: `DIR` (absolute),
   the round, the lane, report path `<DIR>/rounds/<n>/<lane>.md`. `TOOL check` already proved code
   lanes' owned paths are disjoint.
3. **Place blocked files.** Claude Code refuses a subagent's Write to a `.md` file whose name
   starts with `report`, `summary`, `findings` or `analysis`, so a runner writes such a
   deliverable under another name and lists it in its lane report under `## Files to place`
   (`` `docs/draft-report.md` -> `docs/report.md` ``). Grep the round's lane reports for that
   heading. Move each listed draft into place with `mv` when both paths are inside the lane's
   owned paths (for a lane with no `owns`, any path the guardrails allow); leave the rest for
   the checker to flag.
4. **Observe.** When every runner has replied and files are placed, launch
   `campaign-kit:campaign-checker` in `round <n>` mode with `DIR`. It writes
   `rounds/<n>/check.md`.
5. **Report** in at most 8 lines: lane statuses, each criterion's value versus last round,
   regressions, and any `needs-human` lane with what it needs. Next: `/campaign-kit:review
   <slug>` (or the loop continues if `campaign` called this).

## Rules

- A runner that reports `needs-human` is never re-launched to "just do it". Its request goes to
  the user through the judge's verdict.
- Do not re-run a lane yourself or edit lane outputs; a failed lane is information for the
  judge. Moving a listed draft into place (step 3) is the one exception.
- Never launch lanes of two different rounds at once.
