---
title: Decision — run the AI-SDLC with plugins-ci
id: adopt-plugins-ci
doc_type: decision
summary: Use Claude Code plugins (dev-kit) run headless with claude -p, plus the Claude Code GitHub Action, as the AI-SDLC for every repo; not a Factory-like platform and not the Claude apps alone.
status: current
updated: 2026-11-05
audience: software engineers
source_commit: 30d2f9e
scope: [docs/ai-sdlc/, prototypes/ai-sdlc/, plugins/dev-kit/]
tags: [ai-sdlc, adr, plugins-ci, dev-kit, claude-code, headless, github-action, agent-sdk, managed-agents]
aliases: [AI-SDLC decision, ADR plugins-ci, approach A, Factory-like platform, agent-platform, claude-apps, cloud sessions]
related: [docs/ai-sdlc/report.md, docs/ai-sdlc/rubric.md, docs/ai-sdlc/research/plugins-ci.md, docs/ai-sdlc/research/agent-platform.md, docs/ai-sdlc/research/claude-apps.md, prototypes/ai-sdlc/README.md]
group: Decisions
order: 10
html_twin: adopt-plugins-ci.html
---

# Decision — run the AI-SDLC with plugins-ci

## TL;DR
- Decision: `plugins-ci` is the AI-SDLC for all three project types (web-app, small-scripts, plugin-repo) (`docs/ai-sdlc/report.md:83-129`).
- `plugins-ci` = Claude Code plugins (`dev-kit`: plan, implement, review) run headless with `claude -p`, plus `anthropics/claude-code-action@v1` as the CI step.
- Rubric totals out of 40: plugins-ci 31, claude-apps 27, agent-platform 26 (`docs/ai-sdlc/report.md:44-54`).
- A prototype ran plan → implement → review on a clone of `whisk-proto-gcp` twice: exit 0, 2 files changed, tests passed, review approved, USD 1.19 and 1.35 (`docs/ai-sdlc/report.md:150-151`).
- Rejected: a Factory-like platform (8-20 developer-day build, API billing only) and the Claude apps alone (cloud sessions do not load plugins).

## Context
- Reader and goal: a solo developer with many repos (`whisk-proto-gcp`, `static-web-aws-ai`, `resume-forge`, this repo) wants one AI-SDLC for any project, optimised for per-repo setup effort and monthly cost.
- SDLC phases scored: intake, plan, implement, test, review, release, operate (`docs/ai-sdlc/rubric.md:91-99`).
- Starting point: this repo already ships `dev-kit` and `campaign-kit` as Claude Code plugins in the `adrien-skills` marketplace (`README.md:1-20`).
- Method: a 2-round campaign (`ai-sdlc-approaches`, 2026-11-05) with sourced fact sheets per approach, a scored rubric of 8 dimensions, and a scripted trial. Every product capability was verified online on 2026-11-05.
- Constraint: no outward actions during the evaluation (no push, PR, sign-up or payment), so only locally runnable options could be trialled.

## Options considered
- `plugins-ci` (approach A) — Claude Code plugins, skills, subagents and hooks; headless `claude -p`; the Claude Code GitHub Action (`docs/ai-sdlc/research/plugins-ci.md:9`, `docs/ai-sdlc/research/plugins-ci.md:21`).
  - Pros: no build; 8-25 setup minutes per repo; one marketplace serves every repo; ships plan and review phases; runs locally with no sign-up.
  - Cons: a local `claude -p` run executes a repo's hooks and `.mcp.json` without a trust prompt; intake has no ticket queue.
- `agent-platform` (approach B) — a Factory-like app on the Claude Agent SDK or Claude Managed Agents (`docs/ai-sdlc/research/agent-platform.md:13`).
  - Pros: highest autonomy (cron deployments, webhooks, long sessions); a fresh sandbox per session.
  - Cons: 8-20 developer-day build for intake, dashboard, queue and review UI (`docs/ai-sdlc/research/agent-platform.md:66`); API billing only, no subscription; Managed Agents is beta.
- `claude-apps` (approach C) — Claude Code cloud sessions (web, desktop, mobile), scheduled tasks, Slack, connectors, Projects (`docs/ai-sdlc/research/claude-apps.md:12`).
  - Pros: nothing to build; isolated cloud VM per task; scheduled tasks run with the laptop closed.
  - Cons: cloud sessions do not load plugins or the repo's `enabledPlugins` (`docs/ai-sdlc/research/plugins-ci.md:13`); needs a GitHub remote, the Claude GitHub App and a paid plan; scheduled tasks are a research preview.
- Vendor products (Factory, Devin and similar) were reference designs only, not scored: the user chose build over buy.

## Comparison
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
| Total (of 40) | 31 | 26 | 27 |
| Setup minutes per new repo | 8-25 | 30-45 | 25 |
| Monthly USD, 100 tickets (estimate) | 200-450 API, 100-200 plan | 200-330 | 100-200 |

- Scores are 1-5, 5 best for a solo developer with many repos (`docs/ai-sdlc/rubric.md:16-25`).
- Cost and setup figures are estimates (`docs/ai-sdlc/rubric.md:123-127`); the flat-plan fit for 100 tickets a month is [unverified].

## Decision and rationale
- Decision: adopt `plugins-ci` as the AI-SDLC for web-app, small-scripts and plugin-repo projects; each project type names `Recommended: plugins-ci` (`docs/ai-sdlc/report.md:90`, `docs/ai-sdlc/report.md:107`, `docs/ai-sdlc/report.md:120`).
- setup-effort — no platform build; per repo, install `dev-kit` at project scope and commit the target repo's project settings file (`enabledPlugins`) (`prototypes/ai-sdlc/README.md:76-91`).
- phase-coverage — the only approach that ships plan and review as skills; `/dev-kit:plan` stops for approval (`plugins/dev-kit/skills/plan/SKILL.md`).
- multi-repo-reuse — one marketplace repo is the single source of skills for every repo; cloud sessions cannot use it.
- maturity-lock-in — plugins, hooks, `claude -p` and Action v1 are documented as current; the assets are portable Markdown and JSON.
- Proven locally — the only approach the campaign could trial without sign-up, push or new access; the trial passed twice (`docs/ai-sdlc/report.md:142-165`).

## Usage per project type
- web-app — dev-kit's path-owned slices and repo-read gates fit multi-area tickets; work lands on a branch reviewed as a normal PR. Runner-up: `claude-apps` (`docs/ai-sdlc/report.md:88-103`).
- small-scripts — local `claude -p` or an interactive session, no workflow file or secret. Add one `claude-apps` scheduled task only for a recurring job that must run while the machine is off (`docs/ai-sdlc/report.md:105-116`).
- plugin-repo — the marketplace here is dogfooded locally with `--plugin-dir`; `claude-apps` cannot load plugins (`docs/ai-sdlc/report.md:118-129`).

## Consequences
- Positive — no platform to build or host; setup per repo is minutes; dev-kit improvements reach every repo through the marketplace.
- Positive — measured cost of USD 1.19-1.35 per S ticket, about USD 120-135 a month for 100 such tickets at API-equivalent prices; below the 200-450 estimate [inferred].
- Negative — headless runs need a safety check: `claude -p` runs a repo's `.mcp.json` and `.claude/` hooks without a trust prompt; `trial.sh` aborts when it finds them (`prototypes/ai-sdlc/trial.sh:120-129`).
- Negative — `--permission-mode dontAsk` denied 4-7 compound shell commands per trial run; the agents recovered at the cost of a few turns.
- Negative — no hosted intake queue or dashboard; intake is GitHub issues, `@claude` mentions or a manual `/dev-kit:plan`.
- Follow-up done — fixes for the trial's gaps ship with this decision in dev-kit 1.2.0 and campaign-kit 0.2.0: implement creates a working branch, allow-list guidance for headless runs, `plan_tool.py baseline` outside the cwd, and an end-of-run `recap.md` (`plugins/dev-kit/README.md`, `plugins/campaign-kit/README.md`). Not yet exercised by a real `trial.sh` run [unverified].
- Follow-up — wire the GitHub Action per repo: install the Claude GitHub App, add `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` as a secret, add the workflow sketched in `prototypes/ai-sdlc/README.md:93-104` [proposal].

## Revisit when
- A flat plan cannot absorb the monthly ticket volume — `running-cost` for plugins-ci and claude-apps drops to 3 and the API figures apply (`docs/ai-sdlc/report.md:133-134`).
- Cloud sessions start loading plugins — `claude-apps` becomes a real alternative for web-app and plugin-repo (`docs/ai-sdlc/report.md:135-136`).
- Managed Agents leaves beta and gains a repo-event trigger, or the work grows to a team or many more repos — the platform build could pay back (`docs/ai-sdlc/report.md:137-139`).
- A re-measured cost on the 5.5 models, or on larger tickets, is far from the estimates — redo the cost table.

## Invariants
- NEVER run `claude -p` in a repo whose `.mcp.json`, `.claude/settings*.json` or `.claude/hooks` you have not reviewed (`prototypes/ai-sdlc/trial.sh:120-126`).
- Headless phases MUST run with `--permission-mode dontAsk`, an explicit `--allowedTools` list and `--max-budget-usd` per phase (`prototypes/ai-sdlc/trial.sh:136-143`).
- The human plan-approval gate stays human in real use; `trial.sh` scripts it only for the trial (`prototypes/ai-sdlc/README.md:63-65`).

## Open questions
- Whether one Max plan absorbs about 100 tickets a month [unverified].
- Per-ticket cost on the 5.5 models: the trial's CLI (2.1.76) resolved `sonnet` and `opus` to the 4.6 models [unverified].
- Only web-app was trialled; small-scripts and plugin-repo rest on the rubric alone.
- The Action workflow's `plugin_marketplaces` and `plugins` inputs were not verified against a live run [unverified].

## Sources
- `docs/ai-sdlc/report.md:83-129` — recommendation per project type
- `docs/ai-sdlc/report.md:142-165` — prototype findings, two measured runs
- `docs/ai-sdlc/rubric.md:16-25` — scores with sources
- `docs/ai-sdlc/rubric.md:91-99` — phase coverage
- `docs/ai-sdlc/rubric.md:123-127` — cost and setup
- `prototypes/ai-sdlc/trial.sh:120-143` — safety check and headless phase flags
- `prototypes/ai-sdlc/README.md` — per-repo setup and the Action workflow sketch
- https://code.claude.com/docs/en/headless — `claude -p`
- https://code.claude.com/docs/en/github-actions — Claude Code GitHub Action
- https://code.claude.com/docs/en/cloud-environments — what cloud sessions load
- https://platform.claude.com/docs/en/managed-agents/overview — Managed Agents (beta)
