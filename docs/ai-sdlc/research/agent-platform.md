# agent-platform — fact sheet
Accessed: 2026-11-05 (every URL below was fetched on this date; `docs.claude.com/en/api/agent-sdk/overview` answered 301 to `platform.claude.com/docs/en/api/agent-sdk/overview`, which answered 307 to `code.claude.com/docs/en/agent-sdk/overview`. Managed Agents and pricing docs live on `platform.claude.com`, the canonical host of Anthropic's API docs.)

Approach B = a Factory-like standalone platform you build on the Claude Agent SDK (self-hosted loop) or on Claude Managed Agents (Anthropic-hosted loop). "Estimate" marks my own numbers, not vendor claims.

## Verified capabilities

- Claude Agent SDK (Python `claude-agent-sdk`, TypeScript `@anthropic-ai/claude-agent-sdk`): library that runs the Claude Code binary and exposes built-in tools, hooks, subagents, MCP, permissions, sessions, skills/commands/memory loaded from `.claude/`, plugins — GA-style public packages but pre-1.0 (npm 0.3.318 modified 2026-11-04; PyPI 0.2.178, Python >= 3.10) — outward step: none to use it (needs an API key to call the model) — https://code.claude.com/docs/en/agent-sdk/overview ; local check `npm view @anthropic-ai/claude-agent-sdk version` printed `0.3.318`; PyPI JSON printed `0.2.178 >=3.10`.
- Agent SDK auth: `ANTHROPIC_API_KEY`, or Bedrock / Claude Platform on AWS / Vertex / Foundry env flags; docs state third parties may not offer claude.ai login or its rate limits in products built on the SDK (API-key billing is the supported path) — https://code.claude.com/docs/en/agent-sdk/quickstart
- Agent SDK cost control: result message carries `total_cost_usd` (client-side estimate, not billing) and per-model `modelUsage`; `max_budget_usd` / `maxBudgetUsd` caps one call; `max_turns` bounds turns — https://code.claude.com/docs/en/agent-sdk/cost-tracking , https://code.claude.com/docs/en/agent-sdk/hosting
- Agent SDK hosting model: each session is one `claude` CLI subprocess owning shell, cwd and JSONL transcripts; patterns ephemeral / long-running / hybrid / multi-agent container; `SessionStore` adapter mirrors transcripts to durable storage; OTEL telemetry via env vars; starting size 1 GiB RAM, 5 GiB disk, 1 CPU per agent; minimal container about USD 0.05/hour; no top-level session timeout — https://code.claude.com/docs/en/agent-sdk/hosting
- Agent SDK isolation options: sandbox-runtime (bubblewrap / sandbox-exec), Docker hardened flags, gVisor, Firecracker, credential-injecting proxy via `ANTHROPIC_BASE_URL` / `HTTPS_PROXY`; recommended pattern keeps credentials outside the agent boundary — https://code.claude.com/docs/en/agent-sdk/secure-deployment , https://github.com/anthropics/sandbox-runtime
- Claude Managed Agents (hosted agent harness: agent, environment, session, events): **beta**, requires header `managed-agents-2026-04-01` (SDK sets it), enabled by default for all API accounts, behaviours "may be refined between releases"; not eligible for Zero Data Retention or HIPAA BAA; also on Claude Platform on AWS and Claude Models on Google Cloud (Anthropic managed) — outward step: Claude Console account + API key (sign-up) — https://platform.claude.com/docs/en/managed-agents/overview
- Managed Agents cloud sandbox: fresh Linux container per session, `packages` pre-install (apt, cargo, gem, go, npm, pip), `limited` networking with `allowed_hosts` and `allow_package_managers`; a create request that omits `networking` gets `unrestricted` — beta — https://platform.claude.com/docs/en/managed-agents/environments
- Managed Agents self-hosted sandboxes: `self_hosted` environment is a work queue served by your own worker (`ant beta:worker poll`, SDK workers; Cloudflare, Daytona, E2B, Modal, Vercel, Fly.io, GKE guides); tool I/O still flows to Anthropic; `github_repository` and `file` resources are rejected on self-hosted — beta — https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes
- Managed Agents GitHub access: `github_repository` session resource mounts a repo (clone cached across sessions), optional `authorization_token` (fine-grained PAT advised), GitHub MCP (`https://api.githubcopilot.com/mcp/`) lets the agent branch, commit, push, open PRs; repos load `.claude/skills` from repo root — beta — outward step: GitHub token + push/PR on a remote — https://platform.claude.com/docs/en/managed-agents/github
- Managed Agents scheduled deployments: cron schedule + timezone, minute granularity, jitter up to 9 min, per-run `budget`, run history, manual `run`, pause/unpause; max 1,000 per organization; no repo-event trigger (event intake must be your own service) — requires the `managed-agents-2026-04-01` beta header (the page lists status "Available" for Managed Agents, the parent product is beta) — https://platform.claude.com/docs/en/managed-agents/scheduled-deployments
- Managed Agents webhooks: outbound only (Anthropic to your HTTPS endpoint) for session, deployment, vault, agent events; payload carries type and id only, 3 attempts then dropped, signed `whsec_` secret — beta — https://platform.claude.com/docs/en/managed-agents/webhooks
- Managed Agents permission policies: `always_allow` (agent toolset default), `always_ask` (MCP default; session pauses until `user.tool_confirmation`), `auto` (server evaluates; "not a human checkpoint") — beta — https://platform.claude.com/docs/en/managed-agents/permission-policies
- Managed Agents session budgets: hard USD cap per session at list rates (cents, string), pauses with `budget_reached`, one in-flight request can overshoot; add-after-create rejected — beta — https://platform.claude.com/docs/en/managed-agents/budgets
- Managed Agents vaults: register credentials once, reference by id per session; `mcp_oauth` / `static_bearer` injected on MCP calls, `environment_variable` credentials held as opaque placeholders in the sandbox and substituted at egress; env-var credentials not yet supported on self-hosted sandboxes — beta header — https://platform.claude.com/docs/en/managed-agents/vaults
- Managed Agents rate limits: 300 create requests/min and 1,200 read requests/min per organization — beta — https://platform.claude.com/docs/en/managed-agents/reference
- Pricing: Managed Agents bills tokens at model list price plus USD 0.08 per session-hour of `running` time (idle not billed, replaces container-hour billing); web search USD 10 per 1,000; no batch discount — https://platform.claude.com/docs/en/about-claude/pricing
- Reference design, not scored: Factory documents Droid (CLI, desktop, web/mobile, cloud sessions), Automations (triage, code review, QA, docs, incident response), Workstreams (orchestrator over parallel agents), API for sessions/analytics, enterprise deployment; pricing not shown on the fetched page — https://docs.factory.com/ (vendor page, `docs.factory.ai` 308 redirect)

## Scores

Scale: 5 = best for a solo developer with many repos. Scores judge the platform you would build/operate, on Managed Agents where it differs from the SDK path.

| Dimension | Score (1-5) | Justification | Sources |
|---|---|---|---|
| setup-effort | 3 | After the platform exists, one more repo = map repo to environment/agent, mint a scoped GitHub token, set test/packages, smoke ticket: about 35 min (estimate). The platform itself is a one-off build of about 8-10 developer-days on Managed Agents or 15-20 on a self-hosted SDK loop (estimate), which a solo dev with 5 repos must also amortise, hence 3 not 4. | https://platform.claude.com/docs/en/managed-agents/github ; https://platform.claude.com/docs/en/managed-agents/environments ; https://code.claude.com/docs/en/agent-sdk/hosting |
| running-cost | 2 | API-token billing only (SDK may not use a claude.ai subscription for products); about USD 200-330/month for 100 tickets (arithmetic in Cost and setup) vs flat-rate plans; plus runtime USD 0.08/h and hosting up to about USD 36/month always-on. | https://platform.claude.com/docs/en/about-claude/pricing ; https://code.claude.com/docs/en/agent-sdk/quickstart ; https://code.claude.com/docs/en/agent-sdk/hosting |
| phase-coverage | 4 | Anything can be built: plan, implement, test, review, release steps run in the agent loop; intake, release gating and operate need your own services. Nothing is covered out of the box except the loop and sandbox. | https://platform.claude.com/docs/en/managed-agents/overview ; https://platform.claude.com/docs/en/managed-agents/scheduled-deployments |
| autonomy | 5 | Scheduled deployments (cron), webhooks to react to idle/budget/failed runs, long-running stateful sessions, per-run budgets; SDK path runs headless in containers. | https://platform.claude.com/docs/en/managed-agents/scheduled-deployments ; https://platform.claude.com/docs/en/managed-agents/webhooks ; https://code.claude.com/docs/en/agent-sdk/hosting |
| human-control | 4 | `always_ask` gate with `user.tool_confirmation`, interrupt/steer, hard session budgets, persisted event history with `evaluated_permission` audit; but no review UI or dashboard is provided (build it) and `auto` is not a human gate. | https://platform.claude.com/docs/en/managed-agents/permission-policies ; https://platform.claude.com/docs/en/managed-agents/budgets ; https://platform.claude.com/docs/en/managed-agents/reference |
| multi-repo-reuse | 4 | Agent, environment and deployment are config objects applied with `ant apply` and `claude-lock.json`; repos attach per session as resources and bring their own `.claude/skills`; per-repo tokens must be managed (vaults are workspace-scoped). | https://platform.claude.com/docs/en/managed-agents/scheduled-deployments ; https://platform.claude.com/docs/en/managed-agents/github ; https://platform.claude.com/docs/en/managed-agents/vaults |
| isolation-security | 4 | Fresh container per session, host allowlist networking, placeholder-substitution of env secrets, self-hosted option, documented proxy/gVisor/Firecracker hardening; minus: omitted `networking` defaults to `unrestricted`, `limited` hosts still allow `git push` to allowed hosts, not ZDR/HIPAA eligible. | https://platform.claude.com/docs/en/managed-agents/environments ; https://platform.claude.com/docs/en/managed-agents/vaults ; https://code.claude.com/docs/en/agent-sdk/secure-deployment |
| maturity-lock-in | 2 | Managed Agents is beta with a dated beta header and behaviour changes allowed; Agent SDK versions are 0.x (npm 0.3.318, PyPI 0.2.178); Anthropic-only; lock-in partly eased because the SDK drives the same Claude Code loop as `claude -p`. | https://platform.claude.com/docs/en/managed-agents/overview ; https://code.claude.com/docs/en/agent-sdk/overview ; repo path `docs/ai-sdlc/research/agent-platform.md` (local `npm view` and PyPI output recorded in the lane report) |

## Phase coverage

| Phase | Coverage (full/partial/none) | How | Sources |
|---|---|---|---|
| intake | partial | Primitives only: scheduled deployments (cron) and `ant`/API session creation; ticket intake from GitHub issues, Linear or Slack is a service you write (webhooks are outbound-only, so you receive GitHub/Linear events yourself and call `sessions.create`). | https://platform.claude.com/docs/en/managed-agents/scheduled-deployments ; https://platform.claude.com/docs/en/managed-agents/webhooks |
| plan | full | Agent with system prompt and skills (loaded from repo `.claude/skills`) or SDK subagents plans in a read-only toolset; `always_ask` can hold the plan for approval. | https://platform.claude.com/docs/en/managed-agents/github ; https://code.claude.com/docs/en/agent-sdk/overview |
| implement | full | Bash, file edit, glob, grep in a per-session sandbox with the repo mounted; SDK equivalent in a container. | https://platform.claude.com/docs/en/managed-agents/overview ; https://code.claude.com/docs/en/agent-sdk/overview |
| test | full | Agent runs the repo test commands in the sandbox; `packages` and `allow_package_managers` give dependencies; `user.define_outcome` events with outcome-evaluation spans let the agent iterate until satisfied (event types listed in the reference; the outcomes guide page itself was not fetched). | https://platform.claude.com/docs/en/managed-agents/environments ; https://platform.claude.com/docs/en/managed-agents/reference |
| review | full | A separate reviewer agent can read the diff via GitHub MCP (the docs' own example is a "Code Reviewer" agent); human approval via `user.tool_confirmation`; merge decision stays in GitHub. | https://platform.claude.com/docs/en/managed-agents/github ; https://platform.claude.com/docs/en/managed-agents/permission-policies |
| release | partial | Agent can create branch, commit, push and open a PR with a scoped token; deploys need credentials in vaults and allowed hosts, and no release/changelog orchestration is built in. | https://platform.claude.com/docs/en/managed-agents/github ; https://platform.claude.com/docs/en/managed-agents/vaults |
| operate | partial | Scheduled deployments can run recurring health/dependency/triage agents and webhooks report failures; no incident, alert or on-call integration is provided. | https://platform.claude.com/docs/en/managed-agents/scheduled-deployments ; https://platform.claude.com/docs/en/managed-agents/webhooks |

## Cost and setup

### Setup for one more repo (platform already built; estimate)

| Step | Minutes |
|---|---|
| Install or authorise a fine-grained GitHub token / GitHub App on the repo (clone + PR scopes) and store it in a vault or secret store | 8 |
| Add repo to the platform's repo registry (environment, agent, model, budget, label routing) | 7 |
| Set environment `packages`, test command, `allowed_hosts` (or confirm defaults) | 10 |
| Add `CLAUDE.md` / `.claude/skills` pointers to the repo if missing | 5 |
| Smoke ticket end to end and check budget/permission behaviour | 10 |
| **Total per new repo** | **40** (range 30-45) |

### One-off build of the platform (estimate, developer-days)

| Component | Managed Agents path | Self-hosted SDK path |
|---|---|---|
| Ticket intake service (GitHub issues/labels to session; Linear optional) | 1.5 | 1.5 |
| Agent/environment/deployment config as code (`ant apply`) | 0.5 | n/a (own config) |
| Sandbox per task (cloud env vs container + gVisor/sandbox-runtime) | 0.5 | 3 |
| Secrets/credential handling (vaults vs egress proxy) | 1 | 2 |
| Session store, queue, retries, concurrency | 0.5 | 3 |
| Review/approval gate and PR flow | 1.5 | 2 |
| Dashboard (list sessions, cost, status) | 2 | 3 |
| Observability and cost alerts (webhooks/`session.usage`, OTEL) | 0.5 | 1.5 |
| Hosting, CI, tests | 1.5 | 2.5 |
| **Total** | **9.5 (range 8-10)** | **18.5 (range 15-20)** |

### Monthly USD for the reference workload (5 repos x 20 tickets = 100 tickets; each ticket = plan + implement + review)

Pricing basis: Claude API per-token pricing plus Managed Agents runtime fee. No subscription plan applies (SDK terms). Source: https://platform.claude.com/docs/en/about-claude/pricing (Sonnet 5.5: input USD 2, 5m cache write 2.50, cache read 0.10, output 10 per MTok; Opus 5.5: 4 / 5 / 0.20 / 20; Managed Agents runtime USD 0.08 per session-hour).

Token assumptions per ticket (estimate, in thousands; uncached input / cache write / cache read / output): plan 40/80/300/15, implement 80/150/1500/40, review 40/80/400/10. A real trial in round 3 should replace these.

- All Sonnet 5.5: plan 0.08+0.20+0.03+0.15 = 0.46; implement 0.16+0.375+0.15+0.40 = 1.085; review 0.08+0.20+0.04+0.10 = 0.42; total about USD 1.97 per ticket, x100 = **USD 196.5**.
- Opus 5.5 for plan and review, Sonnet 5.5 for implement: about USD 2.85 per ticket, x100 = **USD 284.5**.
- Managed Agents runtime: 100 tickets x 3 sessions x 0.25 h x USD 0.08 = **USD 6** (estimate of 0.25 h running time per session).
- Hosting for intake/dashboard: USD 0 (serverless free tier, estimate) to 730 h x USD 0.05 = **USD 36.5** always-on container (the 0.05 per hour figure is from the hosting doc).
- Self-hosted SDK path replaces the runtime fee with sandbox container time: each 0.25 h task container at about USD 0.05/h is under USD 2 per month (estimate).

Monthly total: low 196.5 + 6 + 0 = about **USD 203**; high 284.5 + 6 + 36.5 = about **USD 327**. Rounded range **USD 200-330**. Token cost is 85-95 percent of it. Session budgets (`max_list_cost`, e.g. USD 5 per ticket) bound the worst case at USD 500 for 100 tickets.

## Fit per project type

- web-app: good — long-running multi-step tickets with tests, cloud deploys and secrets benefit from per-task sandboxes, budgets and approval gates; but the build cost is only justified if 5+ such repos share it.
- small-scripts: poor — a one-off 8-20 developer-day build and API-only billing is oversized for repos with no CI and few tickets; `claude -p` or a chat session does the job.
- plugin-repo: poor — work is Markdown/JSON skills edited and validated locally with `scripts/validate.sh`; a hosted platform adds cost with no gain, and the repo already carries its own orchestration (dev-kit, campaign-kit).

## Smallest prototype

What `prototypes/ai-sdlc/trial.sh` would do for this approach: clone the sample repo with `git clone --no-hardlinks`, then run a ~60-line Python script using `claude_agent_sdk.query()` three times (plan with read-only tools, implement with `Read/Edit/Bash` and `permission_mode="acceptEdits"`, review with read-only tools), `cwd` = the clone, `max_budget_usd` and `max_turns` set, read `ResultMessage.total_cost_usd` per phase, then `git -C <clone> diff --name-only <start-sha>` and write `trial-result.json` (`approach: agent-platform`).

- Runs locally and headless without push/PR/deploy/sign-up? **Partial: yes for the Agent SDK path, no for Managed Agents.** The SDK path needs a project-local install (`npm install` or a venv `pip install` inside `prototypes/ai-sdlc/`, not global) and a model credential: in this shell `ANTHROPIC_API_KEY` is unset, and whether the bundled binary may reuse the local Claude Code login is unverified (docs say API-key auth is the supported route). Managed Agents needs a Claude Console account and API key (sign-up) and a GitHub remote for repos, so it is `needs-human` and cannot be trialled under the guardrails.
- Local fallback that exercises the same loop with no new access: `claude -p --max-budget-usd 5 --output-format json` (verified present in `claude --help`, CLI 2.1.76) — this is approach A's headless equivalent, so a trial would prove A, not B.
- Estimated cost per trial run: about USD 0.5-2 for a small ticket on Sonnet 5.5 (scaled from the USD 1.97 per-ticket estimate; enforce `max_budget_usd` 5 as hard cap).

## Reference designs

- Factory (docs.factory.com): Droid across CLI, desktop, web and mobile; Automations for triage/review/QA/docs/incident response; Workstreams = an orchestrator running a team of agents in parallel; enterprise controls and an API. Useful as a component checklist (intake, fleet, dashboard, automations), not scored. https://docs.factory.com/
- Anthropic's own "build a complete app" quickstarts pair Managed Agents with chat frameworks (Chat SDK, assistant-ui, CopilotKit) and show an Allow/Deny gate per bash command: a ready template for the dashboard/approval UI. https://platform.claude.com/docs/en/managed-agents/quickstart (github.com/anthropics/claude-quickstarts is the repo it links).

## Open risks

- Managed Agents is beta: API, header and billing semantics may change; the pricing page may move. Re-verify before any commitment.
- Cost figures rest on my token-per-ticket assumptions; the real range could be 2-3x either side until a trial measures them. `total_cost_usd` is a client-side estimate, not billing.
- SDK terms: subscription (claude.ai) login cannot back a product built on the SDK, so no flat-rate plan economics.
- A platform concentrates secrets (GitHub tokens, API key); `unrestricted` default networking and allowed-host `git push` are exfiltration paths; Managed Agents is not ZDR/HIPAA eligible and transcripts persist until deleted.
- Webhook delivery is best-effort (3 attempts, then dropped): the intake and state machine must reconcile by polling.
- Developer-day figures are estimates by component; solo-developer maintenance burden after build is not included.
- Round-3 prototype needs `ANTHROPIC_API_KEY` or confirmed login reuse; otherwise this approach cannot be trialled and approach A's headless path must stand in.
