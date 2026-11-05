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

## Marketplace

- [x] Pinned listings of Anthropic plugins: `skill-creator`, `plugin-dev`, `commit-commands`,
      `security-guidance`, `project-artifact`, `webapp-testing`. `claude-md-management` is
      recommended from `claude-plugins-official` (reserved name).
- [x] On-demand `evals` workflow in CI; `validate.yml` unchanged.
- [ ] Bump the pinned SHAs quarterly and re-check licences.
- [ ] Plugin icons (the only `--strict` validation warning).
