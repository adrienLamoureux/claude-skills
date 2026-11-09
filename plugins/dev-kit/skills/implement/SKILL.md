---
name: implement
description: Execute an approved dev-kit plan.md — workers implement its slices wave by wave inside their owned paths, a checker gates each wave, then hand off to review. Also applies a dev-kit review's must-fix findings. Use when the user runs /dev-kit:implement, or says to implement, build or carry out a dev-kit plan, or to fix what the dev-kit review found.
argument-hint: "<slug | plan.md path> [MAX_PARALLEL=3] [branch=<name>] [fix]"
effort: medium
---

# Implement

Step 2 of the developer family: **plan → implement → review**. You orchestrate waves of workers
and read only their short replies and the checker's verdicts.

`<plan-skill-dir>` is the sibling `plan` skill folder: the base directory shown when this skill
loads, with `implement` replaced by `plan`. `TOOL` below means
`python3 <plan-skill-dir>/scripts/plan_tool.py`.

## Shell commands

Headless runs match each part of a chained command against the Bash allow-list separately. So
run one plain command per Bash call from the repo root (no `&&`, `||`, `;`, pipes or `$(...)`),
run `TOOL` by the path above, and look at files with Read, Grep and Glob, not `ls`, `cat` or
`find`. A denial means that one command matched no rule: retry it plainly or with Read, Grep or
Glob. Stop only if a plain `TOOL` call is denied, and name the rule it needs.

## Agents and effort

Launch with the Agent tool. Do not pass `model`. Pass `effort` as stated.

| Role | `subagent_type` | Effort |
|---|---|---|
| implement one slice (Sonnet) | `dev-kit:dev-implementer` | the slice's `effort` from the manifest (`medium` or `high`) |
| gates, ownership, drift (Sonnet) | `dev-kit:dev-checker` | `medium` |

## Workflow

1. **Load.** Resolve the run folder `DIR` from the slug (`.dev-kit/<slug>/`) or the plan path.
   Run `TOOL check <DIR>/plan.md`. Errors → stop and send the user to `/dev-kit:plan`.
   `approved: false` → show the plan summary and ask for approval first; on yes, `TOOL approve`.
2. **Preflight**, before the first wave, every run (including headless and fix runs):
   - **Branch.** Run `TOOL branch <DIR>/plan.md` (add `--name <name>` when the user gave
     `branch=<name>`). On the default branch or a detached HEAD it creates and switches to
     `dev-kit/<slug>`, or switches to it if it exists; on any other branch it stays. Skip it
     only when the user said in words to stay on the current branch. `ok: false` → stop and
     show the user its errors. Say the branch in one line. It never pushes, and neither do you.
   - `TOOL baseline <DIR>/plan.md <DIR>` records the base commit and the files already dirty,
     on the first run only, so pre-existing edits are never blamed on a slice. If it reports
     `dirty_under_owned_paths`, ask the user with a decision card before going on: a worker
     would overwrite those edits (a one-way step for uncommitted work). The run folder may live outside the repository; run `TOOL` from the repository
     root either way.
   - `OWN` below means `TOOL ownership <DIR>/plan.md --baseline <DIR>/baseline-dirty.txt
     --ignore <DIR>/`, and `SIZE` means `TOOL size <DIR>/plan.md <DIR>`.
3. **Waves.** For each wave from `check`, in order, in batches of at most `MAX_PARALLEL`
   (default 3):
   - Launch one `dev-kit:dev-implementer` per slice, all in the same message so they run in
     parallel. Brief: plan path, slice id, report path `<DIR>/slices/<id>.md`.
   - When all have replied, launch one `dev-kit:dev-checker` with scope = the slices of the
     wave, their gates, the `OWN` and `SIZE` commands, and report path `<DIR>/checks/wave-<n>.md`.
   - **Fail →** relaunch the implementer of each failing slice with the checker's failure
     lines for that slice (fix mode), then re-check. At most two fix rounds per wave; then
     stop and report with a decision card. A blocker that needs another slice's paths or a
     contract change → stop with a decision card: the plan must change (`/dev-kit:plan`).
4. **Integrate.** After the last wave, launch `dev-kit:dev-checker` with scope `integration`,
   the manifest's `integration_gates`, the `OWN` and `SIZE` commands, and
   `<DIR>/checks/integration.md`.
   Failures get the same fix loop, attributed by the checker.
5. **Report** in at most 12 lines: regressions and failing gates first, then slices done,
   files changed count, anything unverified. Next step: `/dev-kit:review <slug>`.

## Fix mode (after a review)

When the argument says `fix`, or `<DIR>/review.md` has verdict `changes-required` newer than
the last implement run: group its Must-fix findings by the slice id each is tagged with, launch
one implementer per affected slice with the findings as its brief (effort `high`), then step 4.
A `blocked` verdict goes back to `/dev-kit:plan`, not here. After two review → fix cycles on
the same plan, stop and hand the decision to the user with a decision card.

## Resume block and decision card

Before your first stop, read `<plan-skill-dir>/references/stop-blocks.md` and follow it: at every stop write `<DIR>/resume.md`,
and end every stop that waits for the user's choice with its five-line decision card.
Where examples for this skill: plan · ready, implement · blocked, review · approve

## Rules

- You do not edit source files yourself; workers do. If you catch yourself reading source to
  debug a failure, launch a worker or the checker with the question instead.
- Never commit, push or open a PR here. When review approves, the user decides (they may use
  `/commit`). Creating the local working branch in step 2 is the only version-control change
  this skill makes.
- Parallel workers share one working tree. That is safe only because `check` proved their
  `owns` are disjoint; never launch two slices of different waves at once.
