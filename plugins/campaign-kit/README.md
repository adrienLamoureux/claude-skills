# campaign-kit

The **campaign family**: a ReAct loop for objectives that cannot be fully planned up front —
raise coverage to 80%, cut p95 latency, migrate 300 call sites, clear a backlog, research and
prototype options. Each round reasons about what the last one observed, acts in parallel lanes,
and measures again.

```
/campaign-kit:campaign <objective>     the whole loop, resumable
  /campaign-kit:interview               you answer ≤ 8 questions → strategist (Opus) writes brief.md + round 1
                                         → checker (Sonnet) measures baselines → you approve
  /campaign-kit:execute                 runners (Sonnet) act on every lane in parallel → checker (Sonnet) observes
  /campaign-kit:review                  judge (Opus) → continue | pivot | stop-done | stop-blocked | stop-budget
                                         → writes the next round's plan, or outcome.md
                                         → when it ends: a brief résumé, recap.md
```

| ReAct | Here |
|---|---|
| Thought | `rounds/<n>/plan.md`, written by the strategist (round 1) or the judge |
| Action | one runner per lane, `rounds/<n>/<lane>.md` |
| Observation | the checker re-measures every criterion and verifies lane claims, `rounds/<n>/check.md` |
| next Thought | the judge's verdict and next plan, `rounds/<n>/review.md` + `ledger.md` |
| Final answer | the judge's final report on a stop verdict, `outcome.md`, and its brief résumé, `recap.md` |

## Install

```bash
claude plugin marketplace add adrienLamoureux/claude-skills
claude plugin install campaign-kit@adrien-skills
```

On Claude Code 2.1.275 or later, one step: `/plugin install campaign-kit --marketplace adrienLamoureux/claude-skills`.

## Agents

| Agent | Model | Default effort | Set per call |
|---|---|---|---|
| `campaign-strategist` | opus | high | medium for small, xhigh for multi-system objectives |
| `campaign-runner` | sonnet (opus for one action after a lane fails, chosen by the judge) | high | per action, medium or high, chosen by the judge |
| `campaign-checker` | sonnet | medium | — |
| `campaign-judge` | opus | high | `campaign_tool.py next` computes it: medium for a routine round, high after a failure or regression, xhigh for the final verdict |

Copy an agent file into `~/.claude/agents/` (same `name:`) to change its model or effort. The
skills run their own turn at `effort: medium`; the checker starts without `CLAUDE.md`
(`omitClaudeMd: true`) and carries its manifest format inline, so it does not read
`formats.md` each round.

## Checkpoints and autonomy

Set in the interview: `checkpoint-each-round`, `checkpoint-on-pivot` (default) or `unattended`.
Regardless of autonomy, the loop always stops for: approving the brief, a `stop-blocked`
verdict, a lane that needs a human, and any change to the objective or criteria.

Guardrails default to **no outward-facing actions**: no push, deploy, publish, message, PR,
purchase or data deletion unless the brief lists it.

## Run it unattended: the `/goal` launcher

The judge decides when a campaign is done; `/goal` only makes sure the session keeps taking
turns until it gets there. After every step the loop prints a status line from
`campaign_tool.py next`, for example `campaign coverage-80: running — next review, round 2`,
`campaign coverage-80: waiting for you — approve-round, round 3` or
`campaign coverage-80: done — stop-done, round 4`; when it stops on something it cannot clear,
it prints `campaign coverage-80: blocked — <what would clear it>`.

1. Run the interview and approve the brief (`/campaign-kit:interview` or
   `/campaign-kit:campaign <objective>`), with autonomy `unattended` or `checkpoint-on-pivot`.
2. Send the launcher. It ends on the first status line that needs you:

   ```
   /goal Run /campaign-kit:campaign <slug> until a "campaign <slug>:" status line says done, waiting for you, or blocked.
   ```

3. Headless, the same line is the prompt:

   ```bash
   claude -p '/goal Run /campaign-kit:campaign <slug> until a "campaign <slug>:" status line says done, waiting for you, or blocked.' \
     --plugin-dir /path/to/campaign-kit --model sonnet --permission-mode dontAsk \
     --allowedTools "<see Headless runs>" --max-budget-usd 10
   ```

A blocked step stays blocked under a goal: the orchestrator never measures criteria or
approves rounds itself to get past one. For one checkable condition a single session can
reach, skip the campaign: a plain `/goal <condition>` is cheaper.

## Escalation and the advisor

- **The judge's Opus escalation** (built in): when the checker marks a lane `fail` or
  `partial`, the judge first writes a sharper task on Sonnet; when the lane fails again after
  that, or the cause is clearly reasoning, it puts the lane's next action on Opus
  (`"model": "opus"` in the round manifest). `campaign_tool.py check` allows it
  only right after such a round and not twice in a row for the same lane, so the extra cost is
  bounded and visible in the plan.
- **The advisor** (optional, `/advisor opus`): runners consult it once, before a second
  attempt at something that failed; the strategist and judge at most once. It is session-wide
  and each call re-reads the transcript at Opus rates, so turn it on for campaigns with long,
  failure-prone lanes and leave it off otherwise.

Trial results for both are in `prototypes/campaign-kit-trial/RESULTS.md` at the repo root.

## Headless runs

Under `claude -p --permission-mode dontAsk`, each part of a chained shell command must match an
allow-list rule on its own. So every campaign-kit skill and agent runs one plain command per
Bash call (no `&&`, `;`, pipes, `cd`, `git -C` or shell variables), runs `campaign_tool.py` by
its full path, and treats a denial as one unmatched command, not as Bash being off. The
orchestrator passes the run folder to agents as an absolute path. A starting allow-list is
`TOOLS` in `prototypes/campaign-kit-trial/trial.py`: read tools, `Agent`, `Skill`, writes to the
lanes' paths and `.campaign-kit/**`, `campaign_tool.py`, the criteria's check commands and the
read-only git commands.

## Run folder

`.campaign-kit/<slug>/` (add it to `.gitignore`):

| File | Written by |
|---|---|
| `interview.md` | the orchestrator, from your answers |
| `brief.md` | strategist (baselines added by the checker; `approved` flipped on your yes) |
| `rounds/<n>/plan.md` | strategist for round 1, judge after |
| `rounds/<n>/<lane>.md` | runners |
| `rounds/<n>/check.md` | checker |
| `rounds/<n>/review.md`, `ledger.md` | judge |
| `outcome.md` | judge, on a stop verdict (`report.md` in runs from before 0.2.0, still read) |
| `recap.md` | the main session, when the campaign ends: a brief résumé of at most 8 lines (outcome and rounds used, criteria baseline → final, deliverables, measured cost, open items, your to-dos) |

The format of every file is in `skills/campaign/references/formats.md`.
`scripts/campaign_tool.py next <dir>` reads the folder and says what to do next, so an
interrupted campaign resumes with `/campaign-kit:campaign <slug>`.

Claude Code refuses a sub-agent's Write to a `.md` file whose name starts with `report`,
`summary`, `findings` or `analysis`. That is why the final report is `outcome.md`, the résumé
is `recap.md` rather than `summary.md`, and `campaign_tool.py check` rejects lane ids that
start with those words. When a lane's own deliverable needs such a name, the runner writes a
draft under another name and the execute step moves it into place.

## Evals

`evals/` holds a `claude plugin eval` suite. Run it with
`claude plugin eval plugins/campaign-kit --max-cost-usd 5`.
