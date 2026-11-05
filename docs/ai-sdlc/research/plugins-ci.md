# plugins-ci — fact sheet

Accessed: 2026-11-05 (every https:// URL below was fetched on this date; local CLI is `claude` 2.1.76)

Approach A: Claude Code plugins/skills/agents/hooks, headless `claude -p`, the Claude Code GitHub Action (`anthropics/claude-code-action`), GitLab CI/CD, and how this repo's `dev-kit` and `campaign-kit` fit.

## Verified capabilities

- Plugin = directory of skills, agents, hooks, MCP/LSP servers (and "mods"); manifest `.claude-plugin/plugin.json` — GA (documented, no beta label) — https://code.claude.com/docs/en/plugins
- Marketplaces: a git repo/URL/dir with `.claude-plugin/marketplace.json`; install with `claude plugin install <p>@<marketplace> [--scope user|project|local]` — GA — https://code.claude.com/docs/en/plugins/install
- Per-repo enablement: `enabledPlugins` and `extraKnownMarketplaces` in the repo's `.claude/settings.json`; `extraKnownMarketplaces` only applies in a trusted folder (interactive after trust dialog; in `-p` only if trust was already accepted or `hasTrustDialogAccepted` is set in `~/.claude.json`); plugins whose marketplace entry points at an external source still need `claude plugin install ... --scope project` — GA — https://code.claude.com/docs/en/plugins/org
- CI plugin seeding: `CLAUDE_CODE_PLUGIN_SEED_DIR`, `CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1` makes a `-p` run wait for plugin install — GA — https://code.claude.com/docs/en/plugins/org
- Cloud sessions do NOT load locally installed plugins or the repo's `enabledPlugins` — documented — https://code.claude.com/docs/en/plugins/install (belongs to approach C; noted here as a boundary)
- Headless `claude -p`: `--output-format text|json|stream-json`, `--json-schema` (field `structured_output`), `--allowedTools`, `--permission-mode` (acceptEdits, dontAsk, auto, plan...), `--permission-prompts none` (v2.1.259+), `--continue`/`--resume`, `--bare` (recommended for scripts; skips hooks/plugins/CLAUDE.md discovery, needs `ANTHROPIC_API_KEY`), exit code 0 on success; `--output-format json` returns `total_cost_usd` and per-model breakdown (client-side estimate) — GA — https://code.claude.com/docs/en/headless
- `--max-budget-usd` (print mode only), `--plugin-dir`, `--agents`, `--mcp-config`, `--max-turns` (via `claude_args`) — present in local `claude --help` 2.1.76: `--max-budget-usd <amount> Maximum dollar amount to spend on API calls (only works with --print)`, `--plugin-dir <path>`, `--permission-mode`, `--output-format`, `--json-schema`, `--no-session-persistence` — GA — local command `claude --help`; flag documented at https://code.claude.com/docs/en/headless
- `claude plugin validate <path>` validates a plugin or marketplace manifest — GA — local: `claude plugin validate .` in this repo printed `Validation passed`
- `claude plugin eval` runs plugin eval suites (used by `.github/workflows/evals.yml` with `--max-cost-usd`) — GA (used in repo; not re-fetched from docs) — repo path `.github/workflows/evals.yml`, https://code.claude.com/docs/en/plugin-evals
- Hooks: 20+ events incl. `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `TaskCompleted`; types `command`, `http`, `mcp_tool`, `prompt`, `agent` (agent type "experimental"); exit 2 blocks on blocking events; `onFailure: "block"` (v2.1.295+) fails closed; configurable in settings, plugin `hooks/hooks.json`, skill/agent frontmatter — GA (agent hook type: experimental) — https://code.claude.com/docs/en/hooks
- Hooks do not run in `--bare` mode when passed via `--settings` or a `--plugin-dir` plugin — documented — https://code.claude.com/docs/en/headless
- Sandbox: OS-enforced Bash sandbox (macOS Seatbelt, Linux/WSL2 bubblewrap), network via allowlist proxy; OFF by default, enable with `/sandbox` or `sandbox.enabled: true` — GA — https://code.claude.com/docs/en/sandboxing
- Claude Code GitHub Action `anthropics/claude-code-action@v1`: interactive mode (`@claude` mention) and automation mode (`prompt` input, any GitHub event incl. `schedule`, `issues`, `pull_request`); `prompt` can be a skill call such as `/plugin:skill`; plugins via `plugin_marketplaces` + `plugins` inputs; `claude_args` passes any CLI flag; MIT license; v1 is current (README does not label beta, beta -> v1 migration guide exists) — GA (v1) — https://code.claude.com/docs/en/github-actions , https://github.com/anthropics/claude-code-action
- Action auth: `ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN` (subscription token from `claude setup-token`, Pro/Max/Ultra/Team/Enterprise), workload identity federation, Bedrock/Vertex/Foundry via OIDC; org-level secret recommended to be an API key — GA — https://code.claude.com/docs/en/github-actions
- Action safety: write-access check on triggering user, bots blocked unless `allowed_bots`, no automatic PRs by default (commits to a branch with a link), restores `.claude/`, `CLAUDE.md`, `.mcp.json` from base branch on PRs — GA — https://github.com/anthropics/claude-code-action/blob/main/docs/security.md
- Quick setup `/install-github-app` (github.com only; installs the Claude GitHub App, stores secret, opens a PR with workflow files; needs repo admin) — GA — https://code.claude.com/docs/en/github-actions
- Claude GitHub App is shared by Action, Code Review and web auto-fix; requests 13 permissions incl. Contents/Issues/PR read-write, Workflows read-write — GA — https://code.claude.com/docs/en/github-actions
- Claude Code GitLab CI/CD: `claude -p` job in `.gitlab-ci.yml`, masked `ANTHROPIC_API_KEY`; "currently in beta", maintained by GitLab — beta — https://code.claude.com/docs/en/gitlab-ci-cd
- Managed Code Review product (Anthropic infrastructure, Team/Enterprise plans, GitHub only, never blocks/approves) — available, plan-gated, NOT usable on Pro/Max solo plans — https://code.claude.com/docs/en/code-review
- `/code-review` local command and Ultrareview exist on any plan / claude.ai sign-in — https://code.claude.com/docs/en/code-review
- Cost reference: average ~$13 per developer per active day, $150-250 per developer per month, 90% of users below $30 per active day; agent teams use ~7x tokens — https://code.claude.com/docs/en/costs

## Scores

Scale: 5 = best for a solo developer with many repos.

| Dimension | Score (1-5) | Justification | Sources |
|---|---|---|---|
| setup-effort | 4 | Local-only: one `claude plugin install dev-kit@adrien-skills --scope project` plus committing `.claude/settings.json` (about 8-13 min incl. checking gates). With CI: `/install-github-app` + one workflow file (about 18-25 min). Gates are read from the repo, nothing hard-coded. Not 5: external-source plugins need an install per machine, and CI needs repo admin and a secret. | https://code.claude.com/docs/en/plugins/org , https://code.claude.com/docs/en/github-actions , plugins/dev-kit/skills/plan/SKILL.md |
| running-cost | 3 | API tokens only, no platform fee: estimated 200-450 USD/month for 100 tickets (see Cost and setup), plus GitHub runner minutes. Subscription tokens can be used in the Action (OAuth) which could cap cost at 100-200 USD flat but usage limits at this volume are unverified. | https://platform.claude.com/docs/en/about-claude/pricing , https://code.claude.com/docs/en/costs , https://claude.com/pricing |
| phase-coverage | 4 | plan, implement, review are full via dev-kit; intake, test, release, operate partial (see Phase coverage). Nothing for deploy/monitoring. | plugins/dev-kit/skills/ , plugins/campaign-kit/skills/ , https://code.claude.com/docs/en/github-actions |
| autonomy | 4 | Action runs on `issues`, `pull_request`, `schedule`, `workflow_dispatch` with no human; `claude -p` with `--permission-mode`/`--permission-prompts none`/`--max-budget-usd` runs unattended anywhere (cron, any CI). Not 5: no built-in queue/retry/fleet; schedules need a GitHub default branch; each run is a single job. | https://code.claude.com/docs/en/github-actions , https://code.claude.com/docs/en/headless |
| human-control | 4 | Work lands as branches/commits you review in a normal PR; Action never opens PRs by default; permission modes, `PreToolUse` hooks with exit 2 and `onFailure: "block"` gate actions; dev-kit stops for plan approval; `git revert` is the rollback. No central dashboard of runs beyond GitHub UI and run logs. | https://code.claude.com/docs/en/hooks , https://github.com/anthropics/claude-code-action/blob/main/docs/security.md , plugins/dev-kit/skills/plan/SKILL.md |
| multi-repo-reuse | 4 | One marketplace repo is the single source of skills/agents/hooks, versioned and auto-updatable; per repo you add a settings entry and optionally a workflow (or a reusable workflow + org-level secret/App). Residual per-repo drift: the workflow file and settings copy. | https://code.claude.com/docs/en/plugins/org , https://code.claude.com/docs/en/github-actions , .claude-plugin/marketplace.json |
| isolation-security | 3 | CI path is good (ephemeral GitHub runner, least-privilege `permissions:`, tokens scoped to the repo, base-branch config restore, no auto PR). Local headless path runs with the user's privileges, sandbox is off by default, and a project's `.claude/settings.json` hooks and `.mcp.json` run under `-p` without trust prompt unless `--bare`. Plugins run as the user. | https://code.claude.com/docs/en/sandboxing , https://code.claude.com/docs/en/headless , https://github.com/anthropics/claude-code-action/blob/main/docs/security.md |
| maturity-lock-in | 4 | Plugins, hooks, `claude -p`, Action v1 documented as current, MIT-licensed Action; assets are Markdown/JSON in your repo and portable. Risks: fast-moving CLI flags and hook events (version gates like v2.1.295), GitLab integration is beta, Action README has no explicit GA label. | https://code.claude.com/docs/en/gitlab-ci-cd , https://github.com/anthropics/claude-code-action , https://code.claude.com/docs/en/hooks |

## Phase coverage

| Phase | Coverage (full/partial/none) | How | Sources |
|---|---|---|---|
| intake | partial | Action triggers on issues, `@claude` comments, assignments; `/dev-kit:plan` accepts issue URL or `#n` via `gh issue view`. No triage board, no automatic ticket-to-task queue. | https://code.claude.com/docs/en/github-actions , plugins/dev-kit/skills/plan/SKILL.md |
| plan | full | `/dev-kit:plan`: Sonnet scout + Opus planner write `plan.md` with frozen contracts, path-owned slices, gates, merge order; stops for approval. `campaign-kit` plans multi-round work. | plugins/dev-kit/skills/plan/SKILL.md , plugins/campaign-kit/skills/campaign/SKILL.md |
| implement | full | `/dev-kit:implement`: Sonnet workers per slice in waves with checker; Action `@claude` implements changes and commits to a branch. | plugins/dev-kit/skills/implement/SKILL.md , https://code.claude.com/docs/en/github-actions |
| test | partial | Gates (tests, lint) are read from repo scripts/CI and run by `dev-checker`; hooks can run tests on `Stop`/`PostToolUse`; no test-generation or flaky-test management product. | plugins/dev-kit/skills/implement/SKILL.md , https://code.claude.com/docs/en/hooks |
| review | full | `/dev-kit:review` (Opus judge, approve/changes-required/blocked), `/code-review`, Action running `code-review` plugin on `pull_request`, optional managed Code Review on Team/Enterprise. | plugins/dev-kit/skills/review/SKILL.md , https://code.claude.com/docs/en/github-actions , https://code.claude.com/docs/en/code-review |
| release | partial | `commit-commands` plugin (commit, push, PR) and Action branch/PR flow; no deploy/rollout/changelog orchestration in dev-kit; deploy is whatever your existing CI does. | https://code.claude.com/docs/en/plugins/install , ROADMAP.md , https://github.com/anthropics/claude-code-action/blob/main/docs/security.md |
| operate | partial | Scheduled workflows (`schedule` trigger, e.g. daily report) and headless cron runs can triage or summarise; no incident/monitoring integration out of the box. | https://code.claude.com/docs/en/github-actions , https://code.claude.com/docs/en/headless |

## Cost and setup

Pricing basis: API per-token pricing (primary), subscription plan (alternative). Source for prices: https://platform.claude.com/docs/en/about-claude/pricing — Claude Sonnet 5.5 input 2 USD/MTok, cache read 0.10, output 10; Claude Opus 5.5 input 4, cache read 0.20, output 20. Plans: https://claude.com/pricing — Pro 20 USD/month (17 annual), Max 5x 100, Max 20x 200 ("Ultra" label on page), Team standard seat 25 monthly.

Setup steps for one more repo (solo, minutes):

| Step | Minutes |
|---|---|
| 1. `claude plugin install dev-kit@adrien-skills --scope project` (marketplace added once per machine) and commit `.claude/settings.json` with `enabledPlugins` | 3 |
| 2. Make sure gates are discoverable (AGENTS.md / CLAUDE.md / package scripts) | 5-10 |
| 3. Optional CI: `/install-github-app` (or reuse org-level App + secret) | 5 |
| 4. Optional CI: copy workflow (`claude.yml`, `prompt: /dev-kit:plan ...`, `plugins:` input), set `--max-turns`, permissions | 5-7 |
| Total local-only | 8-13 |
| Total with CI | 18-25 (first-ever repo about 30 more for App, secret, marketplace) |

Monthly USD for the reference workload (5 repos x 20 tickets = 100 tickets; each ticket = plan + implement + review). Per-ticket tokens are my estimate (unverified, no measurement yet): Opus 5.5 planner+reviewer about 0.6M cache-read + 0.1M fresh input + 40k output = 0.12 + 0.40 + 0.80 = 1.32 USD; Sonnet 5.5 implementer+checker about 1.5M cache-read + 0.2M fresh input + 60k output + 50k cache write = 0.15 + 0.40 + 0.60 + 0.125 = 1.28 USD; ticket total about 2.6 USD, range 2-4.5 USD for small to multi-slice tickets.

- API: 100 x 2-4.5 = 200-450 USD/month (central 260). Cross-check: Anthropic's own average of 150-250 USD per developer per month for interactive use (https://code.claude.com/docs/en/costs); 100 autonomous tickets is a heavier load than that average.
- GitHub Actions minutes (if CI used): 100 runs x about 15 min = 1,500 min; free for public repos, otherwise billed per GitHub's rates (not fetched; unverified), assume 0-12 USD.
- Subscription alternative: Max 20x at 200 USD/month if run locally or via `CLAUDE_CODE_OAUTH_TOKEN`; whether it absorbs 100 tickets is unverified (plan limits not measured).
- Number used for the rubric: 200-450 USD/month.

## Fit per project type

- web-app: good — multi-area tickets suit dev-kit slices and CI gates; Action posts to PR and runs existing tests on the runner.
- small-scripts: good — local `claude -p` or just interactive use; no CI needed (8-13 min setup, no workflow file).
- plugin-repo: good — this repo already does it: `claude plugin validate`, `evals.yml` workflow, `--plugin-dir` loading for trials (.github/workflows/evals.yml, scripts/validate.sh).

## Smallest prototype

What `prototypes/ai-sdlc/trial.sh` would do: clone the sample repo with `git clone --no-hardlinks`, then run three headless calls with the repo's own plugin loaded read-only: `claude -p "/dev-kit:plan <ticket>" --plugin-dir plugins/dev-kit --permission-mode acceptEdits --output-format json --max-budget-usd 2`, then `/dev-kit:implement`, then `/dev-kit:review`, each in the clone (cwd = clone; `--add-dir` for the plugin if needed), parsing `total_cost_usd` and summing; compute `changed_files` from `git -C clone diff --name-only <start-sha>`; write `trial-result.json`. Outward step documented but not executed: the equivalent GitHub workflow (`claude-code-action@v1` with `plugins: dev-kit@adrien-skills`, `prompt: /dev-kit:plan ...`).

- Local headless trial with no push/PR/deploy/sign-up: yes — only needs the existing local Claude login/API access (no new service); `--plugin-dir` is read-only and `--max-budget-usd` caps spend. Caveat: uses existing paid access already on this machine; not verified by a run in this lane (a run costs tokens, not executed).
- Risks to check in the spike: skills that spawn subagents under `-p`; `/skill` expansion in `-p` is documented ("User-invoked skills ... include `/skill-name` in the prompt string", https://code.claude.com/docs/en/headless); `--permission-mode acceptEdits` plus `--allowedTools "Bash(...)"` needed for gate commands.
- Estimated cost per run: 1.5-4 USD for a small plan+implement+review ticket (estimate; one `--max-budget-usd 5` cap on the whole trial; split per-phase caps).

## Reference designs

Not scored. Factory (factory.ai) and similar vendor droids are comparable to approach B, not A; no vendor facts used here. GitHub Copilot coding agent / GitLab Duo: not researched.

## Open risks

- Per-ticket token estimates are unmeasured; real cost could be 2x either way. Round 2/3 trial gives one data point.
- `claude -p` runs a repo's `.claude/settings.json` hooks and `.mcp.json` without a trust prompt unless `--bare` (https://code.claude.com/docs/en/headless); `--bare` skips plugin/hook discovery except via flags, and hooks from `--plugin-dir` do not run under `--bare`. Pick one per environment.
- Plugin enabled in project settings still needs per-machine install for external-source plugins; `extraKnownMarketplaces` ignored in untrusted folders and in `-p` unless trust was pre-accepted (https://code.claude.com/docs/en/plugins/org).
- Action posts/pushes use the shared Claude GitHub App with 13 permissions; a custom GitHub App is the least-privilege alternative (https://code.claude.com/docs/en/github-actions).
- Public-repo scheduled workflows are disabled after 60 days without activity (https://code.claude.com/docs/en/github-actions).
- GitHub does not trigger workflows on commits made with the default `GITHUB_TOKEN`, so CI may not run on Claude's pushes unless the App token is used (https://code.claude.com/docs/en/github-actions).
- Models named in docs change fast (Sonnet 5.5 / Opus 5.5 at time of writing); cost figures must be recomputed when defaults change.
- Not verified: GitHub-hosted runner price per minute; subscription limits for 100 tickets/month; `claude plugin eval` details beyond repo usage.
