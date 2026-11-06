---
name: plan
description: Plan a software ticket for plan-and-execute delivery — a Sonnet scout maps the repo, an Opus planner writes plan.md with frozen contracts, slices owned by path, gates read from the repo, merge order and risks — then stop for the user's approval. Use when the user runs /dev-kit:plan, or asks to plan, break down, slice or scope a ticket, feature, issue or change before implementing it, especially one touching several areas. Not for open-ended goals measured over many rounds (use campaign-kit) or for unexplained bugs (use /dev-kit:investigate first).
argument-hint: "<ticket text | file | issue URL or #number> [size=S|M|L] [DIR=.dev-kit/<slug>]"
---

# Plan

Step 1 of the developer family: **plan → implement → review**. You orchestrate; cheaper agents
read and write. Your own context should hold the ticket, a few agent replies and the plan
summary, never the repository.

`<skill-dir>` is the base directory shown when this skill loads.

## Shell commands

Headless runs (`claude -p --permission-mode dontAsk`) approve Bash from an allow-list, and each
part of a chained command must match a rule on its own. Run one plain command per Bash call,
from the repo root, with no `&&`, `||`, `;`, pipes or `$(...)`, and run `plan_tool.py` with
the `<skill-dir>` path. Look at files with Read, Grep and Glob, not `ls`, `cat` or `find`. A
denied call means that one command matched no rule, not that Bash is off: retry the step as a
plain command or with Read, Grep or Glob. Stop only when a plain `plan_tool.py` call is denied
too, and name the allow-list rule it needs.

## Agents and effort

Launch each with the Agent tool, `subagent_type` as below. Do not pass `model`: the agent file
sets it. Pass `effort` exactly as this table says for the ticket size.

| Role | `subagent_type` | Model | S | M | L |
|---|---|---|---|---|---|
| map the repo | `dev-kit:dev-scout` | Sonnet | medium | medium | high |
| write the plan | `dev-kit:dev-planner` | Opus | medium | high | xhigh |

## Workflow

1. **Frame** (no agents yet).
   - Get the ticket: text as given; a path → read it; an issue URL or `#n` → `gh issue view`.
   - Derive a kebab-case `slug` (2-5 words). Run folder: `DIR` if given, else
     `.dev-kit/<slug>/` at the repo root.
   - Size it S / M / L (see `references/plan-format.md`, "Sizing") unless `size=` was given;
     one line of reason. More than ~8 slices or success measured over rounds → suggest
     `/campaign-kit:campaign` instead and stop unless the user insists.
   - If the ticket is ambiguous in a way that would change the slicing (which system, which
     behaviour), ask up to three questions in one AskUserQuestion call. Otherwise go on; the
     planner records assumptions as risks.
   - Say the frame in one line: slug, size, folder.
2. **Scout.** Launch `dev-kit:dev-scout` with the ticket, the repo root and
   `<DIR>/context.md` as its output path.
3. **Plan.** Launch `dev-kit:dev-planner` with: the ticket text, `<DIR>/context.md`, the size,
   `<skill-dir>/references/plan-format.md`, the checker command
   `python3 <skill-dir>/scripts/plan_tool.py check <DIR>/plan.md`, and `<DIR>/plan.md` as its
   output path.
4. **Check.** Run `python3 <skill-dir>/scripts/plan_tool.py check <DIR>/plan.md` yourself. On
   errors, send them back to the same planner (SendMessage) once; if they persist, show them
   to the user.
5. **Present** in at most 15 lines: problem in one sentence, frozen contracts by name, slices
   by wave (id, owns, effort), integration gates, top risks and open questions with their
   assumed defaults. Then ask for approval, edits, or a different size.
6. **On approval**, run `python3 <skill-dir>/scripts/plan_tool.py approve <DIR>/plan.md` and
   tell the user the next step: `/dev-kit:implement <slug>`. On requested edits, send them to
   the planner (SendMessage if it is still addressable, else a new launch with the current
   plan as input) and repeat steps 4-5.

## Rules

- Never edit source code in this skill. Planning that drifts into coding skips the approval
  gate, which is the point of plan-and-execute.
- Do not read source files to second-guess the planner; if the plan looks wrong, say what and
  send it back. Re-reading the repo yourself spends the tokens the agents were meant to save.
- The run folder is working state. Do not commit it; leave version control to the user and
  mention once that `.dev-kit/` can go in `.gitignore`.

## Bundled files

- `references/plan-format.md` — the plan.md sections, the `json plan-manifest` block, sizing.
  The planner reads it; you need it only to size the ticket.
- `scripts/plan_tool.py` — `check` (structure, manifest, path overlap between parallel slices,
  waves), `approve`, and `branch`, `baseline` and `ownership` (used by implement and review).
