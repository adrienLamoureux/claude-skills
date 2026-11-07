# campaign-kit trial: `/goal`, the advisor and Opus escalation

Do `/goal`, an Opus advisor or the judge's Opus escalation make a campaign-kit run cheaper,
more complete or better? This trial runs one fixed campaign headless in four modes and scores
every run itself.

```bash
python3 -I prototypes/campaign-kit-trial/trial.py --self-test                 # fixtures + tool rules, no claude calls
python3 -I prototypes/campaign-kit-trial/trial.py --dry-run                   # set up the runs, print commands
python3 -I prototypes/campaign-kit-trial/trial.py                             # spec fixture, 4 modes x 1 run
python3 -I prototypes/campaign-kit-trial/trial.py --fixture blackbox --budget 5
python3 -I prototypes/campaign-kit-trial/trial.py --modes baseline,advisor --runs 3
```

The fixture repos run in `<tmp>/campaign-kit-trial/<stamp>/`, outside this repository, so the
agents see an ordinary project. Each run's logs (`stream.jsonl`, the full `stream-json` event
stream), campaign folder, diff and `result.json` are copied to `.campaign-kit/trials/<stamp>/`
(gitignored), with `results.md` / `results.json` for the batch.

## Modes

| Mode | Prompt | Flag |
|---|---|---|
| `baseline` | `/campaign-kit:campaign textkit-spec` + the headless note | — |
| `advisor` | same | `--advisor opus` |
| `goal` | `/goal Run /campaign-kit:campaign textkit-spec until a "campaign textkit-spec:" status line says done, waiting for you, or blocked.` + the headless note | — |
| `advisor-goal` | the goal prompt | `--advisor opus` |

Everything else is identical: `claude -p --model sonnet --setting-sources project,local
--strict-mcp-config --permission-mode dontAsk`, the same allow-list (`TOOLS`),
`--max-budget-usd` per run, and `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` so subagents finish
inside the turn. The judge's Opus escalation is part of the kit, so it can happen in any mode.

## The campaign

`fixture/` is a small Python package, `textkit`, with three deliberately naive modules:
`slugify`, `parse_duration` / `format_duration`, and `escape_cell` (a CSV formula-injection
guard). `spec/` is the specification (48 tests, 25 passing at the start); `tests/test_basic.py`
is a guard suite (7 tests, all passing).

Two fixtures share it:

- **`spec`** (`campaign/`): criteria `spec-pass` 48/48 and `guard-tests` 7/7; at most 4 rounds.
- **`blackbox`** (`blackbox/`): adds `acceptance-pass` 36/36, measured by `tools/accept.py`. That
  script runs the `holdout/` cases from a folder outside the repo, like a CI job you cannot
  edit, and prints each failing input with its expected value. Round 1 still targets only the
  spec, so lanes come back `partial`, and the judge, the advisor rule and the escalation rule
  all have a real failure to react to. At most 5 rounds.

Both use three code lanes (one per module) and **2 actions per round**, so at least two rounds
are needed. Autonomy is `unattended`, and `spec/`, `tools/` and the guard tests must not be
edited. The trial writes the baselines, approves the brief and round 1, and starts at `execute`,
so the interview and strategist are not tested. The traps that tend to fail a first attempt:
`ø` and `ß` have no NFKD decomposition, Python's `round(2.5)` is 2, and the text `"-5"` is a
number, not a formula.

## What is scored

The trial scores the final `textkit/` itself, against pristine copies of the tests:

| Measure | Why |
|---|---|
| Spec and guard tests passed | completion; the checker's own claim is recorded next to it |
| `holdout/` (36 cases; the black-box fixture's acceptance suite) | quality on the spec fixture; completion on the black-box one |
| `holdout2/` (24 cases nobody sees in either fixture) | quality: do the fixes follow the rules or only the examples |
| Protected files changed (`spec/`, `tools/`, `tests/test_basic.py`, compared with the state after setup) | guardrail kept |
| Files changed outside the lanes' owned paths | ownership kept |
| Rounds, verdicts, lane statuses per round, `campaign_tool.py next` at the end | did the loop reach `done` with `outcome.md` and `recap.md` |
| Opus lane runs (actions with `"model": "opus"`, runner launches with `model: opus`) | did the judge escalate, and did the orchestrator pass it on |
| Advisor calls (main session / subagents) | `server_tool_use` blocks named `advisor` |
| Turn ends, evaluator USD (Haiku) | `/goal` continuations and what they cost |
| Cost, minutes, turns, permission denials | from the final `result` event |

`reference/` holds a solution that scores 48/48, 7/7, 36/36 and 24/24. `--self-test` checks
both fixtures against it and checks `campaign_tool.py`'s rules: the status lines, Opus allowed
only right after a `fail` or `partial` lane, and never twice in a row. Nothing in `reference/`,
`holdout/` or `holdout2/` is copied into a run's repo.

## Reading the results

One run per mode shows whether a feature works and what it costs. It does not show a quality
difference: two identical dev-kit trial runs differed by 7% in cost. For a quality claim, run
`--runs 3` or more of the modes being compared.

Results so far: `RESULTS.md`.
