# plan.md format

The planner writes this file; `scripts/plan_tool.py check` validates it; the implement and
review skills execute and judge against it. Keep it under ~250 lines: workers read only their
slice and the contracts, so every section must stand on its own.

## Required sections, in this order

```markdown
# <Ticket title>

> slug: <slug> · size: S|M|L · planned at <short sha> on <date>

## Problem
Two to five sentences: what is wrong or missing, for whom, and what "done" looks like.

## Non-goals
Bullets. Things a worker might be tempted to do and must not.

## Frozen contracts
Every shape two slices share, written exactly as code will spell it:
API payloads, function signatures, event names, DB keys, config keys, CLI flags.
One sub-heading per contract, a fenced code block each, and the slice that produces it and
the slices that consume it. Workers may not change these; a change goes back to planning.
"None — slices share no interface" is a valid answer and must be said explicitly.

## Slices
One sub-heading per slice: `### <id> — <title>`
- **Owns:** the globs it may edit (nothing else).
- **Depends on:** slice ids, or none.
- **Does:** 3-8 bullets, concrete enough that a worker who has read only this slice and the
  contracts can do it. Name files and functions with `path:line` where they exist.
- **Acceptance:** observable checks (a test passes, an endpoint returns X, a command prints Y).
- **Gates:** the commands that prove it, taken from the repo (see Gates).
- **Effort:** `medium` (mechanical, pattern exists) or `high` (new logic, tricky edge cases).

## Gates
Where the repo declares its gates (AGENTS.md, CLAUDE.md, CONTRIBUTING.md, package scripts,
Makefile, CI workflow) with the exact commands, and which slice runs which. The integration
gates run once at the end over everything.

## Merge order
Numbered list of slice ids, dependencies first, with one line on the integration risk of each.

## Risks
Ranked bullets: what could break, how the plan contains it, and open questions for the user
(each with the default the plan assumes if nobody answers).

## Manifest
The fenced block below, kept in sync with the sections above.
```

## The manifest block

The fence info string must be exactly `json plan-manifest`:

````markdown
```json plan-manifest
{
  "slug": "login-rate-limit",
  "size": "M",
  "approved": false,
  "slices": [
    {
      "id": "backend-limiter",
      "title": "Rate limiter middleware and config",
      "owns": ["backend/lib/rate-limit.js", "backend/config/limits.js", "backend/test/rate-limit.test.js"],
      "depends_on": [],
      "effort": "high",
      "gates": ["npm --prefix backend test -- rate-limit"],
      "acceptance": ["6th login attempt within 60 s returns 429 with Retry-After"]
    },
    {
      "id": "backend-route",
      "title": "Wire the limiter into POST /login",
      "owns": ["backend/routes/auth.js"],
      "depends_on": ["backend-limiter"],
      "effort": "medium",
      "gates": ["npm --prefix backend test -- auth"],
      "acceptance": ["existing auth tests still pass"]
    }
  ],
  "merge_order": ["backend-limiter", "backend-route"],
  "integration_gates": ["npm --prefix backend test", "node -e \"require('./backend/index')\""]
}
```
````

Rules the checker enforces:
- slice ids are kebab-case and unique, and do not start with `report`, `summary`, `findings`
  or `analysis` (the slice report is `slices/<id>.md`, and Claude Code refuses a subagent's
  Write to `.md` files named that way); `owns`, `gates`, `acceptance` are non-empty;
- `effort` is `medium` or `high` (the implementer is a Sonnet agent; anything needing more
  thought than `high` is a planning problem: split the slice or freeze more of it);
- `depends_on` names known slices, no cycles; `merge_order` lists every slice once, after its
  dependencies;
- two slices with no dependency path between them run **in parallel in the same working
  tree**, so their `owns` patterns must not meet. Narrow the globs or add a dependency;
- `approved` stays `false`. Only the orchestrator flips it, after the user says yes.

## Sizing

| Size | Shape | Typical slices |
|---|---|---|
| S | one area, a few files, no shared interface | 1 |
| M | two or three areas, or one contract between them | 2-4 |
| L | cross-system, migration, security- or data-sensitive, or genuinely ambiguous | 4-8 |

More than 8 slices: the ticket is a campaign or needs splitting into tickets. Say so in Risks.
