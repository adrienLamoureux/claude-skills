# Archon MD format (the agent-facing twin)

The MD is read by coding agents through `grep`, `Read`, retrieval chunks, or a link from another
doc. It is also the canonical fact base the HTML is drawn from. Optimise for: finding it, trusting
it, and spending few tokens on it.

## Contents
1. Frontmatter (the index card)
2. Body skeleton
3. Writing rules
4. Example

## 1. Frontmatter (the index card)

An agent should be able to decide "is this the doc I need?" from the frontmatter alone.
Keep it flat: scalars, `[inline, lists]`, or `- item` lists. No nesting.

```yaml
---
title: Job spine — one record for every generation
id: job-spine                  # = file name without .md; stable, kebab-case
doc_type: module               # architecture | module | decision | runbook | concept | onboarding | review
summary: How every image, video and audio generation becomes one Job record that the UI resumes from.
status: current                # current | draft | proposal | deprecated
updated: 2026-10-26            # absolute date
audience: software engineers
source_commit: 617a159         # when facts come from a repo: the commit you read
scope: [backend/lib/jobs/, backend/routes/jobs.js, frontend/src/services/jobs.js]
tags: [jobs, generation, polling, dynamodb, replicate]
aliases: [media job, generation job, job feed]     # other names people search for
related: [docs/architecture.md, docs/archon/story-store.md]
group: Generation pipeline     # optional: the section of the folder's index.html it sits in
order: 20                      # optional: reading position in the folder (integer, gaps of 10)
html_twin: job-spine.html
---
```

Required: `title id doc_type summary status updated tags html_twin`. The build reads title,
summary, status, updated, audience, source_commit and tags for the HTML header, so edit them
here, never in the HTML.

Optional `group` and `order` place the doc in its collection. `build_index.py` sorts by `order`
(docs without one come last, by type then title), shows groups in the order of their first doc,
and gives every page prev/next links in that order. Without `group`, docs group by doc type.

## 2. Body skeleton

Pick the sections from `doc-types.md`; this is the shared frame. Drop a section rather than
leave it thin. Keep this order: an agent that stops reading early still gets the essentials.

```markdown
# <title>

## TL;DR
- 3-6 bullets. Each is a complete fact.

## <Domain sections from the doc-type blueprint>

## Invariants
- MUST/NEVER rules that hold everywhere, each with a ref.

## Gotchas
- Traps that cost someone time before, each with the symptom and the fix.

## Code map
| Path | Role |
|---|---|

## Glossary
- `Term` — meaning. Aliases: x, y.

## Open questions
- What you could not verify, tagged [unverified].

## Sources
- `path/file.js:10-42` — what it shows
- https://... — what it shows
```

## 3. Writing rules

**Findable**
- Headings are descriptive noun phrases with the words people search for: `## Job status
  lifecycle`, not `## How it works`. No duplicate headings.
- Use one term per concept, the same one the code uses. Put the others in `aliases` and the
  Glossary so a grep for any of them lands here.
- Expand an acronym at first use ("Architecture Decision Record (ADR)") or define it in
  `## Glossary`; `check_docs.py` warns on one that is neither, except for the few every
  engineer knows (API, CI, PR, URL, ...).
- Identifiers go in backticks, exactly as in code: `queryBySkPrefix`, `GET /jobs?active=1`,
  `JOB#<id>`, `REPLICATE_API_TOKEN`.

**Trustworthy**
- Every non-obvious claim carries a repo-relative ref: `backend/lib/jobs.js:42` or a range
  `:42-60`. The checker verifies the path and line exist, so a ref that rots is caught.
  A file that no longer exists goes on a line that says so ("deleted in `717139e`"); the
  checker skips those lines.
- An untagged fact means "verified in the source". Tag the rest at the end of the line:
  `[inferred]` (deduced, not seen), `[unverified]` (heard or assumed), `[proposal]` (not built).
- Absolute dates and the `source_commit` you read. Never "recently" or "currently".

**Cheap to read**
- Facts as bullets: `subject — fact (ref)`. No narrative, no transitions, no marketing,
  no restating the heading.
- Tables when 3+ items share attributes. Code blocks only for code an agent will copy.
- Diagrams: only when the structure (state machine, call graph) is hard to list. Reuse the HTML
  Mermaid source without the `:::kind` tags. Otherwise write the edges as a list:
  `- api → db: put JOB#id`.
- No HTML, images, emoji, bold-for-emphasis, or decorative rules.
- Soft cap ~2,500 words (~3.5k tokens). Beyond that, split by subtopic and link through `related`.

**Self-contained sections**
- Retrieval often returns one section alone. Each `##` must make sense without the others:
  name the subject ("The job worker retries…"), never "it", "as above", "see below".

## 4. Example

```markdown
---
title: Job spine — one record for every generation
id: job-spine
doc_type: module
summary: How every generation becomes one Job record that the UI resumes from.
status: current
updated: 2026-10-26
source_commit: 617a159
tags: [jobs, generation, polling]
aliases: [media job, generation job]
html_twin: job-spine.html
---

# Job spine — one record for every generation

## TL;DR
- Every generation (image, video, audio; any provider) writes one `Job` item (`backend/lib/jobs/store.js:12`).
- The UI resumes in-flight work from `GET /jobs?active=1`, not from a browser cache (`frontend/src/services/jobs.js:30`).
- Provider callbacks update the job; the client never writes job status.

## Job status lifecycle
- `queued → running → succeeded | failed | cancelled` (`backend/lib/jobs/status.js:5-11`).
- Terminal states never change again; a retry creates a new job [inferred].

## Invariants
- NEVER call `queryBySkPrefix` with positional args: it takes one object and returns `[]` otherwise (`backend/lib/media-store.js:88`).
```
(Paths in this example are illustrative. Yours must be real: the checker opens them.)
