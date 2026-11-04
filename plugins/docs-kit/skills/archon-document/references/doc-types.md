# Doc-type blueprints

Each blueprint lists the sections in order, with the main HTML component for each and what the
MD section holds. Both twins share section names so a reader can jump between them. Every type
starts with the TL;DR and ends (MD only) with Glossary, Open questions and Sources when they
have content.

## Contents
- architecture · module · decision · runbook · concept · onboarding · review

## architecture — how a system fits together

| Section | HTML (main visual) | MD |
|---|---|---|
| System context | flowchart: users, system, external deps | actors + external systems, one line each |
| Components | flowchart or cards with `data-kind` | table: component, path, responsibility, owner |
| Key flows | sequenceDiagram per flow (2-3 flows max) | numbered steps with refs |
| Data model | erDiagram or kv | entities, keys, access patterns |
| Deployment | flowchart TB with subgraphs | stack/resources list, env/config keys |
| Cross-cutting | cards: auth, observability, cost, limits | bullets per concern |
| Invariants & gotchas | callouts | Invariants + Gotchas sections |

## module — one module, feature or subsystem

| Section | HTML (main visual) | MD |
|---|---|---|
| What it does | cards (2-4 responsibilities) | purpose + boundaries (what it does NOT do) |
| Code map | table or kv | Code map table: path, role |
| Main flow | sequenceDiagram or steps | numbered steps with refs |
| States / data | stateDiagram-v2 or erDiagram | lifecycle, schema, keys |
| API surface | table: endpoint/function, input, output | signatures and contracts |
| Extending it | steps | how to add a case, where to register it |
| Invariants & gotchas | callouts | Invariants + Gotchas sections |

## decision — an ADR: what we chose and why

| Section | HTML (main visual) | MD |
|---|---|---|
| Context | 2-3 bullets + optional flowchart of the problem | forces, constraints, numbers |
| Options | cards, one per option, `data-kind` ok/warn/danger | each option: summary, pros, cons |
| Comparison | table with `ar-yes`/`ar-no`/`ar-part` | same table |
| Decision | callout `is-tip` | the decision in one sentence + rationale bullets |
| Consequences | cards: gains (ok) vs costs (danger) | positive, negative, follow-ups |
| Revisit when | steps or bullets | triggers that reopen the decision |

Status: `proposal` until accepted, then `current`; `deprecated` when superseded (link the successor in `related`).

## runbook — do a task or fix an incident

| Section | HTML (main visual) | MD |
|---|---|---|
| When to use | callout | symptoms / triggers, exact alert or error text |
| Before you start | kv: access, tools, env | prerequisites |
| Steps | steps, with commands in `<pre>` | numbered steps, one command block each |
| Verify | steps or table: check, expected | checks with expected output |
| Roll back | steps, callout `is-danger` | rollback steps |
| Troubleshooting | table: symptom, cause, fix | same table |

Commands must be copy-pasteable and real. Mark destructive steps with a `is-danger` callout.

## concept — explain an idea, pattern or technology

| Section | HTML (main visual) | MD |
|---|---|---|
| The mental model | one diagram that captures the idea | definition + the model in 3-5 bullets |
| How it works | steps or sequenceDiagram | mechanism, step by step |
| In this codebase | flowchart / table linking concept to files | where it appears, with refs (skip if none) |
| When to use / avoid | cards ok vs danger | criteria lists |
| Compared with | table | same table |
| Pitfalls | callouts | Gotchas section |

## onboarding — get a new engineer productive

| Section | HTML (main visual) | MD |
|---|---|---|
| The map | architecture flowchart, few nodes | system summary + repo layout table |
| Run it locally | steps with commands | exact commands, env setup |
| Where things live | table: "I want to change X" → path | same table |
| Conventions | cards (naming, tests, PRs, style) | rules with refs to config files |
| First tasks | steps | ordered starter tasks with links |
| Who / where to ask | kv | channels, owners, docs |

## review — audit, code review, incident or postmortem

| Section | HTML (main visual) | MD |
|---|---|---|
| Verdict | stats + callout | overall result in 1-2 bullets |
| Scope | kv | what was and wasn't reviewed, commit, date |
| Findings | table: id, severity badge, finding, ref | one subsection per finding: evidence, impact, fix |
| Timeline (incidents) | steps or timeline | timestamped events |
| Root cause | flowchart of the causal chain | causes with evidence |
| Actions | table: action, owner, status | same table |

Severity uses badges: `is-risk` (high), `is-unverified` (medium / needs check), plain (low).
