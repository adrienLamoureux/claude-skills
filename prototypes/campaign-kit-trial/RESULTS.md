# campaign-kit trial results — 2026-11-06

One campaign (`textkit-spec`: 3 lanes, at most 2 actions per round, unattended), run headless
with `claude -p --model sonnet` in four modes, scored by `trial.py` against pristine tests.
Claude Code 2.1.319, campaign-kit 0.3.0 (uncommitted branch `feat/goal-advisor-token-trim`).
Four batches, one run per mode each, plus an advisor probe: USD 14.00 in all.

## Verdict

| Feature | Place in the kit | Evidence |
|---|---|---|
| `/goal` with the status line | **the launcher for unattended and headless campaigns**; insurance, not a quality gain | batches 3–4: met on the `done — stop-done` line after one check, USD 0.003; batch 1: the only run that finished on a broken kit, but by bypassing the checker |
| Judge's Opus escalation | **kept, bounded by `campaign_tool.py check`**; try a sharper Sonnet task first | batch 4: works end to end; the judge escalated in 1 of 2 runs, and the Sonnet run with a sharper task reached the same quality for 25% less |
| Advisor | **optional, documented only** | 0 calls in 7 advisor-enabled runs; one call costs about USD 0.14 even on a near-empty session |
| One-command shell rule, absolute `DIR` | **required** | batch 1 → 2: completion 1/4 → 4/4, denials 4–13 → 0–1 |
| A measurable acceptance criterion | **the biggest quality lever** | batch 3: holdout 36/36 and holdout2 24/24 in every mode, against 31–33/36 when only the spec was visible |

## Batch 1 — spec fixture, kit before the headless fix

| Run | Done | Rounds | Spec | Holdout | Checker measured | Cost USD | Turn ends | Advisor calls | Denials |
|---|---|---|---|---|---|---|---|---|---|
| baseline | no (stopped at `check`) | 0 | 42/48 | 30/36 | no | 0.48 | 1 | 0 | 5 |
| advisor | no (stopped at `check`) | 0 | 42/48 | 30/36 | no | 0.46 | 1 | 0 | 4 |
| goal | yes, `stop-done` | 2 | 48/48 | 32/36 | no: the orchestrator measured | 1.51 | 4 | 0 | 13 |
| advisor-goal | no (stuck at `approve-round`, stop-hook cap) | 1 | 42/48 | 30/36 | round 1 only | 0.91 | 13 | 0 | 7 |

- The campaign-kit agents chained shell commands (`score.py spec; score.py tests; git status`),
  which the headless allow-list denies, so the checker never measured.
- A runner resolved the run folder against the claude-skills folder above the fixture.
- Baseline and advisor stopped honestly at the blocker. `goal` pushed on 3 times and finished
  by measuring the criteria itself. `advisor-goal`'s orchestrator would not retry one denied
  `T=…; python3 $T approve … && …` command, and the goal re-prompted it until the cap.

## Batch 2 — spec fixture, kit with the one-command rule and absolute `DIR`

| Run | Done | Rounds | Spec | Guard | Holdout | Checker measured | Cost USD | Min | Turn ends | Advisor calls | Denials |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | yes, `stop-done` | 2 | 48/48 | 7/7 | 33/36 | yes | 0.97 | 3.6 | 1 | 0 | 0 |
| advisor | yes, `stop-done` | 2 | 48/48 | 7/7 | 31/36 | yes | 0.90 | 4.1 | 1 | 0 | 1 |
| goal | yes, `stop-done` | 2 | 48/48 | 7/7 | 32/36 | yes | 0.87 | 4.3 | 1 | 0 | 1 |
| advisor-goal | yes, `stop-done` | 2 | 48/48 | 7/7 | 33/36 | yes | 0.98 | 4.9 | 1 | 0 | 0 |

Every run missed the same 3 holdout slug cases (`Ł`, `Œ`, `Þ`/`Đ`, letters the spec did not
name).

## Batch 3 — black-box fixture (acceptance suite outside the repo)

| Run | Done | Rounds | Spec | Acceptance | Holdout2 | Lanes not pass | Opus lane runs | Cost USD | Min | Turn ends | Advisor calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | yes, `stop-done` | 2 | 48/48 | 36/36 | 24/24 | 0 | 0 | 1.17 | 4.3 | 1 | 0 |
| advisor | yes, `stop-done` | 2 | 48/48 | 36/36 | 24/24 | 0 | 0 | 1.17 | 4.6 | 1 | 0 |
| goal | yes, `stop-done` | 2 | 48/48 | 36/36 | 24/24 | 0 | 0 | 0.93 | 4.3 | 1 | 0 |
| advisor-goal | yes, `stop-done` | 2 | 48/48 | 36/36 | 24/24 | 0 | 0 | 1.16 | 5.0 | 1 | 0 |

The fixture was meant to make round 1's lanes come back partial. Instead the runners ran
`tools/accept.py` themselves and fixed every case it printed, so no lane failed, nothing
escalated and no advisor rule fired. The orchestrator printed the status line at each step, and
both goal runs ended on `campaign textkit-spec: done — stop-done, round 2` after one evaluation.

## Batch 4 — escalate fixture (starts at the judge after a seeded partial lane)

Round 1 is scripted: durations passed; slugify passes the spec but fails 3 acceptance cases
after two attempts, and its report describes a reasoning gap (letters with no decomposition).

| Run | Judge's round 2 for slugify | Opus runner launched | Done | Spec | Acceptance | Holdout2 | Cost USD | Opus USD | Min |
|---|---|---|---|---|---|---|---|---|---|
| baseline | sharper task, Sonnet, effort medium | no | yes, `stop-done` | 48/48 | 36/36 | 24/24 | 0.99 | 0.49 | 3.5 |
| advisor | `"model": "opus"`, effort high: "misread the rule, taking the examples as exhaustive" | yes | yes, `stop-done` | 48/48 | 36/36 | 24/24 | 1.32 | 0.97 | 5.0 |

The escalation path works end to end: the judge wrote the Opus action, `campaign_tool.py
check` accepted it, `next` listed it under `models`, and the orchestrator launched the runner
with `model: opus`. Both runs fixed the lane in one round, so the escalation bought nothing
here. The judge now tries a sharper Sonnet task first, and escalates when a sharpened lane
fails again.

## Advisor probe

`claude -p --model sonnet --advisor opus "Consult your advisor tool exactly once …"` made one
`server_tool_use` call named `advisor` (an `advisor_redacted_result` came back). Cost: Sonnet
USD 0.04 plus Opus USD 0.14 for a near-empty session. The advisor re-reads the whole
transcript, Claude Code's system prompt included, uncached.

## What changed in the kit because of this trial

- Every campaign-kit skill and agent: one plain command per Bash call, `campaign_tool.py` by
  full path, a denial is one unmatched command; agents get `DIR` as an absolute path.
- `campaign_tool.py next` prints a `status` line (`campaign <slug>: running | waiting for you |
  done …`), which the loop repeats and the `/goal` launcher reads; the loop adds
  `… blocked — <what would clear it>` when it stops on a blocker.
- A blocked step stays blocked under a `/goal`: no self-measured criteria, no self-approved
  rounds.
- The judge may set `"model": "opus"` on a failing lane's next action. `check` allows it only
  right after `fail` or `partial` and never twice in a row, and `next` reports it under
  `models`. A `partial` lane now raises the judge's effort to `high`, like a failed one.

## Limits

- One run per mode per batch: enough to show whether a feature works and what it costs, not
  to rank quality. Identical dev-kit trial runs differed by 7% in cost.
- The campaigns are short (2 rounds, about 4 minutes). No run lasted long enough for a turn to
  end early, which is where `/goal` would earn its place.
- No runner needed a second attempt, so the advisor's one-call rule never fired. Sonnet solved
  every lane once it had a precise task or a failing-case list.
- The interview and strategist are scripted out.
- The judge's "sharper task first" rule came after batch 4 and has not been run.

## Reproduce

```bash
python3 -I prototypes/campaign-kit-trial/trial.py --self-test
python3 -I prototypes/campaign-kit-trial/trial.py --budget 4                                   # batch 2
python3 -I prototypes/campaign-kit-trial/trial.py --fixture blackbox --budget 5                # batch 3
python3 -I prototypes/campaign-kit-trial/trial.py --fixture escalate --modes baseline,advisor   # batch 4
```

Raw logs: `.campaign-kit/trials/20261106-210242/` (batch 1), `20261106-211344/` (2),
`20261106-220746/` (3), `20261106-221508/` (4), gitignored, on the machine that ran them.
