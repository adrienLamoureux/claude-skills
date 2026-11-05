# AI-SDLC with Claude: three approaches compared

Scope: a solo developer with many repos who wants to optimise per-repo setup effort and monthly
cost. Scores, phase cells and cost figures are in `docs/ai-sdlc/rubric.md`; per-approach facts
and sources are in `docs/ai-sdlc/research/`. Everything is verified online on 2026-11-05; cost
numbers are estimates, with one measured data point: USD 1.19-1.35 per S ticket on 4.6 models
(see `## Prototype findings`).

## Summary

Use `plugins-ci` for all three project types. It has the lowest per-repo setup (8-13 minutes
local, 18-25 with CI), the only shipped plan-implement-review pipeline (`dev-kit`), the
strongest maturity score, and it is the only approach that can be tried locally with no sign-up,
push or new access. `claude-apps` is a good complement once a repo is on GitHub, but plugins do
not load in its cloud sessions. `agent-platform` costs 8-20 developer-days to build and cannot
use a flat subscription, which a solo developer does not recover.

## The three approaches

- **`plugins-ci`.** Claude Code plugins, skills, subagents and hooks, run headless with
  `claude -p`, or in GitHub through `anthropics/claude-code-action@v1`
  (https://code.claude.com/docs/en/headless, https://code.claude.com/docs/en/github-actions).
  This repo's `dev-kit` (plan, implement, review) and `campaign-kit` are the pipeline. The
  assets are Markdown and JSON in a git marketplace, enabled per repo through
  `.claude/settings.json` (https://code.claude.com/docs/en/plugins/org).
- **`agent-platform`.** A standalone, Factory-like app you build on the Claude Agent SDK
  (self-hosted loop) or on Claude Managed Agents (Anthropic-hosted loop, beta)
  (https://code.claude.com/docs/en/agent-sdk/overview,
  https://platform.claude.com/docs/en/managed-agents/overview). It supplies the loop, sandbox,
  budgets and cron; intake, dashboard, queue and review UI are yours to write.
- **`claude-apps`.** Anthropic's own surfaces: cloud sessions (web, desktop, mobile), scheduled
  tasks with schedule, API and GitHub-event triggers, Slack, connectors and Projects
  (https://code.claude.com/docs/en/claude-code-on-the-web,
  https://code.claude.com/docs/en/routines). Nothing to build, but it needs a paid plan, a
  GitHub remote and the GitHub App.

Reference designs, not scored: Factory documents Droids, Automations, Workstreams and an API as a
component checklist for approach B (https://docs.factory.com/). Anthropic's Claude Tag is the
channel-based team design for approach C (https://claude.com/docs/claude-tag/overview).

## Comparison

Scores are 1-5, 5 is best for a solo developer with many repos.

| Dimension | plugins-ci | agent-platform | claude-apps |
|---|---|---|---|
| setup-effort | 4 | 2 | 3 |
| running-cost | 4 | 2 | 4 |
| phase-coverage | 4 | 3 | 3 |
| autonomy | 4 | 5 | 4 |
| human-control | 4 | 4 | 4 |
| multi-repo-reuse | 4 | 4 | 3 |
| isolation-security | 3 | 4 | 4 |
| maturity-lock-in | 4 | 2 | 2 |
| **Total (of 40)** | **31** | **26** | **27** |

Reasons, in short:

- **Setup.** `plugins-ci` needs no build and 8-25 minutes per repo. `claude-apps` needs about
  25 minutes plus per-repo `.claude/` copies. `agent-platform` needs 30-45 minutes per repo after
  an 8-20 developer-day build.
- **Cost.** `plugins-ci` and `claude-apps` can both run on a flat plan (USD 100-200); `plugins-ci`
  can also use the API (USD 200-450). `agent-platform` is API-only (USD 200-330) because the SDK
  terms exclude a claude.ai login for products built on it
  (https://code.claude.com/docs/en/agent-sdk/quickstart). Plan fit for 100 tickets a month is
  unverified for both flat-plan routes.
- **Coverage.** Only `plugins-ci` ships planning and review as skills. The other two cover
  implement and test well and leave planning or review to you or to a trigger.
- **Autonomy.** `agent-platform` is highest (cron deployments, webhooks, long sessions) but only
  after you build intake. The Action and cloud triggers are close behind and need no build.
- **Reuse.** One marketplace repo serves every repo for `plugins-ci`. In cloud sessions the
  repo's enabled plugins are not loaded (https://code.claude.com/docs/en/cloud-environments),
  so `claude-apps` copies files into each repo.
- **Security.** The hosted options isolate each task in a fresh container. `plugins-ci` is
  strong in CI and weakest on a local run, where a repo's hooks and `.mcp.json` run under `-p`
  without a trust prompt (https://code.claude.com/docs/en/headless).
- **Maturity.** `plugins-ci` is built on documented, current features. Managed Agents is beta,
  the SDK is 0.x, and scheduled tasks are a research preview.

The sum is a rough aid. The decision below rests on the dimensions named in each project type,
not on the total.

## Recommendation

One approach per project type. A hybrid is described in prose only; the line `Recommended:`
names the primary approach.

### web-app

Recommended: plugins-ci

Samples: `whisk-proto-gcp`, `static-web-aws-ai`. A multi-area ticket suits dev-kit's
path-owned slices and its gates, which are read from the repo's own scripts and CI. On
`setup-effort` it needs 8-13 minutes locally or 18-25 with the GitHub Action, against an
8-20 developer-day build for `agent-platform`. On `phase-coverage` it is the only approach with
shipped plan and review phases (4 full, 3 partial). On `human-control` the work lands on a
branch you review as a normal PR, and `/dev-kit:plan` stops for approval.
`claude-apps` is the runner-up: it would run the repo's tests in a cloud VM, but the plugin
pipeline cannot run there (`multi-repo-reuse` 3), and deploy credentials need network secrets.
Note for the trial: `static-web-aws-ai` already tracks `.claude/`, `.github/workflows/` and
`CLAUDE.md`, and `claude -p` runs a repo's hooks and `.mcp.json` without a trust prompt
(`isolation-security`), so a trial on it needs the same safety check as on `whisk-proto-gcp`,
which tracks neither.

### small-scripts

Recommended: plugins-ci

Sample: `resume-forge` (no CI, no `.claude/`). The deciding dimensions are `setup-effort` and
`running-cost`: a local `claude -p` run or an interactive session needs no workflow file, no
secret and no GitHub App (8-13 minutes), and it runs on the same flat plan or on API tokens.
`claude-apps` is a fair second choice (25 minutes, scheduled tasks run with the laptop closed)
and scores equal on `human-control`, but it needs the repo on GitHub with the App installed and
a research-preview scheduler for `autonomy`. `agent-platform` is oversized for a repo with few
tickets (`setup-effort` 2, `running-cost` 2). If a recurring job such as a weekly content
refresh must run while the machine is off, add a `claude-apps` scheduled task for that one job.

### plugin-repo

Recommended: plugins-ci

Sample: this repo. It already runs `claude plugin validate`, an evals workflow and `--plugin-dir`
loading (`scripts/validate.sh`, `.github/workflows/evals.yml`). The deciding dimensions are
`multi-repo-reuse` and `maturity-lock-in`: the marketplace here is the single source for every
repo's skills, and the assets are portable Markdown and JSON. `claude-apps` is a poor fit
because cloud sessions do not load plugins, so a plugin repo cannot dogfood its own plugins
there (https://code.claude.com/docs/en/plugins/install, Cloud session tab). `agent-platform`
adds hosting cost and a build to a repo that is edited and validated locally (`setup-effort`,
`running-cost`).

## What would change the recommendation

- Plans cannot absorb 100 tickets a month: `plugins-ci` and `claude-apps` both fall to
  `running-cost` 3 and the API figures (USD 200-450) apply.
- Plugins become loadable in cloud sessions: `claude-apps` `multi-repo-reuse` and the plugin-repo
  fit improve, and it becomes a real alternative for web-app.
- Managed Agents leaves beta and a repo-event trigger appears: `agent-platform`
  `maturity-lock-in` and `autonomy` improve; it would still need the build effort to pay back,
  which needs many more repos or a team.
- Per-ticket cost from the trial is far from the estimates: re-run the cost table.

## Prototype findings

The prototype in `prototypes/ai-sdlc/` runs `plugins-ci` for `web-app`: `trial.sh` clones
`whisk-proto-gcp` to a scratch folder, checks it for repo hooks and `.mcp.json`, then runs
dev-kit's plan, implement and review as three `claude -p` phases with per-phase cost caps.

| Run | Exit / ok | Changed files | Gate | Review | Cost (USD) |
|---|---|---|---|---|---|
| Lane runner | 0 / true | 2 | unittest pass (13/13) | approve | 1.19 (plan 0.44, implement 0.39, review 0.36) |
| Checker (independent) | 0 / true | 2 | unittest pass | approve | 1.35 (plan 0.45, implement 0.52, review 0.38) |

- Both runs used one S ticket (`prototypes/ai-sdlc/ticket.md`), Claude Code 2.1.76 and the local
  Claude login. The source repo's HEAD and status were unchanged before and after each run.
- The subagents ran on `claude-sonnet-4-6` and `claude-opus-4-6`, not the 5.5 models the price
  table uses, so the measured cost is not on the same basis as the estimates. 100 S tickets a
  month at this rate is about USD 120-135 on API-equivalent pricing, below the 200-450 estimate;
  the cost table is left as an estimate until a run on 5.5 models and larger tickets.
- `dontAsk` denied 4-7 tool calls per run (compound shell commands such as `&&` and `2>&1;`, and
  one `mkdir`). The agents recovered each time, at the cost of a few turns.
- `/dev-kit:implement` did not create a working branch; it stayed on `main` in the clone.
- A fresh clone has no virtualenv, so the repo's own `make test` gate could not run; the ticket
  uses a stdlib-only gate.
- Only `web-app` was trialled. `small-scripts` and `plugin-repo` are recommended from the
  rubric, not from a run.

## Sources not verified

- GitHub-hosted runner price per minute, and plan limits for 100 tickets a month.
- Artifacts and mobile hand-off for `claude-apps` were not researched in depth.
- GitHub issue events as a scheduled-task trigger.
- All token-per-ticket volumes behind the cost figures.
