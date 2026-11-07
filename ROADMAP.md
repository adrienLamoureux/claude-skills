# Roadmap

> Planned 2026-11-04. Updated 2026-11-05: the planned `sdlc-kit` shipped as the developer family
> inside `dev-kit`, next to a new campaign family (`campaign-kit`).

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

## Marketplace

- [x] Pinned listings of Anthropic plugins: `skill-creator`, `plugin-dev`, `commit-commands`,
      `security-guidance`, `project-artifact`, `webapp-testing`. `claude-md-management` is
      recommended from `claude-plugins-official` (reserved name).
- [x] On-demand `evals` workflow in CI; `validate.yml` unchanged.
- [ ] Bump the pinned SHAs quarterly and re-check licences.
- [ ] Plugin icons (the only `--strict` validation warning).
