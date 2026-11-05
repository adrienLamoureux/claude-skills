---
name: review
description: Review the work of a dev-kit plan before it is committed — a Sonnet checker re-runs the gates fresh, then an Opus reviewer judges the diff against plan.md (contracts, acceptance criteria, non-goals) and for correctness, security and test gaps, and writes review.md with approve / changes-required / blocked. Use when the user runs /dev-kit:review, or asks to review, judge or sign off the implementation of a dev-kit plan. For a plain diff or PR with no dev-kit plan, the built-in /code-review fits better.
argument-hint: "<slug | run folder> [effort=medium|high|xhigh]"
---

# Review

Step 3 of the developer family: **plan → implement → review**. A judge that did not write the
code reads it against the plan. You relay the verdict and route what happens next.

`TOOL` means `python3 <plan-skill-dir>/scripts/plan_tool.py`, where `<plan-skill-dir>` is the
base directory shown when this skill loads with `review` replaced by `plan`.

## Agents and effort

| Role | `subagent_type` | Model | Effort |
|---|---|---|---|
| fresh gate evidence | `dev-kit:dev-checker` | Sonnet | `medium` |
| judge the change | `dev-kit:dev-reviewer` | Opus | S `medium` · M `high` · L `xhigh`; also `xhigh` when the diff touches auth, payments, migrations or secrets handling |

Do not pass `model`. Pass `effort` as above unless the user gave `effort=`.

## Workflow

1. **Load.** Resolve `DIR` (`.dev-kit/<slug>/`, or the most recently modified run folder under
   `.dev-kit/` when no slug is given — say which). Read the manifest size via `TOOL check`.
   Base commit: `<DIR>/base.txt`; if missing, ask the user for the base ref.
2. **Fresh evidence.** If `<DIR>/checks/integration.md` is missing or older than the newest
   change in the tree, launch `dev-kit:dev-checker` with scope `integration`, the manifest's
   `integration_gates`, the ownership command
   `TOOL ownership <DIR>/plan.md --baseline <DIR>/baseline-dirty.txt --ignore <DIR>/`, and
   report path `<DIR>/checks/integration.md`. Reviewers judge evidence; stale evidence
   produces confident wrong verdicts.
3. **Judge.** Launch `dev-kit:dev-reviewer` with: the plan path, `DIR`, the base commit, the
   ownership command, and `<DIR>/review.md` as its output path.
4. **Relay** in at most 12 lines: the verdict, each must-fix finding as one line with
   `path:line` and its slice, then should-fix count and residual risks.
5. **Route:**
   - `approve` → done. Offer to commit (the user decides; `/commit` from commit-commands works
     well) and mention the run folder can be deleted.
   - `changes-required` → offer `/dev-kit:implement <slug> fix`, then review again. After two
     such cycles, stop and let the user decide.
   - `blocked` → the plan is wrong; offer `/dev-kit:plan` with review.md as input.

## Rules

- Do not soften or add to the reviewer's findings from your own reading; if a finding looks
  wrong to you, ask the reviewer (SendMessage) to re-verify it.
- Reviews of reviews are not free: one reviewer per cycle. For a second opinion on an L ticket,
  the user can ask for it explicitly.
