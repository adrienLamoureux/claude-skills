# AI-SDLC prototype: plugins-ci on a web app

Prototype of approach `plugins-ci` (Claude Code plugins plus headless `claude -p`, with the
Claude Code GitHub Action as the CI step) for project type `web-app`. It runs this repo's
`dev-kit` plugin through plan, implement and review on a throwaway clone of
`whisk-proto-gcp`, under a spend cap, and writes a machine-checkable result.

Everything here is local. Nothing is pushed, no PR is opened, no workflow runs.

## Files

| File | Purpose |
|---|---|
| `trial.sh` | Entry point. Run from the repo root. |
| `ticket.md` | The fixed sample ticket: a pure `format_retry_after` helper plus a `unittest` file. It creates 2 new files and touches no existing one. |
| `README.md` | This file. |

## Run it

```bash
# plumbing only: clone, safety check, result file; no claude calls, no spend
TRIAL_DRY_RUN=1 bash prototypes/ai-sdlc/trial.sh

# real run: three headless claude calls, total spend capped below USD 5
bash prototypes/ai-sdlc/trial.sh
```

Output goes to `.campaign-kit/ai-sdlc-approaches/trial/` (gitignored):

- `whisk-proto-gcp/` the clone (`git clone --no-hardlinks`, removed and recreated each run)
- `trial-result.json` keys `approach`, `project_type`, `repo`, `ticket`, `phases_run`,
  `changed_files`, `cost_usd`, `ok`, plus `phase_costs`, `phase_exit`, `permission_denials`,
  `sibling_unchanged`, `gate_exit`, `review_verdict`, `start_sha`, `dry_run`, `abort_reason`,
  `notes`
- `logs/` per-phase `<phase>.json` (the `claude -p --output-format json` result) and
  `<phase>.stderr`, `changed-files.txt`, `gate.txt`, and `dev-kit-run/` (the plan, slice,
  check and review files the plugin wrote)

The script exits 0 only when `ok` is true. A dry run exits 0 when the plumbing worked but
always writes `ok: false` and `dry_run: true`.

## What the trial does

1. Records the sibling repo's `HEAD` and `git status --porcelain` using `git -C` with
   `GIT_OPTIONAL_LOCKS=0` (read-only). It never `cd`s into the sibling.
2. Clones it into the trial folder and records the start SHA.
3. Safety check: aborts with `ok: false` if the clone contains `.mcp.json`,
   `.claude/settings*.json` or `.claude/hooks`. `claude -p` skips the workspace trust dialog
   and runs those without asking.
4. Three headless calls from inside the clone, each with `--plugin-dir <repo>/plugins/dev-kit`
   (read-only), `--setting-sources project,local` (so the user's own plugins and settings do
   not leak in), `--model sonnet`, `--strict-mcp-config`, `--output-format json`,
   `--no-session-persistence`, `--permission-mode dontAsk` (anything not allow-listed is
   denied, never prompted), an explicit `--allowedTools` list per phase, and its own
   `--max-budget-usd`:

   | Phase | Prompt | Writes allowed | Cap (USD) |
   |---|---|---|---|
   | plan | `/dev-kit:plan <ticket> size=S DIR=.dev-kit/retry-hint` | `.dev-kit/**` | 1.4 |
   | implement | `/dev-kit:implement retry-hint` | `backend/**`, `.dev-kit/**` | 1.6 |
   | review | `/dev-kit:review retry-hint effort=medium` | `.dev-kit/**` only | 1.8 |

   Between plan and implement the script runs `plan_tool.py check` and `plan_tool.py approve`
   on `plan.md`. That is a scripted stand-in for the human approval gate, which is the one
   step a person does in real use.
5. Sums `total_cost_usd` from the three result files, counts `changed_files` from
   `git diff --name-only <start-sha>` plus untracked files (the `.dev-kit/` run folder and
   `__pycache__` are excluded), then runs the ticket's own gate itself with the system
   `python3` (`python3 -m unittest discover -s backend/tests -t backend -p test_retry_hint.py`).
6. Re-checks the sibling's `HEAD` and status, then writes `trial-result.json`.

`ok` is true only if every phase exits 0 with `is_error` false, `changed_files >= 1`, the
summed cost is at most 5, the independent gate passes, `review.md` exists and the sibling is
unchanged.

## Per-repo setup (what a new repo needs)

Local only, about 8-13 minutes (estimate from `docs/ai-sdlc/research/plugins-ci.md`):

1. Add the marketplace once per machine and install the plugin at project scope:
   `claude plugin marketplace add adrienLamoureux/claude-skills`, then
   `claude plugin install dev-kit@adrien-skills --scope project`. Commit the resulting
   `.claude/settings.json` (`enabledPlugins`).
2. Make the repo's quality gates discoverable to the scout: an `AGENTS.md` or `CLAUDE.md`
   naming the test, lint and build commands, or a `Makefile` or package scripts that do.
   `whisk-proto-gcp` has a `Makefile` and a `pyproject.toml`, but its gates need a project
   virtualenv, which a fresh clone lacks. The sample ticket therefore names a stdlib-only gate.
3. Run `/dev-kit:plan <ticket>`, approve, `/dev-kit:implement <slug>`, `/dev-kit:review <slug>`.

Note on step 1: committing `.claude/settings.json` is exactly the file the trial's safety check
refuses to run headless without a look. Review it before running `claude -p` in that repo.

## Outward CI step: not executed (superseded by docs/ai-sdlc/onboard-a-repo.md)

Running the same pipeline from GitHub needs actions this campaign forbids (a push, a workflow
file in the target repo, an Actions secret, the Claude GitHub App). It is documented here and
was not run. Sketch, using the inputs listed in the fact sheet
(`docs/ai-sdlc/research/plugins-ci.md`; sources
https://code.claude.com/docs/en/github-actions and
https://github.com/anthropics/claude-code-action). Input names were not re-verified against a
live run:

```yaml
# .github/workflows/dev-kit.yml  (NOT created by this prototype)
name: dev-kit
on:
  issues:
    types: [labeled]          # label an issue "ai-plan" to start
permissions:
  contents: write             # push a branch, never merge
  issues: write
  pull-requests: write
  id-token: write
jobs:
  plan:
    if: github.event.label.name == 'ai-plan'
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}   # or claude_code_oauth_token
          plugin_marketplaces: https://github.com/adrienLamoureux/claude-skills.git
          plugins: dev-kit@adrien-skills
          prompt: |
            /dev-kit:plan Issue #${{ github.event.issue.number }}: ${{ github.event.issue.title }}
            Headless run: use defaults, write the plan to .dev-kit/issue-${{ github.event.issue.number }}/,
            and post a summary as an issue comment. Do not implement.
          claude_args: |
            --max-turns 40
            --max-budget-usd 2
            --allowedTools "Read,Grep,Glob,Task,Write(.dev-kit/**),Bash(git log:*)"
```

Per-repo steps the workflow adds, about 10 more minutes: install the GitHub App
(`/install-github-app`), add the secret, copy the workflow file. A human then approves the plan
in the issue and a second workflow (same shape, `/dev-kit:implement`, on a branch) opens the PR
for review. The trial's scripted approval stands in for that comment.

## Known limits of this prototype

- One fixed ticket and one sample repo. It shows the pipeline runs headless, not that it
  generalises.
- The gate is stdlib-only on purpose. A ticket that needs the project virtualenv would need an
  install step inside the clone, which this prototype does not do.
- Cost is the client-side `total_cost_usd` estimate from `claude -p`, not a bill.
- The trial uses the local Claude login (`ANTHROPIC_API_KEY` is unset on this machine), so the
  spend may count against a subscription rather than an API balance.

## Measured result (round 2 spike, 2026-11-05)

One real run of `bash prototypes/ai-sdlc/trial.sh` on Claude Code 2.1.76 with the local login:
exit 0, `ok: true`, `phases_run` plan/implement/review, `changed_files` 2
(`backend/app/agent/retry_hint.py`, `backend/tests/test_retry_hint.py`), independent gate 13/13
tests, review verdict `approve`, sibling `HEAD` and status unchanged. Client-side cost:
plan 0.44, implement 0.39, review 0.36, total 1.19 USD (about 6 minutes wall clock). The
subagents ran on `claude-sonnet-4-6` and `claude-opus-4-6` as reported in each result's
`modelUsage`. Four tool calls were denied by `dontAsk` (a `mkdir -p` outside the allow-list and
three compound shell commands using `2>&1;` or `&&`); the agents worked around them. A single
run is one data point for one small ticket, not a distribution.

## Re-run on 5.5 models (2026-11-06)

Claude Code 2.1.318 resolves `sonnet` and `opus` to `claude-sonnet-5-5` and `claude-opus-5-5`.

- With dev-kit 1.2.0 the run failed (exit 1, USD 0.50). Plan passed, but implement and review
  each sent a chained shell command first, had it denied, concluded Bash was off and stopped.
- dev-kit 1.2.1 adds the one-command-per-call rule to the plan, implement and review skills.
  The next run passed: exit 0, `ok: true`, 2 changed files, 8/8 tests, review `approve`,
  USD 0.78 (plan 0.33, implement 0.23, review 0.22). Implement created the branch
  `dev-kit/retry-hint`. One call was denied (`ruff`, which the allow-list does not name).
