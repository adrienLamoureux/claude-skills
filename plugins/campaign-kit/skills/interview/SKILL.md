---
name: interview
description: Start a campaign-kit campaign — interview the user (done criteria, lanes, guardrails, budget, autonomy), have an Opus strategist write brief.md and the round 1 plan, measure baselines, then stop for approval. Use when the user runs /campaign-kit:interview, or wants to scope, set up or define a campaign before running it.
argument-hint: "<objective in a sentence> [DIR=.campaign-kit/<slug>]"
effort: medium
---

# Interview

Step 1 of the campaign family: **interview → execute lanes → review and iterate**. The quality
of every later round depends on criteria a checker can measure the same way twice. Spend the
user's attention here, not later.

`<campaign-skill-dir>` is the base directory shown when this skill loads with `interview`
replaced by `campaign`. `TOOL` is `python3 <campaign-skill-dir>/scripts/campaign_tool.py`;
`FORMATS` is `<campaign-skill-dir>/references/formats.md`.

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
| write brief + round 1 (Opus) | `campaign-kit:campaign-strategist` | `medium` for 1-2 lanes and a clear metric · `high` default · `xhigh` when the objective spans several systems or the interview left open questions |
| measure baselines (Sonnet) | `campaign-kit:campaign-checker` | `medium` |

Do not pass `model`.

## Workflow

1. **Frame.** Slug from the objective (kebab-case, 2-4 words); run folder `DIR` or
   `.campaign-kit/<slug>/`. If `brief.md` already exists there, run `TOOL next <DIR>` and
   continue from the step it names instead of re-interviewing.
2. **Look before asking** (cheap, yourself): is this a repo, what test or build commands
   exist, is there an existing metric. One or two commands, not a survey. Questions the
   environment answers are not worth the user's time.
3. **Interview** with AskUserQuestion, at most two calls of up to four questions each. Cover,
   offering concrete options with your recommended one first:
   - **Done:** how will we know it worked? Turn adjectives into numbers ("faster" → p95 below
     what?). One guard metric that must not get worse.
   - **Lanes:** which independent workstreams; anything off-limits.
   - **Guardrails:** outward-facing actions allowed (default: none — no push, deploy, publish,
     send, purchase or delete); paths or systems not to touch.
   - **Budget and autonomy:** max rounds (default 5), actions per round (default 3), and
     checkpoints: every round, only on pivots (default), or unattended.
   Write the answers to `<DIR>/interview.md`, the user's own words where they set a rule.
4. **Brief.** Launch `campaign-kit:campaign-strategist` with: `<DIR>/interview.md`, `FORMATS`,
   `DIR`, "write brief.md and rounds/1/plan.md", and the check command `TOOL check <DIR>`.
5. **Baseline.** Launch `campaign-kit:campaign-checker` in `baseline` mode with `DIR`. A
   criterion that comes back `unmeasurable` goes to the user now: fix its check, drop it, or
   accept it as judged qualitatively.
6. **Present** in at most 15 lines: the brief's `## In plain words` lines, objective, each criterion as `baseline → target`, lanes,
   guardrails, budget and autonomy, round-1 actions, assumptions. End with a decision card
   (below): approve or edit; its undo cost is nothing run yet.
7. **On approval:** `TOOL approve <DIR> brief` and `TOOL approve <DIR> round 1`. Next step:
   `/campaign-kit:campaign <slug>` (runs the loop) or `/campaign-kit:execute <slug>` (one
   round at a time). With autonomy `unattended`, also give the user this line, which keeps the
   loop going across turns (a skill cannot set a goal itself): `/goal Run
   /campaign-kit:campaign <slug> until a "campaign <slug>:"
   status line says done, waiting for you, or blocked.`
   Edits go back to the strategist (SendMessage), then repeat 6.

## Resume block

At every stop (done, waiting for the user, or blocked), write `<DIR>/resume.md` yourself,
replacing the old one, so a later session and the focus-kit inbox know where the run stands:

```
# Resume — <slug>
- Where: <step, e.g. brief · ready, round 2 · plan ready, round 3 · stop-blocked, done>
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

- Never start lane work during the interview. The approval gate is where the user sets the
  guardrails that make unattended rounds safe.
- Do not write the brief yourself; the strategist is cheaper at it than your context is.
- The run folder is working state: do not commit it; mention once that `.campaign-kit/` can go
  in `.gitignore`.
