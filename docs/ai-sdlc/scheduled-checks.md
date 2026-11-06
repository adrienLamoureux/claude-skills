---
title: Scheduled checks — what could run on a cron, and what it costs
id: scheduled-checks
doc_type: concept
summary: Catalogue of scheduled (cron) checks for the AI-SDLC repos — the two already built and switched off, candidates ranked by value and cost, and the off-by-default pattern every new one follows.
status: proposal
updated: 2026-11-06
audience: software engineers
source_commit: 1fada55
scope: [docs/ai-sdlc/, .github/workflows/]
tags: [ai-sdlc, cron, schedule, github-actions, cost, evals, drift-check, dependabot, codeql, claude-code-action]
aliases: [cron jobs, scheduled workflows, nightly checks, weekly checks, scheduled tasks, routines, ENABLE_NIGHTLY_EVAL, ENABLE_DRIFT_CHECK]
related: [docs/ai-sdlc/onboard-a-repo.md, docs/ai-sdlc/adopt-plugins-ci.md, docs/ai-sdlc/research/claude-apps.md]
group: Guides
order: 30
html_twin: scheduled-checks.html
---

# Scheduled checks — what could run on a cron, and what it costs

## TL;DR
- Two cron checks are built, both in whisk-studio PR #8 (open on 2026-11-06), and both are off by default: a nightly live agent eval (bills AWS Bedrock) and a weekly docs drift check (uses the Claude plan).
- Runner minutes are not the cost: standard GitHub-hosted runners are free in public repositories. The cost is Claude plan usage for AI checks and AWS Bedrock for live evals.
- Every cron check follows one pattern: `schedule` plus `workflow_dispatch`, a job gated by an `ENABLE_<CHECK>` repo variable, a spend cap, read-only tools, and one issue as output.
- Cheapest wins first: GitHub's own Dependabot alerts and CodeQL default setup need no workflow; neither is enabled in whisk-studio or whisk-proto-gcp (checked 2026-11-06).
- GitHub disables scheduled workflows in a public repository after 60 days without repository activity.
- Nothing in this doc is enabled; each candidate is a [proposal] until it is built and listed in `## Checks built`.

## Cost drivers for scheduled checks
| Driver | Applies to | Cost | Control |
|---|---|---|---|
| GitHub-hosted runner minutes | every scheduled workflow | free in public repositories (https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions) | `timeout-minutes` |
| Claude via `CLAUDE_CODE_OAUTH_TOKEN` | AI checks through `anthropics/claude-code-action` | counts against the Claude plan | `--max-budget-usd`, `--max-turns`, how often it runs |
| AWS Bedrock | live agent evals of the app's own model | AWS bill | `EVAL_MAX_USD` per run |
| GitHub-native scanners | Dependabot, CodeQL | no workflow to pay for; free status for these repos [unverified] | repo settings |

## Off-by-default pattern for a cron check
1. Triggers — `on: schedule` with a `cron:` line, plus `workflow_dispatch` so a person can run it from the Actions tab or with `gh workflow run <file>`.
2. Gate — the job carries `if: github.event_name == 'workflow_dispatch' || vars.ENABLE_<CHECK> == 'true'`. The schedule still fires; the job is skipped until `gh variable set ENABLE_<CHECK> --body true -R <owner>/<repo>`. `gh variable delete ENABLE_<CHECK>` turns it off again.
3. Caps — Claude steps pass `--max-budget-usd` and `--max-turns` in `claude_args`; other paid APIs get a per-run cap like `EVAL_MAX_USD`; every job sets `timeout-minutes`.
4. Least privilege — minimal `permissions:`, a read-only `--allowedTools` list (`Read,Grep,Glob`) plus `Bash(gh issue create:*)` when the check reports.
5. Output — one issue only when something is wrong. A scheduled check never pushes, merges or deploys.
6. Claude steps set `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS: "1"`, or subagents get cut off (`docs/ai-sdlc/onboard-a-repo.md:90-100`).
7. Stop completely — `gh workflow disable <file> -R <owner>/<repo>`; `gh workflow enable <file>` restores it (https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow).

## Checks built
| Check | Repo and file | Schedule | Cost driver | Cap | Turn on |
|---|---|---|---|---|---|
| Nightly live agent eval | whisk-studio `nightly-eval.yml` (PR #8, open) | daily 03:17 UTC | AWS Bedrock, agent model Haiku 4.5 | `EVAL_MAX_USD` 0.50 per run | `ENABLE_NIGHTLY_EVAL=true` and the `EVAL_AWS_ACCESS_KEY_ID`, `EVAL_AWS_SECRET_ACCESS_KEY` secrets (not created) |
| Weekly docs drift check | whisk-studio `drift-check.yml` (PR #8, open) | Mondays 06:00 UTC | Claude plan | USD 1 and 12 turns per run | `ENABLE_DRIFT_CHECK=true` |

- The nightly eval compares the live agent's tool choices against whisk-studio's eval baseline, `baseline.json` (47/52, 90.4%) and opens an issue on a regression; the replay tier (`npm run eval`) already runs free in every CI build [inferred from PR #8's description].
- The drift check compares whisk-studio's `ai-context.md` and `api-spec.md` docs with its backend and frontend code and opens one "Docs drift" issue when they disagree.
- Not a cron, for comparison: `pr-review.yml` in the same PR reviews every non-draft PR with Claude (8 turns, no budget cap).

## Candidate checks
| # | Check | What it catches | AI | Cost | Effort | Repos | Value |
|---|---|---|---|---|---|---|---|
| 1 | Dependabot alerts and security updates | known-vulnerable dependencies | no | GitHub-native [unverified] | repo setting | all | high |
| 2 | CodeQL default setup | security bugs in code; weekly scan [inferred] | no | GitHub-native [unverified] | repo setting | whisk-studio, whisk-proto-gcp | high |
| 3 | Claude token health, monthly | an expired or revoked `CLAUDE_CODE_OAUTH_TOKEN` before a real dev-kit run hits it | yes, one tiny call | cents of plan [inferred] | small | web apps | high |
| 4 | Full test suite on `main`, nightly | flaky or time-dependent tests, breakage from unpinned dependency ranges | no | free runners | copy `ci.yml` with a schedule | web apps | medium |
| 5 | Production smoke check, daily | the deployed whisk-studio site broken between deploys | no | free runners; needs the site URL and a test user as secrets | medium; whisk-studio already has `sanity-check.mjs`, `ui-smoke.mjs` (cdk scripts) and a Playwright `sanity.spec.js` | whisk-studio | medium |
| 6 | Weekly security review of merged changes | security regressions that slipped past PR review | yes | plan, cap USD 1-2 | small | web apps | medium |
| 7 | Plugin evals on a schedule | dev-kit or campaign-kit skills that break on a new Claude Code release; `evals.yml` runs only on `workflow_dispatch` today (`.github/workflows/evals.yml:3-4`) | yes | plan | small: add a gated schedule | claude-skills | medium |
| 8 | Dependency audit cron (`npm audit --audit-level=high`, `pip-audit`) | the same as 1, for repos that keep Dependabot off | no | free runners | small | web apps | low if 1 is on |
| 9 | Weekly test-gap scan | the least-tested routes, filed as an issue that can become a `dev-kit:plan` ticket | yes | plan | medium | web apps | low |
| 10 | Issue triage for dev-kit | new issues without a size, or ready for `dev-kit:plan` | yes | plan | medium | web apps | low |
| 11 | Docs link check | dead links in Markdown docs | no | free runners | small | claude-skills, whisk-studio | low |
| 12 | Stale issues and PRs (`actions/stale`) | forgotten dev-kit PRs and branches | no | free runners | small | all | low |
| 13 | Infrastructure drift (`cdk diff`) | manual changes to the deployed AWS stack | no | needs read-only AWS credentials | medium | whisk-studio | low |

## Recommended order to enable
1. Dependabot alerts and CodeQL default setup in both web apps — repo settings, no workflow, catches the most for the least.
2. Claude token health check, monthly — one cheap call that keeps the dev-kit workflow from failing on a dead secret.
3. Docs drift check, after PR #8 merges — consider monthly (`cron: "0 6 1 * *"`) instead of weekly until its cost per run is measured.
4. Nightly live eval — keep it manual; run it with `gh workflow run nightly-eval.yml` before a model or prompt change, once the `EVAL_AWS_*` secrets exist.
5. The rest when a real incident shows the need.

## Scheduled checks compared with other ways to run on a timer
| Option | Runs where | Loads dev-kit | Status | Fit |
|---|---|---|---|---|
| GitHub Actions `schedule` | GitHub runner | yes, with `--plugin-dir` | generally available | default for checks tied to a repo |
| Claude Code cloud scheduled tasks | Anthropic cloud | no, plugins do not load in cloud sessions | research preview, minimum interval 1 hour (`docs/ai-sdlc/research/claude-apps.md:10-12`) | checks that need no plugin |
| Desktop local scheduled tasks | this computer, while the app is open and the computer awake | yes | available (`docs/ai-sdlc/research/claude-apps.md:13`) | personal checks across local repos |

## Gotchas
- A scheduled workflow added on a branch does nothing until it reaches the default branch: scheduled runs use the latest commit on the default branch [unverified].
- GitHub disables scheduled workflows in a public repository after 60 days without repository activity; re-enable with `gh workflow enable <file>`.
- A gated-off schedule still records a run each time, with its job skipped [inferred].
- Issues and pushes made with `GITHUB_TOKEN` start no other workflow, so a check's issue will not trigger the dev-kit workflow by itself.
- Scheduled runs can start late when GitHub Actions is under high load [unverified].

## Open questions
- Whether Dependabot alerts, Dependabot security updates and CodeQL default setup cost anything for these public repositories [unverified].
- Claude plan usage per drift-check or PR-review run has not been measured.
- The `EVAL_AWS_*` secrets and an IAM user limited to `bedrock:InvokeModel` do not exist yet.

## Maintaining this scheduled-checks doc
- When a candidate is built, move it to `## Checks built` with its file, schedule, cap and switch; record it in the change log of `docs/ai-sdlc/onboard-a-repo.md`.
- When a check is turned on or off for real, update `## Checks built`.

## Sources
- https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions — standard runners free in public repositories
- https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow — `gh workflow disable`, 60-day inactivity rule
- https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows — the `schedule` event
- https://docs.github.com/en/code-security/code-scanning/enabling-code-scanning/configuring-default-setup-for-code-scanning — CodeQL default setup and its weekly schedule
- https://github.com/adrienLamoureux/whisk-studio/pull/8 — `nightly-eval.yml`, `drift-check.yml`, `pr-review.yml`
- `docs/ai-sdlc/research/claude-apps.md:10-13` — cloud and desktop scheduled tasks
- `.github/workflows/evals.yml:3-4` — plugin evals run only on demand today
