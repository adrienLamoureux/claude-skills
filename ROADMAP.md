# Roadmap

> Planned 2026-11-04, nothing started yet. Tick the boxes as work lands.

## sdlc-kit: the planner / worker / integrator workflow as skills

**Goal:** the multi-agent delivery workflow becomes installable in any repo. Today it lives only as
prompt templates in [whisk-studio's `AGENTS.md`](https://github.com/adrienLamoureux/whisk-studio/blob/main/AGENTS.md),
which are skills in all but name.

- [ ] New plugin `plugins/sdlc-kit/` with four skills:
  - `plan-slices`: break down a ticket, freeze contracts, give each slice its own paths, set
    gates and merge order (the planner's required output).
  - `work-slice`: implement one slice inside its own paths and run the slice gates.
  - `integrate-slices`: merge in the planner's order, detect contract drift, run all gates,
    report regressions first.
  - `investigate-first`: read-only reproduction, three ranked hypotheses, evidence with file
    references, and the smallest experiment.
- [ ] Make them repo-agnostic: each skill reads the gate commands from the repo's `AGENTS.md` or
      `CLAUDE.md` rather than hard-coding npm.
- [ ] Optional `eval-agent` skill that scaffolds a golden set and an eval runner for any repo with
      an LLM agent (modelled on whisk-studio's planned `backend/evals/`).
- [ ] A `claude plugin eval` suite per skill (trigger accuracy and output shape), run in
      `.github/workflows/validate.yml` next to `scripts/validate.sh`.
- [ ] Add `sdlc-kit` to `.claude-plugin/marketplace.json` and to the tree in `README.md`.
- [ ] Trim whisk-studio's `AGENTS.md` to its repo-specific rules and point it at the plugin.
- **Done when:** `claude plugin install sdlc-kit@adrien-skills` works in
  [whisk-proto-gcp](https://github.com/adrienLamoureux/whisk-proto-gcp), and a ticket there goes
  plan → slices → integrate using only the plugin.
