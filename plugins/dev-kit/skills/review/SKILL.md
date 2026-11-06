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

## Shell commands

Headless runs (`claude -p --permission-mode dontAsk`) approve Bash from an allow-list, and each
part of a chained command must match a rule on its own. Run one plain command per Bash call,
from the repo root, with no `&&`, `||`, `;`, pipes or `$(...)`, and run `TOOL` with the path
given above. Look at files with Read, Grep and Glob, not `ls`, `cat` or `find`. A denied call
means that one command matched no rule, not that Bash is off: retry the step as a plain command
or with Read, Grep or Glob. Stop only when a plain `TOOL` call is denied too, and name the
allow-list rule it needs.

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
4. **Recap.** The reviewer's reply ends with a recap block (format below). Check it against
   `TOOL check` (slices), `<DIR>/checks/integration.md` (gates) and the ownership command's
   `by_slice` (files changed), and correct anything that disagrees; if the reply has no block,
   build it from those and `review.md`. Write it yourself, not through an agent, to
   `<DIR>/recap.md` (each review cycle replaces it), and show it as your relay, plus one line
   with the should-fix count and residual risks if there are any.
5. **Route:**
   - `approve` → done. Offer to commit (the user decides; `/commit` from commit-commands works
     well) and mention the run folder can be deleted.
   - `changes-required` → offer `/dev-kit:implement <slug> fix`, then review again. After two
     such cycles, stop and let the user decide.
   - `blocked` → the plan is wrong; offer `/dev-kit:plan` with review.md as input.

## Recap format

A brief résumé of at most eight lines after the heading: ticket and size with the verdict;
slices done and gates passed or failed (name the failing ones); files changed (count, then the
first few paths); each must-fix finding as `path:line`, what is wrong, and its slice (more than
three → the top three and "N more in review.md"; none → drop the line); the next step, which
is commit on `approve`, `/dev-kit:implement <slug> fix` on `changes-required`, or
`/dev-kit:plan` on `blocked`.

```markdown
# Recap — login-rate-limit
- Ticket: Per-user rate limit on POST /login (M) · verdict: changes-required
- Slices: 3 of 3 done · gates: 4 passed, 1 failed (`npm --prefix backend test -- auth`)
- Changed: 6 files: backend/lib/rate-limit.js, backend/routes/auth.js, web/src/Login.tsx, …
- Must fix: `backend/routes/auth.js:41` limiter keyed by IP, not user id (backend-route)
- Next: `/dev-kit:implement login-rate-limit fix`, then `/dev-kit:review login-rate-limit`
```

## Rules

- Do not soften or add to the reviewer's findings from your own reading; if a finding looks
  wrong to you, ask the reviewer (SendMessage) to re-verify it.
- Reviews of reviews are not free: one reviewer per cycle. For a second opinion on an L ticket,
  the user can ask for it explicitly.
