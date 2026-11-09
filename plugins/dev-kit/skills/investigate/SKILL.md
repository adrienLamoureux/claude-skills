---
name: investigate
description: Investigate a bug or unexplained behaviour read-only before anyone fixes it — reproduce, rank three hypotheses with path:line evidence, design the smallest experiment that separates them. Use when the user runs /dev-kit:investigate, reports a bug, regression, error, crash, flaky test or "why does X happen", or asks to look into something without changing code yet.
argument-hint: "<symptom, error, issue URL or #number> [DIR=.dev-kit/<slug>]"
effort: medium
---

# Investigate

Investigation first, fix second. Nothing in this skill edits tracked files.

`<plan-skill-dir>` is the sibling `plan` skill folder: the base directory shown when this skill loads, with `investigate` replaced by `plan`.

## Agents and effort

| Role | `subagent_type` | Model | Effort |
|---|---|---|---|
| reproduce, trace, hypothesise | `dev-kit:dev-investigator` | Sonnet (agent default) | `high` |
| escalation when confidence is low | `dev-kit:dev-investigator` with `model: opus` | Opus | `medium` |

The escalation is the only time a dev-kit skill passes `model` to the Agent tool.

## Workflow

1. **Frame.** Symptom from the argument (an issue → `gh issue view`). Slug `bug-<2-4 words>`,
   run folder `DIR` or `.dev-kit/<slug>/`. If the report lacks the one fact needed to start
   (which environment, which command), ask it in one question; otherwise go.
2. **Investigate.** Launch `dev-kit:dev-investigator` with the symptom, the repo root, `DIR`
   for scratch files, and `<DIR>/investigation.md` as output.
3. **Escalate** only when its confidence is `low` or its top two hypotheses are both `high`:
   relaunch with `model: opus`, effort `medium`, the same brief, plus "a first pass wrote
   <DIR>/investigation.md: verify or overturn it and rewrite the file". If the reply says an
   advisor already reviewed the ranking, do not relaunch: report, and offer the Opus pass as a
   next step instead.
4. **Report** in at most 10 lines: reproduced or not, the ranked hypotheses (one line each with
   the key `path:line`), the experiment, confidence.
5. **Next step**, the user's choice, as a decision card (below):
   - run the experiment (it may need a command the user must run, e.g. against prod);
   - fix it: `/dev-kit:plan` with `<DIR>/investigation.md` as the ticket. A one-file fix with
     high confidence can be planned at size S.

## Resume block and decision card

Before your first stop, read `<plan-skill-dir>/references/stop-blocks.md` and follow it: at every stop write `<DIR>/resume.md`,
and end every stop that waits for the user's choice with its five-line decision card.
Where examples for this skill: investigate · done

## Rules

- No code changes, no dependency installs, no git writes, even for an "obvious" one-line fix.
  A fix made before the cause is confirmed hides the evidence for the real one.
- Do not read the code yourself to double-check the investigator; escalate instead.
