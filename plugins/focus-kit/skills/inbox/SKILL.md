---
name: inbox
description: List every dev-kit and campaign-kit run that waits on you — plans to approve, verdicts to act on, blocked questions, interrupted runs — oldest first, with what each needs. Use when the user runs /focus-kit:inbox, asks what is waiting on them, what they left open, where they were or what to pick up next, or says a run is finished, committed or abandoned.
argument-hint: "[--all] [--root DIR] [page] [dismiss <run-dir>]"
effort: low
---

# Inbox

One place for what waits on the user, so they do not rebuild it from several sessions.

`TOOL` is `python3 <skill-dir>/../../scripts/focus_tool.py`, where `<skill-dir>` is the base
directory shown when this skill loads.

1. Run `TOOL inbox` with the user's arguments (`--all`, `--root DIR`). Show its output as is.
2. If any run waits, add one line: the run to take first and the command that resumes it
   (the oldest decision usually; an interrupted run if the user is about to work on it). Then
   stop; do not start the run unless the user asks.
3. `page`: the hooks already rebuild the page whenever a run stops; run `TOOL page` (with any
   `--root`) only to force it, and give the path it prints. On macOS the user opens it with
   `open <path>`.
4. When the user says a run is finished, committed or abandoned, in any words, run
   `TOOL dismiss <run-dir>` for it.
   Deleting the run folder works too; never delete it yourself.

Runs live in `.dev-kit/` and `.campaign-kit/` under the current repository and under every
folder in `FOCUS_KIT_ROOTS`. Each run's state comes from its `resume.md`, which the kits write
at every stop, or, when that is missing or older than the run's files, from the run's files.
