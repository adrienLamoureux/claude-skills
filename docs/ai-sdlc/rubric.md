# AI-SDLC rubric

Compares three ways to run an AI-SDLC with Claude for a solo developer with many repos:
`plugins-ci` (Claude Code plugins, hooks, headless `claude -p`, GitHub Action), `agent-platform`
(Factory-like app on the Claude Agent SDK or Managed Agents) and `claude-apps` (Claude Code cloud
sessions, scheduled tasks, Slack, connectors, projects).

Merged from the three fact sheets in `docs/ai-sdlc/research/`. Facts verified online on
2026-11-05. Every cost and setup number is an **estimate**. Measured for one S ticket: USD
1.19-1.35 on 4.6 models, USD 0.78 on 5.5 models (see `docs/ai-sdlc/report.md`, `## Prototype findings`).

Scale: 1-5, 5 = best for a solo developer with many repos.

## Scores

| Dimension | plugins-ci | agent-platform | claude-apps | Sources |
|---|---|---|---|---|
| setup-effort | 4 | 2 | 3 | https://code.claude.com/docs/en/plugins/org ; https://code.claude.com/docs/en/github-actions ; https://platform.claude.com/docs/en/managed-agents/github ; https://code.claude.com/docs/en/web-quickstart ; docs/ai-sdlc/research/plugins-ci.md |
| running-cost | 4 | 2 | 4 | https://platform.claude.com/docs/en/about-claude/pricing ; https://claude.com/pricing ; https://code.claude.com/docs/en/costs ; https://code.claude.com/docs/en/agent-sdk/quickstart |
| phase-coverage | 4 | 3 | 3 | plugins/dev-kit/skills/ ; https://code.claude.com/docs/en/github-actions ; https://code.claude.com/docs/en/routines ; https://platform.claude.com/docs/en/managed-agents/overview |
| autonomy | 4 | 5 | 4 | https://code.claude.com/docs/en/github-actions ; https://code.claude.com/docs/en/headless ; https://platform.claude.com/docs/en/managed-agents/scheduled-deployments ; https://code.claude.com/docs/en/routines |
| human-control | 4 | 4 | 4 | https://code.claude.com/docs/en/hooks ; https://platform.claude.com/docs/en/managed-agents/permission-policies ; https://code.claude.com/docs/en/routines ; plugins/dev-kit/skills/plan/SKILL.md |
| multi-repo-reuse | 4 | 4 | 3 | https://code.claude.com/docs/en/plugins/org ; https://platform.claude.com/docs/en/managed-agents/scheduled-deployments ; https://code.claude.com/docs/en/cloud-environments |
| isolation-security | 3 | 4 | 4 | https://code.claude.com/docs/en/sandboxing ; https://github.com/anthropics/claude-code-action/blob/main/docs/security.md ; https://platform.claude.com/docs/en/managed-agents/environments ; https://code.claude.com/docs/en/cloud-environments |
| maturity-lock-in | 4 | 2 | 2 | https://github.com/anthropics/claude-code-action ; https://code.claude.com/docs/en/gitlab-ci-cd ; https://platform.claude.com/docs/en/managed-agents/overview ; https://code.claude.com/docs/en/routines |

### Score notes

Normalisation rule: each sheet scored only its own approach, so every row was re-read across the
three sheets on one basis and changed where the sheets disagreed with each other. "Sheet" is the
score in the fact sheet; "Here" is the score above.

- **setup-effort.** Basis: minutes to enable one more repo, plus any one-off build.
  - `plugins-ci` 4 (sheet 4): 8-13 min local-only, 18-25 min with CI; nothing to build; the
    plugin marketplace already exists in this repo. Not 5 because external-source plugins still
    need one install per machine and CI needs repo admin plus a secret.
  - `agent-platform` 2 (sheet 3, **changed**): about 30-45 min per repo, and the platform itself
    is an 8-10 developer-day build on Managed Agents or 15-20 on a self-hosted SDK loop. For a
    solo developer with 5 repos this one-off build dominates, which the sheet's own text
    acknowledged but did not score.
  - `claude-apps` 3 (sheet 4, **changed**): about 25 min per repo, which equals `plugins-ci`
    with CI, but it also requires committing `CLAUDE.md` and `.claude/skills` copies into every
    repo, because plugins do not load in cloud sessions (see the verification below).
- **running-cost.** Basis: monthly USD for 100 tickets (cost table below).
  - `plugins-ci` 4 (sheet 3, **changed**): the sheet scored only the API path (USD 200-450),
    but the same approach runs on a flat plan: local `claude -p` under a Claude login, or the
    Action with `CLAUDE_CODE_OAUTH_TOKEN`
    (https://code.claude.com/docs/en/github-actions). That puts it on the same footing as
    `claude-apps`, plus an API option.
  - `agent-platform` 2 (sheet 2): API billing only; the Agent SDK docs do not allow a claude.ai
    login for products built on it (https://code.claude.com/docs/en/agent-sdk/quickstart);
    USD 200-330 plus hosting.
  - `claude-apps` 4 (sheet 4): flat plan USD 100-200, no VM charge.
  - Sensitivity: whether one plan absorbs 100 tickets a month is **unverified** for both
    `plugins-ci` and `claude-apps` (Anthropic publishes no ticket or token counts per plan,
    https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan).
    If it does not, both drop to 3 and the API cost rows apply.
- **phase-coverage.** Basis: the Phase coverage table below, where `full` means a documented
  feature or shipped skill covers the phase with configuration only, and `partial` means you
  must write glue code or a second tool is needed. `plugins-ci` has 4 full and 3 partial,
  `claude-apps` 3 full and 4 partial, `agent-platform` 2 full and 5 partial.
  - `agent-platform` 3 (sheet 4, **changed**): the sheet scored what could be built; coverage is
    scored on what is provided.
- **autonomy.** `plugins-ci` 4 and `claude-apps` 4 as in the sheets; `agent-platform` 5 as in the
  sheet, but it assumes the intake service and session store are already built (no repo-event
  trigger is provided,
  https://platform.claude.com/docs/en/managed-agents/scheduled-deployments).
- **human-control.** All three kept at 4. Each lands work on a branch or PR for normal review;
  `agent-platform` has the strongest primitives (`always_ask`, hard budgets) but no review UI,
  which is why it does not get 5.
- **multi-repo-reuse.** `claude-apps` stays at 3. The cause is now verified in the docs: the
  repo's `enabledPlugins` and the user's plugins are not loaded in a cloud session
  (https://code.claude.com/docs/en/cloud-environments, row "Plugins and marketplaces declared in
  your repo's `.claude/settings.json`" = No). Per-repo `.claude/` copies therefore drift. This
  is a documented fact, so the 3 does not rest on an unverified claim.
- **isolation-security.** `plugins-ci` stays at 3: strong in CI (ephemeral runner, scoped token,
  base-branch config restore) but a local `claude -p` run executes the repo's hooks and
  `.mcp.json` without a trust prompt and the sandbox is off by default
  (https://code.claude.com/docs/en/headless, https://code.claude.com/docs/en/sandboxing). The
  other two get 4 for a fresh container per session; `agent-platform` loses a point for the
  `unrestricted` default network and `claude-apps` for repo content leaving the machine.
- **maturity-lock-in.** `plugins-ci` 4: plugins, hooks, `claude -p` and Action v1 are
  documented as current, and the assets are Markdown and JSON in your repo. `agent-platform` 2:
  Managed Agents is beta behind a dated header and the SDK packages are 0.x. `claude-apps` 2:
  scheduled tasks are research preview, Projects beta, Claude Tag public beta.

## Phase coverage

Cell values: `full`, `partial`, `none`.

| Phase | plugins-ci | agent-platform | claude-apps | Sources |
|---|---|---|---|---|
| intake | partial: Action fires on issues, `@claude` mentions and assignments; `/dev-kit:plan` reads an issue with `gh`; no ticket queue | partial: `sessions.create` and cron only; GitHub, Linear or Slack intake is a service you write | partial: Slack `@Claude` and MCP connectors feed tasks; no native queue; GitHub issue events not verified as a trigger | https://code.claude.com/docs/en/github-actions ; plugins/dev-kit/skills/plan/SKILL.md ; https://platform.claude.com/docs/en/managed-agents/webhooks ; https://code.claude.com/docs/en/slack |
| plan | full: `/dev-kit:plan` writes `plan.md` with contracts and slices and stops for approval | partial: you write the planner agent; `always_ask` gates tool calls, not a plan | partial: plan mode in Desktop and CLI; no enforced plan approval gate in cloud sessions | plugins/dev-kit/skills/plan/SKILL.md ; https://platform.claude.com/docs/en/managed-agents/permission-policies ; https://code.claude.com/docs/en/claude-code-on-the-web |
| implement | full: `/dev-kit:implement` workers per slice; Action `@claude` commits to a branch | full: edit and bash tools in a per-session sandbox with the repo mounted | full: cloud session clones, edits, commits and pushes a `claude/` branch | plugins/dev-kit/skills/implement/SKILL.md ; https://platform.claude.com/docs/en/managed-agents/overview ; https://code.claude.com/docs/en/claude-code-on-the-web |
| test | full: gates read from the repo are run by `dev-checker`; the Action runs the repo's tests on the runner | full: the agent runs repo test commands in the sandbox; packages pre-installed | full: the VM has toolchains and runs pytest, jest or cargo in the session | plugins/dev-kit/skills/implement/SKILL.md ; https://platform.claude.com/docs/en/managed-agents/environments ; https://code.claude.com/docs/en/cloud-environments |
| review | full: `/dev-kit:review`, `/code-review`, Action on `pull_request` | partial: you build a reviewer agent (the docs show a Code Reviewer example); merge stays in GitHub | full: `pull_request.opened` trigger posts an inline review; auto-fix reacts to CI and comments | plugins/dev-kit/skills/review/SKILL.md ; https://code.claude.com/docs/en/github-actions ; https://platform.claude.com/docs/en/managed-agents/github ; https://code.claude.com/docs/en/routines |
| release | partial: `commit-commands` plugin and Action branch and PR flow; deploy is whatever your CI does | partial: can branch, commit, push and open a PR with a scoped token; no release orchestration | partial: release and merged-PR events can trigger tasks; no deploy pipeline of its own | https://code.claude.com/docs/en/plugins/install ; https://platform.claude.com/docs/en/managed-agents/github ; https://code.claude.com/docs/en/routines |
| operate | partial: scheduled workflows and cron `claude -p` can triage or summarise; no monitoring integration | partial: scheduled deployments and webhooks run recurring checks; no incident or on-call integration | partial: scheduled tasks and the API trigger run recurring checks | https://code.claude.com/docs/en/github-actions ; https://platform.claude.com/docs/en/managed-agents/scheduled-deployments ; https://code.claude.com/docs/en/routines |

### Phase notes

Changes from the sheets, applied so all three columns use the same definition of `full`:

- **test / `plugins-ci`: partial to full.** The sheet said partial because no test-generation
  product exists. Neither do the other two approaches, which the sheets scored `full` for
  running the repo's tests. Same basis: run tests and gate on the result.
- **plan / `agent-platform`: full to partial.** Shipped planning exists only for `plugins-ci`
  (dev-kit). On Managed Agents the planner is a prompt you write, and `always_ask` gates tool
  calls, not a plan.
- **review / `agent-platform`: full to partial.** The same reasoning: a reviewer agent is
  something you build; the documented example is a template.
- **review / `claude-apps`: unchanged (full).** A `pull_request.opened` trigger posting an
  inline review is configuration only.
- Research-preview or beta status does not change a cell; it is scored under `maturity-lock-in`.

## Cost and setup

All numbers are estimates. Token volumes per ticket come from the fact sheets' own assumptions
and have not been measured. The prototype trial gives two data points for one S ticket:
USD 1.19-1.35 on 4.6 models (two runs) and USD 0.78 on 5.5 models.

| Approach | Setup minutes per new repo | Monthly USD (reference workload) | Pricing basis | Sources |
|---|---|---|---|---|
| plugins-ci | 8-25 | 200-450 | est.; API per-token pricing (Sonnet 5.5 USD 2 in / 10 out per MTok, Opus 5.5 USD 4 / 20; cache read 0.10 / 0.20). Subscription alternative USD 100-200 (Max), fit unverified | https://platform.claude.com/docs/en/about-claude/pricing ; https://claude.com/pricing ; https://code.claude.com/docs/en/costs ; docs/ai-sdlc/research/plugins-ci.md |
| agent-platform | 30-45 | 200-330 | est.; API per-token pricing plus Managed Agents runtime USD 0.08 per session-hour; no subscription plan applies | https://platform.claude.com/docs/en/about-claude/pricing ; https://code.claude.com/docs/en/agent-sdk/hosting ; docs/ai-sdlc/research/agent-platform.md |
| claude-apps | 25 | 100-200 | est.; subscription plan (Max USD 100, top tier USD 200), no VM charge; plan fit for 100 tickets unverified | https://claude.com/pricing ; https://code.claude.com/docs/en/claude-code-on-the-web ; docs/ai-sdlc/research/claude-apps.md |

### Cost notes

- Reference workload: 5 repos x 20 tickets = 100 tickets a month; each ticket is plan, implement
  and review.
- **plugins-ci setup 8-25.** 8-13 min local-only (install the plugin at project scope, commit
  `.claude/settings.json`, check gates are discoverable); 18-25 min with the GitHub Action
  (`/install-github-app` plus one workflow file). The first-ever repo adds about 30 min for the
  App, secret and marketplace.
- **plugins-ci monthly 200-450.** About USD 2.6 per ticket (range 2-4.5) x 100, from the sheet's
  token assumptions: Opus 5.5 for plan and review, Sonnet 5.5 for implement. Add 0-12 USD of
  runner minutes if CI is used on private repos (GitHub runner price unverified). Anthropic's
  own average of USD 150-250 per developer per month is for interactive use
  (https://code.claude.com/docs/en/costs).
- **agent-platform monthly 200-330.** Low case all Sonnet 5.5 (about USD 1.97 per ticket) plus
  runtime fee; high case Opus for plan and review (about USD 2.85) plus runtime and an always-on
  container (USD 36.5). The plugins-ci and agent-platform API figures differ only by token
  assumptions; at equal assumptions the API cost is the same, which is why the real gap is the
  subscription option and the build effort.
- **agent-platform one-off build:** 8-10 developer-days on Managed Agents, 15-20 on a
  self-hosted SDK loop (estimates from the sheet). Not included in the monthly figure.
- **claude-apps monthly 100-200.** One flat plan; the central case is one Max plan at USD 100.
  Over the plan's limits, usage credits add metered overage
  (https://code.claude.com/docs/en/routines).
- Prices verified 2026-11-05 on https://platform.claude.com/docs/en/about-claude/pricing:
  Sonnet 5.5 USD 2 input, 2.50 five-minute cache write, 0.10 cache read, 10 output; Opus 5.5
  USD 4, 5, 0.20, 20 per MTok; Managed Agents session runtime USD 0.08 per session-hour.

## Verification log

- **Claim: plugins enabled in a repo's `.claude/settings.json` do not load in Claude Code cloud
  sessions. Result: verified, documented.**
  - https://code.claude.com/docs/en/cloud-environments, "what carries over" table: "Plugins and
    marketplaces declared in your repo's `.claude/settings.json`" is `No`, and "Plugins enabled
    only in your user settings" is `No`.
  - https://code.claude.com/docs/en/plugins/install, Cloud session tab: a cloud session "has no
    plugin browser and doesn't load the plugins you installed on your own machine or the ones
    your repository's `.claude/settings.json` turns on". Organization-distributed plugins go
    through managed settings (https://code.claude.com/docs/en/plugins/org).
  - Both pages fetched on 2026-11-05. The earlier "inferred" status in the claude-apps sheet is
    resolved.
