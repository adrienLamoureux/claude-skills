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
```

| ReAct | Here |
|---|---|
| Thought | `rounds/<n>/plan.md`, written by the strategist (round 1) or the judge |
| Action | one runner per lane, `rounds/<n>/<lane>.md` |
| Observation | the checker re-measures every criterion and verifies lane claims, `rounds/<n>/check.md` |
| next Thought | the judge's verdict and next plan, `rounds/<n>/review.md` + `ledger.md` |
| Final answer | the judge's final report on a stop verdict, `outcome.md` |

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
| `campaign-runner` | sonnet | high | per action, medium or high, chosen by the judge |
| `campaign-checker` | sonnet | medium | — |
| `campaign-judge` | opus | high | `campaign_tool.py next` computes it: medium for a routine round, high after a failure or regression, xhigh for the final verdict |

Copy an agent file into `~/.claude/agents/` (same `name:`) to change its model or effort.

## Checkpoints and autonomy

Set in the interview: `checkpoint-each-round`, `checkpoint-on-pivot` (default) or `unattended`.
Regardless of autonomy, the loop always stops for: approving the brief, a `stop-blocked`
verdict, a lane that needs a human, and any change to the objective or criteria.

Guardrails default to **no outward-facing actions**: no push, deploy, publish, message, PR,
purchase or data deletion unless the brief lists it.

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

The format of every file is in `skills/campaign/references/formats.md`.
`scripts/campaign_tool.py next <dir>` reads the folder and says what to do next, so an
interrupted campaign resumes with `/campaign-kit:campaign <slug>`.

Claude Code refuses a sub-agent's Write to a `.md` file whose name starts with `report`,
`summary`, `findings` or `analysis`. That is why the final report is `outcome.md` and why
`campaign_tool.py check` rejects lane ids that start with those words. When a lane's own
deliverable needs such a name, the runner writes a draft under another name and the execute
step moves it into place.

## Evals

`evals/` holds a `claude plugin eval` suite. Run it with
`claude plugin eval plugins/campaign-kit --max-cost-usd 5`.
