# Kit auto-routing: what Claude Code allows and what works

Dates: 2026-11-07/08 · Claude Code 2.1.319 · probes: 32 headless runs, **USD 4.14 measured**.
Ten more runs were killed by a session restart before reporting. Their spend is unknown and
bounded by their caps (USD 2.04); a full re-run of the same ten cost USD 0.93. Cap: USD 5.

## Target behaviour (the user's words, via the parent session)

"focus-kit should always be used. dev-kit should be used mostly automatically. An Agent could
propose also the campaign kit if more fitting by decision based." Read as one routing decision
per coding task:

| The task reads as | Route | Behaviour |
|---|---|---|
| a change inside one file or one area | direct edit | nothing happens |
| a change across two or more areas | `/dev-kit:plan` | **starts on its own**, with a one-line note saying why; "just edit it" overrides |
| an unexplained failure | `/dev-kit:investigate` | **starts on its own**; "just fix it" overrides |
| an objective measured over rounds | `/campaign-kit:campaign` | **proposed in one line, never started**; the user decides |

focus-kit is out of scope here; the parent session handles it.

## Short answer

- **A note alone is not enough.** In the earlier probes the advisory note was ignored in
  10 of 10 investigate and campaign runs, and in 1 of 3 Sonnet plan runs.
- **A hold the model cannot skip works.** A `PreToolUse` hook denies Edit and Write for the
  task until the routed skill has run (plan: until the plan is approved) or the user says to
  edit directly. The prompt note now states that hold as a fact. With it, each route did what
  the target says on its first try:
  - plan: `dev-kit:plan` was the first call, and no code was written;
  - bug: after one held edit, Claude started `dev-kit:investigate`;
  - objective: no tool calls, just a one-line campaign-kit proposal and a question.

  That is one run per route.
- **False positives on one-area tasks, measured on real history.** I replayed 66 real tasks
  with repo edits through the same hook code:
  - 28 of 28 multi-area tasks are held, and none are missed. 26 of them are caught by the
    second-area hold, mostly follow-ups like "continue" and "resume".
  - 2 of 38 one-area tasks are held (5.3%). One is a greenfield FastAPI + React build, which
    is right by intent; the other is a README edit from pasted text, a real false positive
    (2.6%).
- **Subagents** cannot get the user's approval, so they cannot run a kit end to end. Holds
  apply inside subagents (kit agents exempt), and their reason says to report back so the
  main session can route.

## Ranked mechanisms

Ranked for the target behaviour. "One-area false positives" is measured where a number is
given; otherwise it says so.

| # | Mechanism | Possible? (docs) | Verified | Measured effect | Cost | One-area false positives | Effect on subagents | Off switch |
|---|---|---|---|---|---|---|---|---|
| 1 | **Prompt router + task hold, mode `gate` (shipped default).** `UserPromptSubmit` picks one route and records it; `PreToolUse` on Edit, Write, MultiEdit and NotebookEdit holds edits for routed tasks: plan until a plan is approved; investigate until `dev-kit:investigate` runs (seen via `PreToolUse` on `Skill`); campaign for the rest of the turn. Lifts: approved plan, the skill run, or the user's own words ("just edit it", "just fix it", "no campaign") | Yes. `additionalContext` beside the prompt; `permissionDecision: "deny"` with a reason Claude reads (hooks › UserPromptSubmit, PreToolUse) | Probed + 19 unit tests + replay | **plan 1/1, investigate 1/1, campaign 1/1** did the target behaviour. Plan and campaign needed no denial; the stated hold sufficed | About 110 tokens when a prompt is routed (4.9% of 285 real typed prompts); about 72 ms per prompt and per Edit, Write, Skill or Agent call, per kit; a held edit costs one denied tool call | **2/38 (5.3%) held by a prompt route**; 1 is a real false positive (2.6%) | Holds apply inside subagents; `dev-kit:*` and `campaign-kit:*` agents exempt; "report back" wording | `KIT_ROUTING=nudge` (notes only) or `off`; per kit `DEV_KIT_ROUTING`, `CAMPAIGN_KIT_ROUTING` |
| 2 | **Second-area hold** (part of 1): a direct edit that brings *this task's* edits to a second area, with no approved plan, is held the same way | Same | Unit tests + replay + earlier gate probe (F) | Caught **26 of 28** real multi-area tasks, mostly keyword-free follow-ups | Same | **0/38** with areas tracked per task. Tracked per session it would be **7/38** extra (rejected) | Same | Same |
| 3 | **Wider `plan` description** (main checkout): "asks to build, implement or add … more than one area … (plan it first)" | Yes (1,536-character listing cap) | Probed | Opus alone 0/2 → **3/3**; Sonnet alone **0/3** | About 40 listing tokens per session | Rename probe quiet (not a rate) | Listed to subagents that have `Skill` | Edit the text |
| 4 | **Agent hand-off hold** (gate): deny once when a multi-area build goes to a non-kit subagent | Yes. A note would arrive only after the subagent ran (PreToolUse `additionalContext` arrives with the result) | Unit tests only | Not probed | One denied call per session | Same classifier as 1 | The realistic "agents use dev-kit" lever | Same |
| 5 | Notes only (mode `nudge`) | Yes | Probed | plan Sonnet 0/3 → 2/3, Opus (old description) 0/2 → 1/2; **investigate 0/2; campaign 0/2** | As 1, never blocks | Never blocks; prompt-route rate as 1 | None | Same |
| 6 | Hold once, then let a retry through (speed bump) | Yes | Probed | Bug: retried, fixed directly, did not say why. Cross-area rename: retried and disclosed. Doesn't route | One denied call | — | — | — |
| 7 | Skill descriptions as they are (investigate, campaign) | Yes | Probed | **0/6** hook-off runs | Already paid | — | — | — |
| 8 | Repo `CLAUDE.md` rule (main checkout) | Yes | Earlier 3 probes, 0 fires (cut short) | Unknown alone; it defines the same areas the hook uses | About 200 tokens per session, this repo only | Not measured | Read by subagents unless `omitClaudeMd` | Delete lines |
| 9 | `SessionStart` static rule | Yes (command or mcp_tool) | Docs | Not probed: weaker than 1 | About 100 tokens per session, every project | Not measured | `SubagentStart` input has no prompt: static only | Toggle |
| 10 | Rewrite the prompt into a slash command | **No**: UserPromptSubmit output has no prompt-rewrite field; `UserPromptExpansion` sees only typed commands | Docs | — | — | — | — | — |
| 11 | Small-model prompt classifier in a command hook | Yes | Not built | — | A model call and 1–3 s per prompt | Probably lower than 1 | None | — |
| 12 | `type: "prompt"` hook on UserPromptSubmit | Can't add context: `ok: false` ends the turn | Docs | Would block the prompt | A model call per prompt | Loses the prompt | None | — |
| 13 | `Skill` in kit agents' `tools:` / `skills:` preload | Possible (`skills:` works for plugin agents; nesting to 3 layers) | Docs | Not useful: no `AskUserQuestion` in subagents, so no approval stop; recursion risk | Full skill text per launch | — | Don't | — |
| 14 | Plugin output style `force-for-plugin` | Yes | Docs | Rejected: overrides the user's `outputStyle` and drops coding instructions | Every turn | — | — | — |

## Probe results

Setup: the fixture is a 7-file Express + React repo with a real bug: the form posts FormData,
and the server parses JSON (`make_fixture.py`). Each run: `claude -p … --max-turns 6
--setting-sources project --plugin-dir <dev-kit> [--plugin-dir <campaign-kit>]
--tools Read,Glob,Grep,Skill,Edit,Write --permission-mode acceptEdits`. Agent and Bash were
withheld to cap cost, so a started skill stops before its agents. Records:
`probe-summaries.json`.

Prompts: **build** *Implement per-user rate limiting on POST /login in our Express backend,
show a "too many attempts" message with a countdown in the React login form, and make the
limit configurable per environment.* · **bug** *Login always fails with "Login failed
(attempts: 1)" even when I type alice and secret. Fix it.* · **objective** *Raise test
coverage of server/ and client/ to 80%.*

**Gate (the shipped behaviour), Sonnet:**

| Route | Outcome | USD |
|---|---|---|
| build → plan | `dev-kit:plan` was the first call. No denial needed; wrote only `.dev-kit/<slug>/resume.md` | 0.08 |
| bug → investigate | Read 3 files; the first edit was held; then started `dev-kit:investigate`, writing only under `.dev-kit/` | 0.09 |
| objective → campaign | No tool calls: "This looks like a goal measured over several rounds … I suggest running `/campaign-kit:campaign` … Do you want that, or should I just start adding tests directly?" | 0.03 |
| bug, with a hold-once (superseded) | First edit held; retried; fixed directly; never said why | 0.07 |

**Notes only, and baselines:**

| Route | Model | Kit description | Hook | Fired | USD |
|---|---|---|---|---|---|
| plan | Sonnet | wider | off | 0/3 | 0.40 |
| plan | Sonnet | wider | nudge | 2/3 | 0.40 |
| plan | Sonnet | old | nudge | 0/1 | 0.14 |
| plan | Opus | wider | off | **3/3** | 0.46 |
| plan | Opus | wider | nudge | 1/1 | 0.17 |
| plan | Opus | old | off | 0/2 | 0.59 |
| plan | Opus | old | nudge | 1/2 | 0.58 |
| investigate | Sonnet | main checkout | off / nudge | 0/2 / 0/2 | 0.28 |
| investigate | Opus | main checkout | off | 0/1 | 0.14 |
| campaign | Sonnet | main checkout | off / nudge | 0/2 / 0/2 | 0.33 |
| campaign | Opus | main checkout | off | 0/1 | 0.18 |

Other probes (Sonnet):
- **One-file rename:** quiet, edited directly (USD 0.07).
- **Prose false positive** ("Add Angular for front-end skills…"): the note fired, and the
  model edited `resume.md` directly and said why (USD 0.06).
- **Cross-area rename, earlier hold-once gate:** held once, retried, disclosed (USD 0.07).

## Offline measurements (no model calls)

**`replay_gate.py`** replays real sessions' typed prompts and main-thread Edit and Write
calls, in order, through the hook's own `record_prompt()` and `decide_edit()`. It runs in
gate mode, with no plans approved, over 4 local projects.

| Area tracking | Tasks with repo edits | One-area tasks held | Multi-area tasks held | Missed |
|---|---|---|---|---|
| **per task** (shipped) | 66 | **2/38 (5.3%)**: a greenfield "Create a GCP with Python FastAPI and React…" (right by intent) and a README edit from pasted text (wrong) | **28/28** | 0 |
| per session | 66 | 9/38 (23.7%) | 28/28 | 0 |

Of the 28 multi-area tasks, 2 were caught by the prompt route. One is "Build all the options
one after another", the cognitive-load incident. The other 26 were caught by the second-area
hold, mostly follow-ups ("continue", "resume", "move next step"). Caveats:
- After the first hold, the real session kept editing, so only "held at least once" counts.
- Subagent edits were not replayed.
- One repo no longer exists on disk; its sessions' first working folder stands in as root.

**Prompt router** (`plugins/dev-kit/hooks/test_route.py`, `replay_transcripts.py`):
- **Hand-labelled corpus (66 prompts):** plan 19/19, investigate 9/9, campaign 8/8, quiet
  28/30. The 2 misses are plan notes on one-area prompts; one only fires outside the main
  checkout.
- **Real typed prompts (285):** 14 routed (4.9%): plan 13 (5 right, 8 prose), investigate 1
  (right: a pasted CI failure), campaign 0.
- **Unit tests:** 19 pass. They cover:
  - holds per route, and what lifts each (a finished or stale plan does not);
  - only the user's own words lift a hold: a message from another session or a task note
    does not;
  - area tracking restarts per task;
  - nudge never blocks, and off is silent;
  - exempt agents and `.dev-kit/` writes;
  - the Agent hand-off hold;
  - failing open on bad input;
  - the two `route.py` copies being identical.

**Latency:** median 72 ms per hook call.

## Subagents: what "agents use the kits" can mean

- A subagent can call `Skill` if its tools allow it, and can nest agents 3 layers deep. It
  cannot finish a kit's flow, because `AskUserQuestion` is stripped from every subagent.
- So routing happens in the main session, before it delegates. Routed holds and the
  second-area hold also apply to a general-purpose subagent's edits, with "report back"
  wording. Gate mode holds a multi-area hand-off once.
- Kit agents keep their tools as they are: no `Skill` and no `skills:` preload.

## Known holes

- **Bash writes are not held.** `sed -i` and heredocs bypass the Edit and Write hold. The
  reason says "Do not retry this edit", but nothing enforces it for shell writes. A Bash
  matcher for obvious write commands into the repo is possible; it is not built.
- **Areas reset at each typed prompt.** This is what keeps one-area false positives at 0
  rather than 7 of 38. The cost: a multi-turn task that edits one area per turn is caught
  only if its first prompt was routed.
- **Keyword heuristic:** English only. Prose about tech (résumés, prep notes) can route to
  plan; the user lifts it with "just edit it".
- **Unverified:** whether a subagent's hook input carries the parent's `session_id`, which
  the task state assumes; whether `claude plugin eval` runs plugin hooks; the Agent
  hand-off hold in a live run.
- **Small samples:** one run per gate route, one tiny fixture, Agent withheld. The full
  plan → approve → implement path was not run.

## Shipped (dev-kit 1.5.0, campaign-kit 0.5.0)

- The wider `plan` description and the `CLAUDE.md` routing rule landed on main in PR #8.
- `plugins/dev-kit/hooks/` and `plugins/campaign-kit/hooks/`, with `test_route.py` beside
  dev-kit's router. `scripts/validate.sh` runs it, and it fails if the two `route.py` copies
  drift apart.
- Added while landing: a plan lifts holds only while its run is live. That means it is
  approved, has no `approve` or `blocked` verdict in `review.md`, and was touched in the last
  7 days. Without this rule, any finished run left in `.dev-kit/` turned the gate off for good.
- Kit READMEs explain how to lift a hold ("just edit it", "just fix it", "no campaign"), and
  their headless sections say to set `KIT_ROUTING` for free-text runs. The ROADMAP has a
  `## Kit routing` section. The onboarding doc gained a gotcha and a change-log line. Version
  bumps: dev-kit 1.5.0, campaign-kit 0.5.0, marketplace 1.5.0.
- `CLAUDE.md`'s area list already matches the hook's rule: each `plugins/<kit>/` and each
  top-level folder is an area, and root files and tests belong to none.
- Left for later: a `routing` userConfig row in `/config`. `options` needs Claude Code
  ≥ 2.1.271 and would stop older versions loading the kit, so the env vars stay the switch
  for now.

## Files

- **New:**
  - `plugins/dev-kit/hooks/hooks.json`, `route.py` and `test_route.py`;
  - `plugins/campaign-kit/hooks/hooks.json` and `route.py` (a copy);
  - in `prototypes/dev-kit-routing/`: `RESULTS.md`, `replay_gate.py`,
    `replay_transcripts.py`, `make_fixture.py`, `summarize_probe.py` and
    `probe-summaries.json`.
- **Edited:** both kits' `plugin.json` and `README.md`, `.claude-plugin/marketplace.json`,
  `ROADMAP.md`, `scripts/validate.sh`, `docs/ai-sdlc/onboard-a-repo.{md,html}` and the docs
  index.
- **Untouched:** focus-kit.
