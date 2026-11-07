---
name: review
description: Review a dev-kit plan's implementation before it is committed — fresh gates, then an Opus reviewer judges the diff against plan.md and for correctness, security and test gaps, and gives an approve, changes-required or blocked verdict. Use when the user runs /dev-kit:review, or asks to review, judge or sign off the work of a dev-kit plan. For a diff or PR with no dev-kit plan, /code-review fits better.
argument-hint: "<slug | run folder> [effort=medium|high|xhigh]"
effort: medium
---

# Review

Step 3 of the developer family: **plan → implement → review**. A judge that did not write the
code reads it against the plan. You relay the verdict and route what happens next.

`TOOL` means `python3 <plan-skill-dir>/scripts/plan_tool.py`, where `<plan-skill-dir>` is the
base directory shown when this skill loads with `review` replaced by `plan`.

## Shell commands

Headless runs match each part of a chained command against the Bash allow-list separately. So
run one plain command per Bash call from the repo root (no `&&`, `||`, `;`, pipes or `$(...)`),
run `TOOL` by the path above, and look at files with Read, Grep and Glob, not `ls`, `cat` or
`find`. A denial means that one command matched no rule: retry it plainly or with Read, Grep or
Glob. Stop only if a plain `TOOL` call is denied, and name the rule it needs.

## Agents and effort

| Role | `subagent_type` | Effort |
|---|---|---|
| fresh gate evidence (Sonnet) | `dev-kit:dev-checker` | `medium` |
| judge the change (Opus) | `dev-kit:dev-reviewer` | S `medium` · M `high` · L `xhigh`; also `xhigh` when the diff touches auth, payments, migrations or secrets handling |

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
4. **Recap.** The reviewer's reply ends with a recap block: `# Recap — <slug>`, then at most
   eight lines (ticket and size · verdict; slices done · gates passed or failed, naming the
   failures; files changed, count then first paths; up to three must-fix as `path:line`,
   problem, slice; the next step). Check it against `TOOL check` (slices),
   `<DIR>/checks/integration.md` (gates) and the ownership command's `by_slice` (files), and
   correct anything that disagrees; with no block, build it from those and `review.md`. Write
   it yourself, not through an agent, to `<DIR>/recap.md` (each cycle replaces it), and show it
   as your relay, plus one line with the should-fix count and residual risks if any.
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
