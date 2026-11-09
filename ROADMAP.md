# Roadmap

> Planned 2026-11-04. Updated 2026-11-05: the planned `sdlc-kit` shipped as the developer family
> inside `dev-kit`, next to a new campaign family (`campaign-kit`). Updated 2026-11-07: the nine
> cognitive-load options (`docs/ai-sdlc/cognitive-load.md`) shipped across the kits and a new
> `focus-kit`.

## Developer family (was: sdlc-kit) — `dev-kit` 1.1.0

**Goal:** the planner / worker / integrator workflow from
[whisk-studio's `AGENTS.md`](https://github.com/adrienLamoureux/whisk-studio/blob/main/AGENTS.md)
becomes installable in any repo, with cheap agents doing the reading and writing.

- [x] Skills in `dev-kit` rather than a new plugin, so model routing (`pick-model`) and the
      workflow ship together:
  - `plan` (was `plan-slices`): scout → planner → `plan.md` with frozen contracts, slices
    owned by path, gates, merge order; `plan_tool.py check` proves parallel slices are disjoint.
  - `implement` (was `work-slice` + `integrate-slices`): waves of workers, a checker per wave
    (gates, ownership, contract drift), integration gates in merge order, regressions first.
  - `review`: an Opus judge reads the diff against the plan; `changes-required` loops back to
    `implement … fix`.
  - `investigate` (was `investigate-first`): read-only reproduction, three ranked hypotheses
    with `path:line` evidence, smallest experiment.
- [x] Repo-agnostic: gates come from `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, CI and
      package scripts, never hard-coded.
- [x] Model and effort routing: Sonnet medium/high executes and checks, Opus medium/high/xhigh
      plans and judges; `pick-model` advises on effort too.
- [x] `claude plugin eval` suite (trigger and outcome cases, one should-not-fire).
- [x] Listed in `marketplace.json` and the README.
- [ ] Run the eval suite once and tune descriptions on its results (`skill-creator`).
- [ ] Trim whisk-studio's `AGENTS.md` to its repo-specific rules (stack map, Cognito, slice
      templates, gates) and point it at `dev-kit`.
- [x] 1.3.0: orchestrating turns at `effort: medium`, checker and scout without `CLAUDE.md`,
      shorter descriptions, `/goal` line after plan approval, one-call advisor rule.
- [x] Re-run `prototypes/ai-sdlc/trial.sh` on 1.3.0: passed, `approve`, USD 0.84 against 0.78
      on 1.2.1 (one run each). No saving shows on this S ticket: the repo has no `CLAUDE.md`.
- [ ] Measure 1.3.0 where the savings apply: an M ticket in whisk-studio (its `CLAUDE.md`
      imports an 8 KB `AGENTS.md`), and an interactive Opus session at high effort.
- [ ] Try the `/goal` implement → review → fix loop headless, and a Sonnet session with
      `--advisor opus`, and keep whichever is cheaper per approved ticket.
- [ ] Optional: `isolation: worktree` for parallel slices that cannot be made path-disjoint.
- [ ] Optional `eval-agent` skill: scaffold a golden set and an eval runner for a repo with an
      LLM agent (modelled on whisk-studio's planned `backend/evals/`).
- **Done when:** `claude plugin install dev-kit@adrien-skills` works in
  [whisk-proto-gcp](https://github.com/adrienLamoureux/whisk-proto-gcp), and a ticket there goes
  plan → implement → review using only the plugin.

## Campaign family — `campaign-kit` 0.1.0

**Goal:** objectives that cannot be planned up front (coverage, latency, migrations, backlogs,
research) run as a resumable ReAct loop with measurable done criteria.

- [x] `interview`, `execute`, `review`, and `campaign` (the loop), with a strategist, runners,
      a checker and a judge; `campaign_tool.py next` drives and resumes the loop and sets the
      judge's effort from the round's results.
- [x] Guardrails default to no outward-facing actions; checkpoints configurable per campaign.
- [x] `claude plugin eval` suite.
- [ ] Run a real campaign end to end (candidate: raise test coverage in whisk-studio) and
      tune round sizes and judge effort thresholds on what it costs.
- [ ] Publish the campaign status with `project-artifact` automatically at each checkpoint
      when installed.
- [x] 0.3.0: the checker no longer reads `formats.md` each round; `/goal` line for unattended
      campaigns; plain `/goal` suggested for single-condition objectives.
- [x] Headless trial (`prototypes/campaign-kit-trial/`): 4 modes x 2 batches. It found that the
      checker and orchestrator chained shell commands and a runner resolved the run folder
      against the wrong root; 0.3.0 adds the one-command rule and absolute `DIR`. Completion
      went from 1 of 4 runs to 4 of 4.
- [x] `/goal` launcher with a status line from `campaign_tool.py next`; the judge's bounded Opus
      escalation for a failing lane (`"model": "opus"`, checked by the tool). Trial batches 3-4:
      both work end to end; neither changed quality on these fixtures.
- [ ] Advisor: still never called (0 in 7 runs). Needs a lane Sonnet cannot solve in one
      attempt even with failing cases in hand; otherwise leave it as documentation.
- [ ] `/goal`: a long campaign (6+ lanes, 4+ rounds) where a turn is likely to end early.
- [ ] Run the judge's "sharper Sonnet task first" rule on the escalate fixture with `--runs 3`.

## Human attention — `focus-kit` 0.1.0, dev-kit 1.4.0, campaign-kit 0.4.0, docs-kit 1.1.0

**Goal:** the person supervising the kits reads less, decides faster and loses less context
between sessions, without losing their understanding of the code (research and options:
`docs/ai-sdlc/cognitive-load.md`).

- [x] Review map: `## Where to look` and `## Machine-checked` in dev-kit `review.md` and campaign
      `outcome.md`; `## Needs human eyes` in campaign checks; a `Look at:` recap line.
- [x] Decision card (`Decide`, `Recommend`, `If wrong`, `Undo cost`, `On "ok"`) at every gate of
      both kits.
- [x] `focus-kit:Reader-first` output style. Benchmark (Sonnet, 3 prompts, 1 run): 173 mean
      words against 205 for `Concise` and 266 for the default; ends with the next move 3/3 against
      0/3 (`prototypes/focus-kit-trial/RESULTS.md`, USD 0.55).
- [x] `resume.md` at every stop; focus-kit inbox, `SessionStart` hook, status-line segment,
      `dismiss`.
- [x] `max_lines` per slice and `plan_tool.py size`; the checker reports, the reviewer flags.
- [x] `/focus-kit:explain` and a personal vocabulary handed to Claude at session start.
- [x] Pacing line past three open runs; one campaign checkpoint per round.
- [x] `## In plain words` in plans, reviews and briefs; `Reader-first` learning mode on request (`Explanatory` without focus-kit).
- [x] Acronym check in `check_docs.py`; `/focus-kit:inbox page` (static runs page).
- [x] No command needed: `Reader-first` sets `force-for-plugin` (verified headless); a
      `PostToolUse` hook rebuilds the runs page when a run's `resume.md` is written (verified
      headless); finished runs stop asking after 7 days; explain and dismiss trigger on plain
      words.
- [x] Review fixes: inbox shows blocked campaigns despite an outcome, shows dev-kit fixes in
      progress, reads verdict lines in any form, and decides "finished" by pattern; status line
      cached 3 minutes and Write hook guarded in shell; `size` counts untracked files from a
      subdirectory; Reader-first learning mode on request; one `stop-blocks.md` per kit.
      Planned, implemented and approved through dev-kit (`cognitive-load-review-fixes`); its two
      should-fix items followed: `dismiss` clears the status-line cache and rebuilds the page, and
      a failed cache delete no longer stops the Write hook.
      Fixtures: `prototypes/focus-kit-trial/check_focus_tool.py` (14 cases), `check_plan_size.py`.
- [ ] Seeded-bug trial: does `## Where to look` point at a planted bug in 4 of 5 runs
      (`prototypes/ai-sdlc/trial.sh` with a bug in the fixture)?
- [ ] Measure words a human reads per ticket before and after, from trial transcripts.
- [ ] A/B: does a term in the vocabulary stop being glossed under `Reader-first`?
- [ ] Re-run `bench_styles.py --runs 3`; tighten the style if replies stay above ~120 words.
- [ ] Check that the `SessionStart` message shows in the desktop app and VS Code, not only the
      CLI.
- [ ] Run the focus-kit eval suite once and tune the skill descriptions.
- [ ] Route coding tasks through dev-kit without the slash command. A repo `CLAUDE.md` rule and a
      wider `plan` description (build, implement, add across areas) did not fire in 3 headless
      probes (Sonnet, 3 turns, 1 run each, USD 0.30); eval cases `implement-multi-area-unplanned`
      and `no-fire-one-file-edit` added. Hooks and subagent options are being tried next.

## Marketplace

- [x] Pinned listings of Anthropic plugins: `skill-creator`, `plugin-dev`, `commit-commands`,
      `security-guidance`, `project-artifact`, `webapp-testing`. `claude-md-management` is
      recommended from `claude-plugins-official` (reserved name).
- [x] On-demand `evals` workflow in CI; `validate.yml` unchanged.
- [ ] Bump the pinned SHAs quarterly and re-check licences.
- [ ] Plugin icons (the only `--strict` validation warning).
