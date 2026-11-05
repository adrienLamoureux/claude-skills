# dev-kit

The **developer family**: plan-and-execute delivery of a well-defined ticket. The plan is
frozen and approved before any code is written; cheaper agents then execute it, and an
independent judge reviews the result against it.

```
/dev-kit:plan <ticket>        scout (Sonnet) → planner (Opus) → plan.md → you approve
/dev-kit:implement <slug>     waves of implementers (Sonnet) → checker (Sonnet) per wave → integration gates
/dev-kit:review <slug>        fresh gates (Sonnet) → reviewer (Opus) → approve | changes-required | blocked
                              changes-required → /dev-kit:implement <slug> fix → review again

/dev-kit:investigate <bug>    read-only: reproduce, 3 ranked hypotheses, smallest experiment
/dev-kit:pick-model <task>    model + effort routing advice
```

## Install

```bash
claude plugin marketplace add adrienLamoureux/claude-skills
claude plugin install dev-kit@adrien-skills
```

On Claude Code 2.1.275 or later, one step: `/plugin install dev-kit --marketplace adrienLamoureux/claude-skills`.

## Agents

| Agent | Model | Default effort | Raised / lowered by the skill |
|---|---|---|---|
| `dev-scout` | sonnet | medium | high for L tickets |
| `dev-planner` | opus | high | S medium · L xhigh |
| `dev-implementer` | sonnet | high | per slice: the planner sets medium or high |
| `dev-checker` | sonnet | medium | — |
| `dev-reviewer` | opus | high | S medium · L or sensitive diff xhigh |
| `dev-investigator` | sonnet | high | escalates to opus medium on low confidence |

The main session only orchestrates: it reads agents' short replies and the plan summary, never
the repository. Agents write their detail to files in the run folder.

To change an agent's model or effort, copy its file from `agents/` into `~/.claude/agents/`,
keep its `name:` line, and edit `model:` / `effort:`; your copy takes precedence.

## Run folder

`.dev-kit/<slug>/` at the repo root (add it to `.gitignore`):

| File | Written by |
|---|---|
| `context.md` | scout |
| `plan.md` | planner (with a `json plan-manifest` block; `approved` flipped on your yes) |
| `base.txt`, `baseline-dirty.txt` | implement, first run only |
| `slices/<id>.md` | implementers |
| `checks/wave-<n>.md`, `checks/integration.md` | checker |
| `review.md` | reviewer |
| `investigation.md` | investigator |

## Gates

Read from the repo, never hard-coded: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, CI
workflows, package scripts, `Makefile`. A repo that states its gates in `AGENTS.md` or
`CLAUDE.md` gets the most reliable plans.

## Safety

- Parallel implementers share one working tree; `plan_tool.py check` refuses plans whose
  parallel slices could touch the same paths.
- Nothing in the family commits, pushes or opens a PR. After an `approve`, you decide.
- `investigate` never edits tracked files.

## Evals

`evals/` holds a `claude plugin eval` suite (trigger and outcome checks). Run it with
`claude plugin eval plugins/dev-kit --max-cost-usd 5`.
