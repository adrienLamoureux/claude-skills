---
name: investigate
description: Investigate a bug or unexplained behaviour read-only before anyone fixes it — reproduce, rank three hypotheses with path:line evidence, design the smallest experiment that separates them. Use when the user runs /dev-kit:investigate, reports a bug, regression, error, crash, flaky test or "why does X happen", or asks to look into something without changing code yet.
argument-hint: "<symptom, error, issue URL or #number> [DIR=.dev-kit/<slug>]"
effort: medium
---

# Investigate

Investigation first, fix second. Nothing in this skill edits tracked files.

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

## Resume block

At every stop (done, waiting for the user, or blocked), write `<DIR>/resume.md` yourself,
replacing the old one, so a later session and the focus-kit inbox know where the run stands:

```
# Resume — <slug>
- Where: <step, e.g. investigate · done>
- Did: <one line: what this turn finished>
- Needs: <what the user must do or decide, or nothing>
```

Show it only when the stop has no decision card; the card already says what is needed.

## Decision card

Every stop that waits for the user's choice ends with these five lines, then the question.
One decision per card; a progress note that needs no answer gets no card.

```
Decide: <the choice, in one line>
Recommend: <option> — <one reason>
If wrong: <what breaks and when it would show; name the top unverified risk>
Undo cost: <none, nothing written yet | revert the branch | re-run round n | one-way: why>
On "ok": <exactly what happens next if the user just says ok>
```

The undo cost tells the user where to spend attention: a cheap undo needs a glance, a one-way
step needs a read. Never hide a risk to make the card shorter.

## Rules

- No code changes, no dependency installs, no git writes, even for an "obvious" one-line fix.
  A fix made before the cause is confirmed hides the evidence for the real one.
- Do not read the code yourself to double-check the investigator; escalate instead.
