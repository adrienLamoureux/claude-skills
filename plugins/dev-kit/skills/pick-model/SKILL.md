---
name: pick-model
description: Recommend the Claude model tier (haiku/sonnet/opus), reasoning effort (low…max) and advisor setup for a described task, set of tasks or sub-agent. Use when the user asks which model or effort to use, wants to cut agent or token costs, writes an agent's model/effort frontmatter, or wants model routing advice for a workflow. Also use proactively when planning a multi-agent pipeline.
---

# Model and effort advisor

Route each piece of work to the cheapest model **and** effort that does it reliably. Model sets
the ceiling of what can be understood; effort sets how long it thinks before acting. A cheap
model at high effort often beats an expensive one at low effort on well-specified work, and
loses badly on ambiguous work.

## Tiers

| Model | Strengths |
|---|---|
| `haiku` | narrow, mechanical, well-defined: formatting, boilerplate, docstrings, classification, summarisation, extraction, output validation |
| `sonnet` | standard engineering with clear requirements: feature slices, debugging, code generation, checks, research, refactoring, running and reading gates |
| `opus` | ambiguity and judgement: planning, architecture and trade-offs, security review, judging other agents' work, deciding what to do next |

## Effort

| Effort | Use for |
|---|---|
| `low` | lookups, formatting, single-step transforms |
| `medium` | routine work with a pattern to follow; checks and gate runs; small plans; orchestration that only dispatches agents and relays their replies |
| `high` | new logic or tricky edge cases; plans with contracts between areas; reviews of normal changes |
| `xhigh` | cross-system plans, security- or data-sensitive reviews, final verdicts, pivot decisions |
| `max` | rare: a hard problem where a wrong answer is very costly and time does not matter |

## Advisor and goal

- **Advisor** (`/advisor opus`, `--advisor opus`, `"advisorModel"` in settings): the working
  model consults a stronger one at the decisions that matter. Sonnet plus an Opus advisor is
  the cheaper alternative to Opus throughout on long, mostly routine tasks. It is session-wide
  (every subagent inherits it, Opus ones too; no per-agent field, no call cap), each call
  re-reads the whole transcript uncached at the advisor's rates, and it needs the Anthropic
  API. Suggest it for Sonnet sessions or all-Sonnet pipelines, with prompts that cap the calls.
- **Goal** (`/goal <condition>`, set by the user only): Claude keeps taking turns until a small
  fast model judges the condition met from the transcript. For one checkable condition a single
  session can reach, it beats a multi-agent loop. Make the condition visible in Claude's output
  (a test result, a verdict line) and bound it ("or stop after 20 turns").

## Default routing in this marketplace

Execution and checking go to Sonnet; planning, review and judging go to Opus.

| Role | Model | Effort |
|---|---|---|
| orchestrate (main session) | session model | medium, set by the skill |
| scout / map context | sonnet | medium (high for large tickets) |
| implement a slice / run a lane | sonnet (a lane: opus once after a failure, set by the judge) | medium or high, set by the planner or judge |
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
4. **Downgrade opportunities:** anything mechanical; anything a script could do instead (then
   recommend the script, which costs no tokens); Opus throughout where Sonnet plus an Opus
   advisor would do.
5. When unsure between two tiers or efforts, start lower and escalate on evidence.

## Output

| Sub-task | Model | Effort | Reason |
|---|---|---|---|
| … | `haiku/sonnet/opus` | `low…xhigh` | one line |

Then:
- **Main session** model and effort if this runs as a single task, and whether an advisor or a
  `/goal` fits.
- **Pipeline** if it benefits from sub-agents: who orchestrates, who executes, who checks, who
  judges, and what each writes to a file so the orchestrator reads summaries, not transcripts.
- **Relative cost:** low / medium / high.

Agent frontmatter: `model: sonnet` and `effort: medium` (omitted means inherit the session's).
A skill's `effort:` applies to its turn; avoid a skill-level `model:`, which makes that turn
re-read the whole conversation uncached.

If no task is described, ask what they are trying to accomplish.
