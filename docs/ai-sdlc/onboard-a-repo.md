---
title: Onboard a repo to the AI-SDLC (dev-kit)
id: onboard-a-repo
doc_type: onboarding
summary: Every step to run dev-kit (plan, implement, review) on a repo, locally and from GitHub labels, with the pitfalls the first rollout hit and the repos onboarded so far.
status: current
updated: 2026-11-13
audience: software engineers
source_commit: 45b1347
scope: [docs/ai-sdlc/templates/dev-kit.yml, plugins/dev-kit/, prototypes/ai-sdlc/]
tags: [ai-sdlc, onboarding, dev-kit, github-actions, claude-code-action, setup-token, plugins-ci, headless]
aliases: [AI-SDLC setup, dev-kit workflow, GitHub Action setup, install-github-app, CLAUDE_CODE_OAUTH_TOKEN, label workflow, dev-kit labels]
related: [docs/ai-sdlc/scheduled-checks.md, docs/ai-sdlc/adopt-plugins-ci.md, docs/ai-sdlc/report.md, plugins/dev-kit/README.md, prototypes/ai-sdlc/README.md]
group: Guides
order: 20
html_twin: onboard-a-repo.html
---

# Onboard a repo to the AI-SDLC (dev-kit)

## TL;DR
- The AI-SDLC is the `dev-kit` plugin (plan → implement → review), chosen in the plugins-ci decision (`docs/ai-sdlc/adopt-plugins-ci.md:65-71`).
- Local use needs the plugin once per machine at user scope; every repo on that machine then has `/dev-kit:plan`, `/dev-kit:implement` and `/dev-kit:review`.
- GitHub use (web apps) adds five per-repo steps: the Claude GitHub App, the `CLAUDE_CODE_OAUTH_TOKEN` secret, one Actions setting, two labels, and a `dev-kit.yml` workflow in the repo's workflows folder, copied from `docs/ai-sdlc/templates/dev-kit.yml`.
- Two labels drive the workflow: `dev-kit:plan` on an issue opens a draft PR holding the plan; `dev-kit:implement` on that PR approves it and runs implement and review.
- First end-to-end run, 2026-11-06, whisk-proto-gcp issue #4 → PR #8: plan USD 0.25, implement 0.19, review 0.22; 6 tests pass; review verdict `approve`.
- This doc is maintained: update `## Repos onboarded`, `## Gotchas` and `## Change log` whenever the setup changes.

## AI-SDLC pipeline map
- Local flow — you run `/dev-kit:plan <ticket>`, approve, `/dev-kit:implement <slug>`, `/dev-kit:review <slug>`, then commit yourself.
- GitHub flow — issue labelled `dev-kit:plan` → job `plan` → branch `dev-kit/issue-<n>` + draft PR → PR labelled `dev-kit:implement` → job `implement` (install deps, approve plan, implement, review) → push + recap comment → you merge.
- dev-kit source in CI — each job clones `adrienLamoureux/claude-skills` at `DEV_KIT_REF` (default `main`) and passes `--plugin-dir <clone>/plugins/dev-kit` (`docs/ai-sdlc/templates/dev-kit.yml:37`, `docs/ai-sdlc/templates/dev-kit.yml:68`).
- Billing — the Claude steps use `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}`, so runs count against the Claude subscription (`docs/ai-sdlc/templates/dev-kit.yml:81`).

## Setup per project type
| Project type | Example repos | Local plugin | GitHub workflow |
|---|---|---|---|
| web-app | whisk-proto-gcp, whisk-studio | yes | yes |
| small-scripts | resume-forge | yes | no |
| plugin-repo | claude-skills | yes, via `--plugin-dir` | no |

- Source: the decision's usage per project type (`docs/ai-sdlc/adopt-plugins-ci.md:73-76`).

## One-time machine setup
1. Claude Code CLI — installed at `~/.local/bin/claude`. If the shell says `command not found: claude`, add `export PATH="$HOME/.local/bin:$PATH"` to `~/.zshrc`. Update with `claude update`; CLI 2.1.318 maps `sonnet` and `opus` to the 5.5 models, 2.1.76 mapped them to 4.6 (`docs/ai-sdlc/report.md:142-173`).
2. dev-kit plugin — `claude plugin marketplace add adrienLamoureux/claude-skills`, then `claude plugin install dev-kit@adrien-skills` (user scope). After each merge to claude-skills: `claude plugin marketplace update adrien-skills`, `claude plugin update dev-kit@adrien-skills`, then restart Claude Code.
3. GitHub CLI — `gh auth status` must show the `repo` and `workflow` scopes.
4. Subscription token — `claude setup-token` prints a long-lived token (`sk-ant-oat01-…`) once. Save it for the secret step, or run the command again later for a new one.

## Per-repo setup for local use
- No per-repo install: the user-scope plugin covers every repo on the machine.
- Make the gates findable: a `Makefile`, package scripts, or an `AGENTS.md` / `CLAUDE.md` naming the test, lint and build commands (`prototypes/ai-sdlc/README.md:84-89`).
- Committing the repo's project settings file with `enabledPlugins` is optional; a committed `.claude/settings*.json` is exactly what the headless safety check refuses to run without review (`prototypes/ai-sdlc/README.md:90-91`).
- Headless local runs use `claude -p` with `--permission-mode dontAsk`, an explicit `--allowedTools` list and `--max-budget-usd` (`plugins/dev-kit/README.md:97-101`).

## Per-repo setup for the GitHub workflow
1. Claude GitHub App — install https://github.com/apps/claude with "Only select repositories". Alternative: `/install-github-app` in a terminal `claude` session inside the repo; it also opens a starter `@claude` PR (see Gotchas).
2. Secret — `gh secret set CLAUDE_CODE_OAUTH_TOKEN -R <owner>/<repo>`, paste the token at the hidden prompt. Check with `gh secret list -R <owner>/<repo>`.
3. Actions setting — repo Settings → Actions → General → Workflow permissions: keep "Read repository contents and packages permissions", tick "Allow GitHub Actions to create and approve pull requests", Save. CLI equivalent: `gh api -X PUT repos/<owner>/<repo>/actions/permissions/workflow -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true`.
4. Labels — `gh label create "dev-kit:plan" -R <owner>/<repo> --color 1D76DB --description "dev-kit: plan this issue and open a draft PR"` and `gh label create "dev-kit:implement" -R <owner>/<repo> --color 0E8A16 --description "dev-kit: plan approved; implement, review and push"`.
5. Workflow — copy `docs/ai-sdlc/templates/dev-kit.yml` into the target repo as `dev-kit.yml` in its workflows folder, edit the three `CUSTOMISE` places (`docs/ai-sdlc/templates/dev-kit.yml:151`, `:177`, `:193`), open a PR and merge it. Issue-triggered workflows run only from the default branch, so nothing runs before the merge.
6. Smoke test — open a small issue (the S ticket in `prototypes/ai-sdlc/ticket.md` works), label it `dev-kit:plan`, read the draft PR's plan, label the PR `dev-kit:implement`, then check the recap comment and run the gate yourself.

## Customising the workflow per repo
| Repo | Dependency setup (CUSTOMISE 1) | Gate rules (CUSTOMISE 2 and 3) |
|---|---|---|
| whisk-proto-gcp | `actions/setup-python` 3.12, `actions/setup-node` 22, `make install` | `make test`, `make lint`, `backend/.venv/bin/python -m pytest`, `backend/.venv/bin/ruff check`, `npm --prefix frontend run`, `python3 -m pytest`, `python3 -m unittest` |
| whisk-studio | `actions/setup-node` 22 with npm cache, `npm ci --prefix backend`, `npm ci --prefix frontend` | `npm --prefix backend test`, `npm --prefix backend run`, `npm --prefix frontend run`, `bash scripts/check-file-length.sh` |

- Gate rules — one `Bash(<command>:*)` rule per command the plan may name as a gate; the allow-list denies chained commands (`plugins/dev-kit/README.md:99-101`).
- Budgets — `PLAN_BUDGET_USD` 3, `IMPLEMENT_BUDGET_USD` 8, `REVIEW_BUDGET_USD` 4 per run (`docs/ai-sdlc/templates/dev-kit.yml:38-40`).
- Dependency setup runs only in the `implement` job; the `plan` job reads the repo and needs none.
- Token use — dev-kit 1.3.0 runs its orchestrating turn at `effort: medium` and starts `dev-checker` and `dev-scout` without `CLAUDE.md`. Jobs pick it up through `DEV_KIT_REF` (default `main`); set it to an older branch or tag to hold a repo back.
- `/advisor` — not in the template. `--advisor opus` in an Implement step's `claude_args` would let the Sonnet orchestrator and workers consult Opus. The Opus planner and reviewer inherit it too, each call re-reads the whole transcript at Opus rates, and the tool is experimental [unverified in CI].
- `/goal` — not in the template: a person re-labels the PR between a `changes-required` review and its fix. To fix inside the same job, start the Implement prompt with the dev-kit `/goal` line from `plugins/dev-kit/README.md` and raise `IMPLEMENT_BUDGET_USD` [unverified in CI].

## Daily use of the dev-kit labels
- Plan — label an issue you opened `dev-kit:plan`. The job opens a draft PR on `dev-kit/issue-<n>` holding `.dev-kit/issue-<n>/plan.md`, comments the link on the issue and removes the label (`docs/ai-sdlc/templates/dev-kit.yml:115-117`).
- Approve — read the plan in the PR; edit it on the branch if needed; label the PR `dev-kit:implement`. The job runs `plan_tool.py approve` only after that label (`docs/ai-sdlc/templates/dev-kit.yml:165`).
- Result — the job implements, runs the gates, reviews, pushes to the PR branch, posts `recap.md` as a comment and removes the label (`docs/ai-sdlc/templates/dev-kit.yml:218`).
- Fix cycle — after a `changes-required` review, label the PR `dev-kit:implement` again; implement runs in fix mode.
- Re-plan — close the PR, delete the `dev-kit/issue-<n>` branch, label the issue again.
- CI — pushes made with `GITHUB_TOKEN` start no other workflow; re-run CI from the PR before merging.
- Merge — always yours. The `.dev-kit/issue-<n>/` run folder rides along in the PR; delete it first if `main` should not keep it.

## Invariants
- NEVER let the workflow act on another user's issue or label in a public repo: both jobs require `github.repository_owner` (`docs/ai-sdlc/templates/dev-kit.yml:50-51`, `docs/ai-sdlc/templates/dev-kit.yml:128-129`).
- Every Claude step MUST pass `--plugin-dir`, `--allowedTools` and `--max-budget-usd` in `claude_args`.
- The plan approval stays human: the `dev-kit:implement` label is the approval.
- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS: "1"` MUST stay in the workflow env (`docs/ai-sdlc/templates/dev-kit.yml:43`).
- The workflow NEVER merges, deploys or pushes to the default branch.

## Gotchas
- `zsh: command not found: claude` — `~/.local/bin` is not on the shell's PATH. Fix: run `~/.local/bin/claude`, or add the PATH line from `## One-time machine setup`.
- `/install-github-app` stored `ANTHROPIC_API_KEY` and its starter workflow uses `anthropic_api_key` — that bills the API key, not the subscription. Fix: set `CLAUDE_CODE_OAUTH_TOKEN` and use `claude_code_oauth_token:`; close the starter PR if unused (whisk-proto-gcp#2 and whisk-studio#4 were closed on 2026-11-06).
- Plan step succeeds but no `plan.md`, final message "I'll launch the planner once it finishes" — subagents start in the background by default and the Action stops at Claude's first result. Fix: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS: "1"` (https://code.claude.com/docs/en/sub-agents).
- `git push` fails with "Invalid username or token" after a Claude step — the Action points `origin` at its GitHub App token and revokes it when the step ends. Fix: `git remote set-url origin "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY.git"` and `gh auth setup-git` before pushing (`docs/ai-sdlc/templates/dev-kit.yml:103-104`).
- `gh pr create` fails with "GitHub Actions is not permitted to create or approve pull requests" — the repo setting is off by default. Fix: per-repo step 3.
- Choosing "Read and write permissions" while ticking that setting makes every workflow's default token writable. dev-kit does not need it: keep the default at read.
- A Claude step fails in about 2 seconds with `is_error: true`, USD 0 and hidden output — the Action prints Claude's output only with `show_full_output` or `ACTIONS_STEP_DEBUG`; `gh run rerun --debug` is not enough. Fix: `gh variable set DEV_KIT_DEBUG --body true -R <owner>/<repo>`, re-trigger, read the log, then `gh variable delete DEV_KIT_DEBUG -R <owner>/<repo>`; the log is public on a public repo.
- A headless session stops after one denied chained command (`&&`, `;`, `|`) — fixed in dev-kit 1.2.1, which tells every skill and agent to run one command per call. Fix: keep dev-kit at 1.2.1 or later.
- `git -C <path> diff` is denied although `Bash(git diff:*)` is allowed — the rule matches the command as written. Seen once in the 1.3.0 trial; the reviewer went on with the checker's evidence. Fix: dev-kit 1.3.0 tells its agents not to prefix commands with `cd` or `git -C`.
- GitHub rejects a workflow whose plain `run:` value contains `: ` — YAML reads it as a mapping. Fix: use `run: |`.
- Re-running a failed run reuses the workflow file from the original commit. Fix: after changing the workflow, remove and re-add the label instead of re-running.
- A headless run with a free-text prompt stops with "[dev-kit routing gate] … edits are held" — since dev-kit 1.5.0 a routed task waits for a human to lift the hold. The label workflow is unaffected: its prompts are slash commands, which are never routed, and it approves the plan before `/dev-kit:implement` (`docs/ai-sdlc/templates/dev-kit.yml:161-165`). Fix for other headless runs: set `KIT_ROUTING: off` (or `nudge`) in the step's `env`.

## Repos onboarded
| Repo | Type | Local plugin | GitHub workflow | Last end-to-end run |
|---|---|---|---|---|
| claude-skills | plugin-repo | yes | no | local trial 2026-11-06, USD 0.78 (`docs/ai-sdlc/report.md:153`) |
| resume-forge | small-scripts | yes | no | none |
| whisk-proto-gcp | web-app | yes | merged 2026-11-06 (PRs #3, #5, #6, #7) | 2026-11-06, issue #4 → PR #8, `approve`, USD 0.66 |
| whisk-studio | web-app | yes | merged 2026-11-06 (PR #5); PR #8 (open) adds Claude PR review and two cron checks, off by default | none yet [unverified] |

## Where things live
| I want to change | Path |
|---|---|
| The workflow for new repos | `docs/ai-sdlc/templates/dev-kit.yml` |
| A live repo's workflow | `dev-kit.yml` in that repo's workflows folder |
| How dev-kit plans, implements, reviews | `plugins/dev-kit/skills/plan/SKILL.md`, `plugins/dev-kit/skills/implement/SKILL.md`, `plugins/dev-kit/skills/review/SKILL.md` |
| Headless allow-list guidance | `plugins/dev-kit/README.md` |
| Why plugins-ci | `docs/ai-sdlc/adopt-plugins-ci.md` |
| The local headless trial | `prototypes/ai-sdlc/trial.sh` |
| Scheduled (cron) checks and their cost | `docs/ai-sdlc/scheduled-checks.md` |

## Maintaining this onboarding doc
- Update when a repo is onboarded or removed, when the workflow changes, when a new pitfall appears, or when a dev-kit release changes headless behaviour.
- A workflow fix goes into `docs/ai-sdlc/templates/dev-kit.yml` and into each onboarded repo's copy, then into `## Gotchas`.
- Edit this MD, then the HTML body, then run `build_html.py --rebuild docs/ai-sdlc/onboard-a-repo.html`, `check_docs.py docs/ai-sdlc/onboard-a-repo.md --repo .` and `build_index.py docs/ai-sdlc` (scripts in `plugins/docs-kit/skills/archon-document/scripts/`).
- Add a dated line to `## Change log` and bump `updated` and `source_commit`.

## Change log
- 2026-11-06 — First version. Workflow tested end to end on whisk-proto-gcp and merged in whisk-studio; starter `@claude` PRs closed; unused `ANTHROPIC_API_KEY` secrets deleted from both repos, leaving only `CLAUDE_CODE_OAUTH_TOKEN`; template added.
- 2026-11-06 — dev-kit 1.3.0: orchestrating skills at `effort: medium`, checker and scout without `CLAUDE.md`, shorter descriptions, `/goal` and advisor guidance. The template is unchanged. `prototypes/ai-sdlc/trial.sh` on 1.3.0: all phases passed, verdict `approve`, USD 0.84 against 0.78 on 1.2.1 at the same whisk-proto-gcp commit (one run each, so within run-to-run noise).
- 2026-11-07 — dev-kit 1.4.0: plans open with `## In plain words` and give each slice a `max_lines` budget; `plan_tool.py size` reports slices over budget; `review.md` adds `## In plain words`, `## Where to look` and `## Machine-checked`; every stop writes `.dev-kit/<slug>/resume.md` and ends with a decision card. The template is unchanged: its allow-lists already cover `Write(.dev-kit/**)` and `plan_tool.py` (`docs/ai-sdlc/templates/dev-kit.yml:92`).
- 2026-11-06 — whisk-studio pilot PRs #6 (backend route split and tests) and #7 (TypeScript start) merged; in PR #8 the nightly live eval and weekly drift check are gated off by default (`ENABLE_NIGHTLY_EVAL`, `ENABLE_DRIFT_CHECK`); `docs/ai-sdlc/scheduled-checks.md` added.
- 2026-11-13 — dev-kit 1.5.0 and campaign-kit 0.5.0: routing hooks (`plugins/dev-kit/hooks/route.py`) send a typed prompt to plan, investigate or a campaign proposal, and hold edits until the routed skill has run or the user says to edit directly. The template is unchanged; `KIT_ROUTING` turns routing off for other headless runs.

## Open questions
- The whisk-studio workflow has not run yet [unverified].
- The first live plan run failed in 2 seconds at USD 0 for no logged reason; it did not recur [unverified].
- Whether one Claude plan absorbs about 100 tickets a month [unverified] (`docs/ai-sdlc/adopt-plugins-ci.md:99`).
- The Action's `plugin_marketplaces` and `plugins` inputs are untested; the workflow uses `--plugin-dir` instead.
- Whether `/goal` and `--advisor` work under `anthropics/claude-code-action` [unverified].

## Sources
- `docs/ai-sdlc/templates/dev-kit.yml` — the workflow tested on whisk-proto-gcp
- `docs/ai-sdlc/adopt-plugins-ci.md:65-76` — decision and usage per project type
- `docs/ai-sdlc/report.md:142-173` — local trial runs and model versions
- `plugins/dev-kit/README.md:97-101` — headless runs and allow-lists
- `prototypes/ai-sdlc/README.md:76-91` — per-repo local setup
- https://code.claude.com/docs/en/github-actions — GitHub App, secrets, `claude setup-token`, Action inputs
- https://code.claude.com/docs/en/sub-agents — background subagents and `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS`
- https://github.com/anthropics/claude-code-action/blob/main/src/github/operations/git-config.ts — the Action's token on `origin`
- https://github.com/anthropics/claude-code-action/blob/main/base-action/src/parse-sdk-options.ts — `show_full_output` and `ACTIONS_STEP_DEBUG`
- https://github.com/adrienLamoureux/whisk-proto-gcp/pull/8 — first end-to-end run
