---
name: pick-model
description: Recommend the right Claude model tier (haiku/sonnet/opus) and reasoning effort (low/medium/high/xhigh/max) for a described task, set of tasks or sub-agent. Use when the user asks which model or effort to use, wants to cut agent or token costs, writes an agent's model/effort frontmatter, or describes a workflow and wants model routing advice. Also use proactively when planning a multi-agent pipeline.
---

# Model and effort advisor

Route each piece of work to the cheapest model **and** effort that does it reliably. Model sets
the ceiling of what can be understood; effort sets how long it thinks before acting. A cheap
model at high effort often beats an expensive one at low effort on well-specified work, and
loses badly on ambiguous work.

## Tiers

| Tier | Model | Strengths |
|---|---|---|
| **Junior** | `haiku` | Narrow, mechanical, well-defined: formatting, boilerplate, docstrings, classification, summarisation, extraction, simple transforms, output validation |
| **Senior** | `sonnet` | Standard engineering with clear requirements: feature slices, debugging, code generation, checks, research, refactoring, running and reading gates |
| **Principal** | `opus` | Ambiguity and judgement: decomposition and planning, architecture and trade-offs, security review, judging other agents' work, deciding what to do next |

## Effort

| Effort | Use for |
|---|---|
| `low` | lookups, formatting, single-step transforms |
| `medium` | routine work with a pattern to follow; checks and gate runs; small plans; routine progress reviews |
| `high` | new logic or tricky edge cases; plans with contracts between areas; reviews of normal changes |
| `xhigh` | cross-system plans, security- or data-sensitive reviews, final verdicts, pivot decisions |
| `max` | rare: a hard problem where a wrong answer is very costly and time does not matter |

## Default routing in this marketplace

Execution and checking go to Sonnet; planning, review and judging go to Opus.

| Role | Model | Effort |
|---|---|---|
| scout / map context | sonnet | medium (high for large tickets) |
| implement a slice / run a lane | sonnet | medium or high, set by the planner per slice |
| check: gates, ownership, contract drift, metrics | sonnet | medium |
| investigate a bug | sonnet | high (escalate to opus medium when confidence is low) |
| plan | opus | S medium · M high · L xhigh |
| review a change | opus | S medium · M high · L or sensitive xhigh |
| judge a campaign round | opus | routine medium · failures high · final or pivot xhigh |

`dev-kit` and `campaign-kit` agents carry these defaults in their `model:` and `effort:`
frontmatter; their skills raise or lower effort per task.

## Analysis steps

1. **Split** the request into distinct sub-tasks.
2. **For each**, ask:
   - Must it resolve ambiguity, weigh trade-offs or judge someone else's work? → `opus`.
   - Is it standard work with clear inputs and a checkable result? → `sonnet`.
   - Is it narrow and mechanical? → `haiku`.
   - Then effort: is there a pattern to follow (`medium`), new logic (`high`), or a costly,
     wide-reaching decision (`xhigh`)?
3. **Escalation triggers:** ambiguity, security implications, architectural scope, no clear
   right answer, a cheaper attempt already failed.
4. **Downgrade opportunities:** anything mechanical, anything a script could do instead (then
   recommend the script, which costs no tokens).
5. When unsure between two tiers or efforts, start lower and escalate on evidence.

## Output

| Sub-task | Model | Effort | Reason |
|---|---|---|---|
| … | `haiku/sonnet/opus` | `low…xhigh` | one line |

Then:
- **Main session** model and effort if this runs as a single task.
- **Pipeline** if it benefits from sub-agents: who orchestrates, who executes, who checks, who
  judges, and what each writes to a file so the orchestrator reads summaries, not transcripts.
- **Relative cost:** low / medium / high.

Agent frontmatter for a sub-agent: `model: sonnet` and `effort: medium` (both optional; omitted
means inherit the session's).

If no task is described, ask what they are trying to accomplish.
