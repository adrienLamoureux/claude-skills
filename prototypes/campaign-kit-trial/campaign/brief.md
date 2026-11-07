# Campaign — textkit-spec

## Objective
Make the `textkit` package meet its specification in `spec/` without changing the
specification, and keep the existing tests in `tests/test_basic.py` passing.

## Done criteria
- **spec-pass** — every spec test passes: `python3 tools/score.py spec`, the `spec total` line.
- **guard-tests** — the existing tests keep passing: `python3 tools/score.py tests`, the
  `tests total` line. Must not drop.

## Lanes
- **slugify** — `textkit/slug.py` against `spec/test_slug.py`.
- **durations** — `textkit/durations.py` against `spec/test_durations.py`.
- **cells** — `textkit/cells.py` against `spec/test_cells.py`.

## Guardrails
No outward-facing actions. Never edit `spec/`, `tools/` or `tests/test_basic.py`. Never
commit, push, stash or switch branches.

## Budget and autonomy
At most 4 rounds and 2 actions per round. Autonomy: unattended.

## Assumptions
- The docstrings at the top of each spec file state the rules; the tests are examples of them.

```json brief-manifest
{
  "slug": "textkit-spec",
  "objective": "Make the textkit package pass every test in spec/ without editing spec/, tools/ or tests/test_basic.py, and keep tests/test_basic.py passing.",
  "criteria": [
    {"id": "spec-pass", "metric": "spec tests passing", "target": "48/48",
     "check": "python3 tools/score.py spec; read the 'spec total' line", "baseline": "__SPEC__"},
    {"id": "guard-tests", "metric": "existing tests passing", "target": "7/7 (must not drop)",
     "check": "python3 tools/score.py tests; read the 'tests total' line", "baseline": "__GUARD__"}
  ],
  "lanes": [
    {"id": "slugify", "kind": "code", "scope": "slugify in textkit/slug.py against spec/test_slug.py", "owns": ["textkit/slug.py"]},
    {"id": "durations", "kind": "code", "scope": "parse_duration and format_duration in textkit/durations.py against spec/test_durations.py", "owns": ["textkit/durations.py"]},
    {"id": "cells", "kind": "code", "scope": "escape_cell in textkit/cells.py against spec/test_cells.py", "owns": ["textkit/cells.py"]}
  ],
  "budget": {"max_rounds": 4, "max_actions_per_round": 2},
  "autonomy": "unattended",
  "guardrails": {
    "outward_actions_allowed": [],
    "never": ["edit anything under spec/ or tools/, or tests/test_basic.py", "commit, push, stash or switch branches"]
  },
  "approved": false
}
```
