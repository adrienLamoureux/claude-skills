# claude-apps — fact sheet
Accessed: 2026-11-05 (every URL below was fetched on this date; local CLI is `claude` 2.1.76)

Outward step key: GH-remote = repo on GitHub; GH-App = Claude GitHub App installed on the repo; push = branch push; PR = pull request; Slack-install = Slack workspace app install; sign-up = claude.ai paid plan / account.

## Verified capabilities
- Cloud sessions (claude.ai/code, mobile Code tab, Desktop "Cloud" environment, `claude --cloud`) — available on Pro, Max, Ultra, Team, Enterprise premium seats; no separate VM charge, counts toward plan limits — https://code.claude.com/docs/en/claude-code-on-the-web — needs: sign-up (paid plan), GH-remote + GitHub connection (GH-App or `/web-setup` gh token), push for results.
- Repo without GitHub: `claude --cloud` can upload a local bundle (<100 MB, tracked files only) but the session cannot push back — https://code.claude.com/docs/en/claude-code-on-the-web — needs: sign-up; no push.
- Cloud environments (network level, env vars, setup script, network secrets, Ubuntu 24.04 VM, credentials kept outside the VM behind a proxy) — https://code.claude.com/docs/en/cloud-environments — needs: sign-up.
- Repo `CLAUDE.md`, `.claude/skills|agents|commands|rules`, `.mcp.json` and (single-repo session) `.claude/settings.json` hooks/permissions load from the clone; plugins and marketplaces declared in `.claude/settings.json` and user-level `~/.claude` do NOT load in cloud sessions — https://code.claude.com/docs/en/cloud-environments (table "what carries over") — needs: GH-remote + push to commit the files. Consequence: this repo's dev-kit/campaign-kit plugins are not usable in cloud sessions.
- Skills enabled on claude.ai are loaded automatically in cloud sessions — https://code.claude.com/docs/en/cloud-environments (row on `~/.claude/skills`) — needs: sign-up.
- Cloud scheduled tasks (formerly routines): schedule (min 1 h), API (HTTP POST with bearer token) and GitHub-event triggers; research preview; Pro/Max/Ultra/Team/Enterprise; pushes to `claude/` branches; 100 scheduled runs/h per account, 30/h per task for Run-now/API — https://code.claude.com/docs/en/routines — needs: sign-up, GH-remote, GH-App (for GitHub trigger), push.
- Desktop local scheduled tasks (run on own machine, only while app open and computer awake, optional worktree per run) — https://code.claude.com/docs/en/desktop-scheduled-tasks — needs: Desktop app + sign-up; none beyond that for local folder.
- Auto-fix of PRs (watches CI failures and review comments; needs GH-App) — https://code.claude.com/docs/en/claude-code-on-the-web — needs: GH-remote, GH-App, PR.
- Claude Code in Slack (earlier version): @Claude in channels creates a cloud session, "Create PR" button; Pro/Max/Ultra only, workspaces not connected to Claude Tag; GitHub only; the page notes the earlier bot is retired for workspaces connected to an organization — https://code.claude.com/docs/en/slack — needs: Slack-install by workspace admin, GH-remote, sign-up.
- Claude Tag (organization-wide @Claude in Slack, ephemeral sandbox, connectors, scheduled jobs, draft PRs): Public Beta, Team and Enterprise only, usage-billed from a funded balance with spend limit, no per-seat charge — https://claude.com/docs/claude-tag/overview — needs: Slack-install, Team/Enterprise plan (not a solo plan), GH-App, PR.
- Projects (one conversation coordinating parallel cloud threads, shared memory, Overview pane): public beta on Pro/Max/Ultra, not on Team/Enterprise, needs GitHub App per repo — https://code.claude.com/docs/en/claude-projects — needs: sign-up, GH-App, PR.
- Connectors / MCP in cloud sessions and scheduled tasks (all connected connectors included by default, traffic via Anthropic servers) — https://code.claude.com/docs/en/routines and https://code.claude.com/docs/en/cloud-environments — needs: sign-up; per-service OAuth for each connector.
- Desktop Code tab: Local/Cloud/SSH sessions, parallel sessions, git worktrees, PR card with CI status, auto-fix, merge-when-ready (needs `gh`) — https://code.claude.com/docs/en/desktop — needs: Desktop install + sign-up; PR features need GH-remote.
- Artifacts (claude.ai pages, Artifact tool in Claude Code) — status not verified separately this round; `enableArtifact` setting exists — https://code.claude.com/docs/en/settings (exceptions table) — unverified beyond that.
- Limits: sessions share rate limits with all other Claude usage; Pro/Max have 5-hour and weekly limits (no numeric prompt counts published) — https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan — needs: sign-up.
- Not available: cloud sessions with Bedrock/Vertex providers, with ZDR/HIPAA/CMEK orgs, or on non-GitHub remotes (no push) — https://code.claude.com/docs/en/claude-code-on-the-web.

## Scores
| Dimension | Score (1-5) | Justification | Sources |
|---|---|---|---|
| setup-effort | 4 | Connect GitHub once, install the GitHub App on each repo, add `CLAUDE.md`/`.claude/skills` and optionally a scheduled task; no workflow YAML or secrets to manage | https://code.claude.com/docs/en/web-quickstart, https://code.claude.com/docs/en/claude-code-on-the-web |
| running-cost | 4 | Flat subscription ($20-$200/month), no VM charge; usage limits are the cap, not dollars; Tag is usage-billed and Team/Enterprise only | https://claude.com/pricing, https://code.claude.com/docs/en/claude-code-on-the-web, https://claude.com/docs/claude-tag/overview |
| phase-coverage | 3 | Strong on implement/test/review via sessions, PR auto-fix and triggers; plan, intake, release, operate are partial | https://code.claude.com/docs/en/routines, https://code.claude.com/docs/en/slack |
| autonomy | 4 | Cloud schedule/API/GitHub-event triggers run with the laptop closed; but research preview, hourly run caps, interval >= 1 h | https://code.claude.com/docs/en/routines |
| human-control | 4 | Work lands on `claude/` branches and PRs, branch protection applies, diff view and session transcripts; cloud threads ignore repo permission rules and rely on auto mode | https://code.claude.com/docs/en/routines, https://code.claude.com/docs/en/claude-projects |
| multi-repo-reuse | 3 | Environments and claude.ai skills are account-level, Projects span repos, but plugins do not load in cloud sessions so per-repo `.claude/` files are copied (drift risk) | https://code.claude.com/docs/en/cloud-environments, https://code.claude.com/docs/en/claude-projects |
| isolation-security | 4 | Isolated VM per session, credentials behind a proxy, network allowlist, secrets outside sandbox; repo content leaves the machine; ZDR/HIPAA unsupported | https://code.claude.com/docs/en/claude-code-on-the-web, https://code.claude.com/docs/en/cloud-environments |
| maturity-lock-in | 2 | Scheduled tasks research preview, Projects and Claude Tag beta, API behind a dated beta header; low content lock-in (markdown/skills) but UI-configured tasks are not portable | https://code.claude.com/docs/en/routines, https://code.claude.com/docs/en/claude-projects, https://claude.com/docs/claude-tag/overview |

## Phase coverage
| Phase | Coverage (full/partial/none) | How | Sources |
|---|---|---|---|
| intake | partial | Slack @Claude (earlier bot or Tag) and connectors (issue trackers via MCP) feed tasks; no native ticket queue; GitHub issue events not verified as a trigger (PR and release events are) | https://code.claude.com/docs/en/slack, https://code.claude.com/docs/en/routines |
| plan | partial | Plan permission mode in Desktop/CLI and a plan committed to the repo then run with `--cloud`; no enforced plan-approval gate in cloud | https://code.claude.com/docs/en/claude-code-on-the-web |
| implement | full | Cloud session clones repo, edits, commits, pushes `claude/` branch, opens PR | https://code.claude.com/docs/en/claude-code-on-the-web, https://code.claude.com/docs/en/routines |
| test | full | VM has toolchains, pytest/cargo/jest run in session; setup script installs the rest | https://code.claude.com/docs/en/cloud-environments |
| review | full | GitHub-event trigger on `pull_request.opened` posts inline review; Auto-fix reacts to CI and comments | https://code.claude.com/docs/en/routines, https://code.claude.com/docs/en/claude-code-on-the-web |
| release | partial | `release` and merged-PR events can trigger tasks; merge-when-ready in Desktop; no deploy pipeline of its own (network secrets possible) | https://code.claude.com/docs/en/routines, https://code.claude.com/docs/en/desktop |
| operate | partial | Scheduled tasks and API trigger (e.g. from an alert) run recurring checks; Tag adds monitor watching but is Team/Enterprise | https://code.claude.com/docs/en/routines, https://claude.com/docs/claude-tag/overview |

## Cost and setup
Setup for one more repo (minutes):
| Step | Min | Source |
|---|---|---|
| Install Claude GitHub App on the repo (account connection done once) | 3 | https://code.claude.com/docs/en/web-quickstart |
| Commit `CLAUDE.md` + 1-3 `.claude/skills` or `agents` (copy from a template) | 10 | https://code.claude.com/docs/en/cloud-environments |
| Environment: reuse Default; add setup script if toolchain missing | 2 | https://code.claude.com/docs/en/cloud-environments |
| Create scheduled task / GitHub trigger for the repo (optional) | 5 | https://code.claude.com/docs/en/routines |
| Smoke-test one session | 5 | https://code.claude.com/docs/en/claude-code-on-the-web |
| Total | 25 | (estimate; step times are my estimates, steps are sourced) |

Monthly USD for the reference workload (100 tickets = plan + implement + review):
- Pricing basis: subscription plan (flat), not API tokens. Prices: Pro $20/month ($17 annual), Max $100/month, Ultra $200/month; Team standard seat $25/month, premium $125/month — https://claude.com/pricing. Cloud VM has no separate charge — https://code.claude.com/docs/en/claude-code-on-the-web.
- Anthropic does not publish tokens or tickets per plan, so fit is unverified. Estimate: 100 tickets/month is about 3-4 tickets/day; heavy agentic use of this size most likely needs Max ($100); Ultra ($200) as headroom; Pro ($20) probably insufficient. Cost range 100-200 USD, central 100. Over the limit, usage credits add metered overage — https://code.claude.com/docs/en/routines.
- Arithmetic: 1 solo subscription x $100 = $100 (Max), upper bound 1 x $200 = $200. Hourly run caps (100/h) are not binding at 100 tickets/month.
- Tag alternative (usage balance, Team/Enterprise) not costed: no published per-task price — https://claude.com/docs/claude-tag/overview.

## Fit per project type
- web-app: ok — cloud sessions run tests and GitHub triggers review PRs, but deploy and cloud infra access need network secrets and trusted network, and plugins/CI hooks are absent.
- small-scripts: good — no CI needed, cloud scheduled tasks or Desktop local tasks fit; sample repo must be on GitHub (or bundle with no push-back).
- plugin-repo: poor — dev-kit/campaign-kit are plugins that do not load in cloud sessions; only committed `.claude/skills|agents` would, so the repo cannot dogfood its own plugins there.

## Smallest prototype
A trial.sh for this approach cannot exercise cloud sessions, Slack, Tag or scheduled tasks: all need sign-up, GH-remote, push and/or Slack-install. Local headless trial of the cloud-session mechanics: no (installed CLI 2.1.76 shows no `--cloud` flag in `claude --help`; docs describe it and it needs a claude.ai login and GitHub). What can run locally with no outward action: a "cloud-session-equivalent" check that a repo carries everything a cloud session would load (`CLAUDE.md`, `.claude/skills`, `.mcp.json`, no plugin dependency) and a `claude -p --max-budget-usd 2` run in a `git clone --no-hardlinks` scratch copy using only those committed files, plus a README documenting the outward steps (install GitHub App, create scheduled task with prompt, GitHub trigger). Estimated cost per trial: USD 0.5-2. That tests the prompt, not the platform.

## Reference designs
Claude Tag (https://claude.com/docs/claude-tag/overview) is Anthropic's own channel-based team design; Factory-like fleets (not scored here) are covered in the agent-platform sheet.

## Open risks
- Scheduled tasks, Projects and Tag are preview/beta; limits and APIs may change (https://code.claude.com/docs/en/routines).
- Plan usage fit for 100 tickets/month is unpublished; real usage must be measured.
- Plugins not loading in cloud sessions blocks reuse of dev-kit/campaign-kit; skills must be copied into each repo or enabled at account level on claude.ai.
- Cloud threads in Projects ignore repo permission rules and hooks (https://code.claude.com/docs/en/settings, "Settings in cloud sessions").
- Repo code and secrets pass through Anthropic infrastructure; ZDR, HIPAA and CMEK orgs cannot use cloud sessions.
- Claude Tag is Team/Enterprise only; Claude Code in Slack on solo plans works only in workspaces not connected to Tag, and the earlier bot is described as retired for connected workspaces.
- Artifacts and mobile hand-off not researched in depth (https://code.claude.com/docs/en/mobile not fetched).
