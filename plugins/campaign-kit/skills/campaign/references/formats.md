# Campaign run folder formats

A campaign is a ReAct loop on disk: each round is **Thought** (the round plan), **Action** (lane
reports), **Observation** (the check) and a **judgement** that writes the next Thought. Files are
the memory; every agent starts cold and reads only what its brief names.

```
.campaign-kit/<slug>/
  interview.md          the user's answers, verbatim where it matters (orchestrator)
  brief.md              objective, done criteria, lanes, budget, autonomy, guardrails (strategist)
  ledger.md             "## Current state" on top, then one entry per round (judge only)
  rounds/<n>/plan.md    Thought + actions for round n (strategist for round 1, judge after)
  rounds/<n>/<lane>.md  Action report per lane (runner)
  rounds/<n>/check.md   Observation: lane statuses, criteria measured, regressions (checker)
  rounds/<n>/review.md  judgement and verdict (judge)
  outcome.md            final report (judge, on a stop verdict)
```

Machine-read blocks are fenced ` ```json <kind>-manifest ` and `campaign_tool.py` validates them.
Everything around them is free Markdown for humans.

**File names.** Claude Code refuses a subagent's Write to any `.md` file whose name starts with
`report`, `summary`, `findings` or `analysis` (any case). So the final report is `outcome.md`,
and lane ids, which name the lane reports, may not start with those words (`campaign_tool.py
check` rejects them). Runs started before campaign-kit 0.2.0 have `report.md` instead; the tool
accepts either.

## brief.md

Sections: `## Objective`, `## Done criteria`, `## Lanes`, `## Guardrails`, `## Budget and
autonomy`, `## Assumptions`, then the manifest:

```json brief-manifest
{
  "slug": "coverage-80",
  "objective": "Raise line coverage of packages/api and packages/web to at least 80% without slowing CI by more than 10%.",
  "criteria": [
    {"id": "api-coverage", "metric": "line coverage of packages/api", "target": ">= 80%",
     "check": "npm --prefix packages/api test -- --coverage; read 'All files' Lines column"},
    {"id": "ci-time", "metric": "CI test job duration", "target": "<= 1.10 x baseline",
     "check": "time npm test at repo root, median of 2 runs"}
  ],
  "lanes": [
    {"id": "api-tests", "kind": "code", "scope": "unit tests for packages/api services", "owns": ["packages/api/test/**"]},
    {"id": "web-tests", "kind": "code", "scope": "component tests for packages/web", "owns": ["packages/web/src/**/*.test.tsx"]}
  ],
  "budget": {"max_rounds": 5, "max_actions_per_round": 3},
  "autonomy": "checkpoint-on-pivot",
  "guardrails": {
    "outward_actions_allowed": [],
    "never": ["change production code to make a test pass", "push", "delete tests"]
  },
  "approved": false
}
```

- **criteria** are measurable and each has a `check` a Sonnet checker can run or follow
  exactly. The checker adds `"baseline": "<value>"` to each before the user approves.
- **lanes** are independent workstreams. `kind` is `code`, `research`, `docs`, `data`, `ops` or
  `other`; code lanes must say which paths they `owns`.
- **autonomy:** `checkpoint-each-round` (the user approves every round), `checkpoint-on-pivot`
  (only approach changes), `unattended` (runs to a stop verdict).
- **guardrails.outward_actions_allowed** lists the outward-facing actions runners may take
  (e.g. "open draft PRs"). Empty means none: no push, deploy, send, publish, purchase or delete.

## rounds/<n>/plan.md

Sections: `## Thought` (state in two or three sentences, what this round tries and why, what
would change the approach), `## Actions` (one sub-heading per lane), then:

```json round-manifest
{
  "round": 2,
  "thought": "api-tests reached 71%; the gap is in services/billing. web-tests is blocked on a missing test util; add it first.",
  "actions": [
    {"lane": "api-tests", "task": "Add unit tests for services/billing/*.ts covering refunds and proration.",
     "owns": ["packages/api/test/billing/**"], "effort": "medium",
     "acceptance": ["new tests pass", "packages/api line coverage >= 76%"]},
    {"lane": "web-tests", "task": "Add renderWithProviders helper and cover Checkout.tsx.",
     "owns": ["packages/web/src/test-utils/**", "packages/web/src/checkout/**/*.test.tsx"], "effort": "high",
     "acceptance": ["helper used by at least 3 tests", "Checkout tests pass"]}
  ],
  "approved": false
}
```

One action per lane per round; all actions of a round run in parallel, so code lanes' `owns`
must not meet. `effort` is `medium` or `high` (runners are Sonnet). A lane may appear that is
not in the brief only after a `pivot` verdict.

## rounds/<n>/<lane>.md (runner)

`## Status` (done / partial / failed / needs-human), `## What I did`, `## Evidence` (commands
and their key output, links, files), `## Acceptance` (each: met / not met / unverified),
`## Surprises`, `## Suggested next step`, and `## Files to place` when needed (below).

A deliverable whose file name the harness blocks (say `docs/report.md`) is written next to it
under a name that does not start with a blocked word (`docs/draft-report.md`) and listed under
`## Files to place` as `` `docs/draft-report.md` -> `docs/report.md` ``. The orchestrator, which
the rule does not cover, moves each one into place before the checker runs.

## rounds/<n>/check.md (checker)

Free Markdown with the evidence, then:

```json check-manifest
{
  "round": 2,
  "lanes": [{"lane": "api-tests", "status": "pass"}, {"lane": "web-tests", "status": "partial"}],
  "criteria": [{"id": "api-coverage", "value": "76.4%", "met": false},
               {"id": "ci-time", "value": "1.04 x", "met": true}],
  "regressions": []
}
```

Lane `status`: `pass`, `partial`, `fail`, `needs-human`. A lane report's claims count only
when the checker reproduced them.

## rounds/<n>/review.md (judge)

`## Verdict`, `## Progress` (criteria vs last round), `## What worked / what did not`,
`## Next` (the reasoning for the next round), then:

```json review-manifest
{
  "round": 2,
  "verdict": "continue",
  "reason": "coverage +5.4 pts; billing gap closing; web lane unblocked",
  "criteria": [{"id": "api-coverage", "value": "76.4%", "met": false},
               {"id": "ci-time", "value": "1.04 x", "met": true}],
  "needs_user": []
}
```

Verdicts: `continue` (same lanes, next tasks), `pivot` (lanes added, dropped or re-scoped;
objective and criteria unchanged), `stop-done` (every criterion met, verified by the checker),
`stop-blocked` (cannot progress without the user: access, a decision, a change to objective or
criteria), `stop-budget` (rounds exhausted). On `continue` or `pivot` the judge also writes
`rounds/<n+1>/plan.md`; on a stop verdict it writes `outcome.md` (below). The judge never changes
the objective or the criteria.

## outcome.md (judge)

The final report, written once, on a stop verdict or in final mode: `## Outcome` (each
criterion baseline -> final, met or not), `## Per lane` (what each lane delivered),
`## What did not work`, `## Open items`, `## Next for the user` (needs-human items first). No
manifest; `campaign_tool.py next` returns `done` once the file exists.

## ledger.md (judge only)

```markdown
## Current state
<= 200 words, rewritten every round: where each criterion stands, what is known to work,
what failed and why, open risks. Agents read this instead of the whole history.

## Round 2 — continue
- Thought: <one line from the round plan>
- Actions: api-tests (pass), web-tests (partial)
- Observation: api-coverage 71.0 → 76.4%; ci-time 1.04 x
- Judgement: <one or two lines>
```

Older rounds are never rewritten; only `## Current state` is.
