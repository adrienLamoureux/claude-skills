# dev-kit

The **developer family**: plan-and-execute delivery of a well-defined ticket. The plan is
frozen and approved before any code is written; cheaper agents then execute it, and an
independent judge reviews the result against it.

```
/dev-kit:plan <ticket>        scout (Sonnet) → planner (Opus) → plan.md → you approve
/dev-kit:implement <slug>     working branch → waves of implementers (Sonnet) → checker (Sonnet) per wave
                              → integration gates
/dev-kit:review <slug>        fresh gates (Sonnet) → reviewer (Opus) → approve | changes-required | blocked → recap.md
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

The skills run their own turn at `effort: medium`. `dev-checker` and `dev-scout` start without
`CLAUDE.md` (`omitClaudeMd: true`): the checker runs the gates it is given, and the scout reads
`CLAUDE.md` as a file and records its rules in `context.md`.

## Unattended runs and the advisor

After you approve a plan, one `/goal` runs implement → review → fix without you:

```
/goal Run /dev-kit:implement <slug>, then /dev-kit:review <slug>; on changes-required run /dev-kit:implement <slug> fix and review again. Done when a review shows verdict approve or blocked, after two fix cycles, or when dev-kit stops on a blocker or a question for me.
```

With an advisor set (`/advisor opus`), the implementer consults it once before its second
attempt at a failing gate, the investigator once before settling a low-confidence ranking (then
`investigate` does not relaunch on Opus), and the planner and reviewer at most once. See
"With `/goal` and `/advisor`" in the repo README for the costs.

## Run folder

`.dev-kit/<slug>/` at the repo root (add it to `.gitignore`), or the folder given as `DIR=`,
which may also be outside the repository (a CI artifacts folder, say):

| File | Written by |
|---|---|
| `context.md` | scout |
| `plan.md` | planner (with a `json plan-manifest` block; `approved` flipped on your yes) |
| `base.txt`, `baseline-dirty.txt` | implement, first run only (`plan_tool.py baseline`) |
| `slices/<id>.md` | implementers |
| `checks/wave-<n>.md`, `checks/integration.md` | checker |
| `review.md` | reviewer |
| `recap.md` | the main session, from the reviewer's closing recap: a brief résumé of at most 8 lines (ticket and verdict, slices and gates, files changed, must-fix items, next step) |
| `investigation.md` | investigator |

Claude Code refuses a sub-agent's Write to a `.md` file whose name starts with `report`,
`summary`, `findings` or `analysis`, so no file above is named that way, and
`plan_tool.py check` rejects slice ids that start with those words.

## Gates

Read from the repo, never hard-coded: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, CI
workflows, package scripts, `Makefile`. A repo that states its gates in `AGENTS.md` or
`CLAUDE.md` gets the most reliable plans.

## Safety

- Parallel implementers share one working tree; `plan_tool.py check` refuses plans whose
  parallel slices could touch the same paths.
- On the default branch (or a detached HEAD), `implement` first creates and switches to a local
  branch, `dev-kit/<slug>` unless you pass `branch=<name>`; on any other branch it stays. Say
  "stay on this branch" to skip it.
- Nothing in the family commits, pushes or opens a PR. After an `approve`, you decide.
- `investigate` never edits tracked files.

## Headless runs

Under `claude -p --permission-mode dontAsk`, every tool call the allow-list does not name is
denied, and nobody is there to approve it. Each part of a chained shell command must match a
rule on its own, so the plan, implement and review skills and every dev-kit agent run one
plain command per Bash call (no `&&`, `;`, pipes or `mkdir`), and treat a denial as one
unmatched command, not as Bash being off. A starting allow-list for the whole pipeline, for the repo's
`.claude/settings.json` or a file passed with `--settings`:

```json
{
  "permissions": {
    "allow": [
      "Read", "Grep", "Glob", "Agent", "Skill",
      "Write(.dev-kit/**)", "Edit(.dev-kit/**)",
      "Write(src/**)", "Edit(src/**)",
      "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)",
      "Bash(git rev-parse:*)", "Bash(git ls-files:*)",
      "Bash(python3 /path/to/dev-kit/skills/plan/scripts/plan_tool.py:*)",
      "Bash(npm test:*)"
    ]
  }
}
```

- Replace `src/**` with the paths the plan's slices own, and `npm test` with each command in
  the manifest's `gates` and `integration_gates`, written the way the plan writes it.
- `/path/to/dev-kit` is the folder you pass to `--plugin-dir`, or the installed plugin's
  folder under `~/.claude/plugins/`.
- `plan_tool.py branch` creates the working branch itself, so no `git switch` rule is needed.
  Nothing here allows `git commit`, `git push` or network access.
- The plan phase needs only the read and `.dev-kit/**` rules, the git read rules and
  `plan_tool.py`; review adds the gate commands. The same rules work as `--allowedTools`,
  comma-separated.
- Under the Agent SDK, for example `anthropics/claude-code-action`, set
  `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`. Subagents start in the background by default, and
  the host stops at the first result, so the plan would end before the planner runs. The
  tested GitHub workflow and its setup are in `docs/ai-sdlc/templates/dev-kit.yml` and
  `docs/ai-sdlc/onboard-a-repo.md` at the repo root.

## Evals

`evals/` holds a `claude plugin eval` suite (trigger and outcome checks). Run it with
`claude plugin eval plugins/dev-kit --max-cost-usd 5`.
