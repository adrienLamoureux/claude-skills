---
title: Cognitive load — designing the kits around human attention
id: cognitive-load
doc_type: concept
summary: Human attention (reading volume, context switches, unknown terms, oversight fatigue) is now the AI-SDLC bottleneck — what the research says, nine ranked options to cut the load, and where each one shipped (dev-kit 1.4.0, campaign-kit 0.4.0, docs-kit 1.1.0, focus-kit 0.1.0).
status: current
updated: 2026-11-07
audience: software engineers
source_commit: fc8c004
scope: [plugins/dev-kit/, plugins/campaign-kit/, plugins/docs-kit/, plugins/focus-kit/]
tags: [ai-sdlc, cognitive-load, attention, fatigue, context-switching, jargon, review, output-style, hooks, human-factors]
aliases: [human bottleneck, oversight tax, AI brain fry, review fatigue, approval fatigue, attention residue, reading load, focus-kit, decision card, review map]
related: [docs/ai-sdlc/adopt-plugins-ci.md, docs/ai-sdlc/scheduled-checks.md, plugins/dev-kit/README.md, plugins/campaign-kit/README.md, plugins/focus-kit/README.md]
group: Guides
order: 40
html_twin: cognitive-load.html
---

# Cognitive load — designing the kits around human attention

## TL;DR
- Agents get cheaper and faster each release; the person who reads, decides and checks does not. Human attention is now the bottleneck of the AI-SDLC.
- Four limits recur: reading volume, context switches between sessions, unknown terms, and fatigue from overseeing AI output. Oversight fatigue has the strongest evidence and the highest cost.
- The rule from cognitive load theory: cut effort spent on format and search (extraneous load), keep effort spent on understanding (germane load). Removing all effort lowers comprehension.
- Before these options, the kits already capped agent replies at 80-150 words, ended runs with an 8-line recap, and rendered docs twice (HTML for people, MD for agents).
- All nine options shipped on 2026-11-07 across dev-kit 1.4.0, campaign-kit 0.4.0, docs-kit 1.1.0 and a new focus-kit 0.1.0; `## Options built` lists each one's files and what is verified.
- `focus-kit:Reader-first` beat the built-in `Concise` style in a small benchmark: 173 against 205 mean words, and it ended with the user's next move in 3 of 3 replies against 0 of 3.
- Still unmeasured: whether the review map catches a planted bug, and how many words a human reads per ticket before and after. Tuning against those is campaign-shaped.

## The four limits of human attention
| Limit | What happens to the person | Evidence |
|---|---|---|
| Reading volume | Long replies, plans and diffs exceed working memory; people skim and miss the one risky line | DORA 2025 links AI adoption to more delivery instability and recommends small batches [unverified: secondary summaries] |
| Context switches | Returning to a session is fast; rebuilding the mental model is slow; unfinished tasks leave attention residue | Mark, Gudith and Klocke, CHI 2008: interrupted workers finished faster but with more stress [unverified]; Leroy 2009 on attention residue [unverified] |
| Unknown terms | Experts forget what readers do not know (curse of knowledge); jargon defined with more jargon does not help | Jargon support personalised to the listener beat generic support on comprehension (arXiv 2508.10239) |
| Oversight fatigue | Checking AI output needs sustained, sceptical attention; confident output slips past tired reviewers | BCG, March 2026, 1,488 US workers: 14% reported "AI brain fry", linked to more errors and intent to quit; overseeing several agents was the riskiest pattern |

- Overconfidence hides the cost: experienced developers were 19% slower with AI but believed they were 20% faster (METR, arXiv 2507.09089, 16 developers, 246 tasks).
- Trust shifts effort: knowledge workers with more confidence in GenAI reported less critical thinking, and their work moved from producing to verifying (Lee et al., CHI 2025, 319 workers).
- Full delegation costs understanding: developers learning a new library with AI scored about 50% on a quiz, against 67% by hand. Those who also asked conceptual questions scored highest (Anthropic, January 2026, arXiv 2601.20245).

## Design principles for human attention
1. Answer first. Line 1 is the decision or result; detail is one file away (progressive disclosure).
2. Point, do not dump. Show the 1-3 places that need human eyes, and say what was already machine-checked.
3. Small batches. A diff a person can hold in mind beats a large one reviewed tired.
4. Close every loop. Each turn ends with "done" or "waiting on you for X"; open loops become attention residue.
5. One inbox, few pings. One place lists what waits on the human; notifications fire on done or blocked only.
6. Define on demand, per person. Gloss only the terms this reader does not know; explain deeper when asked.
7. Keep the human's model current. Cut extraneous effort, not understanding; an opt-in explain step beats silent delegation.
8. Gate by reversibility. Stop for irreversible or outward-facing steps; let reversible ones run and report.

## What the kits did for attention before the options
| Mitigation | Limit | Where |
|---|---|---|
| Agents write detail to files and reply in at most 80-150 words | reading volume | `README.md:102` |
| Every run ends with `recap.md`, at most 8 lines | reading volume, context switches | `README.md:37`, `plugins/campaign-kit/skills/campaign/references/formats.md:145-164` |
| The reviewer replies in 120 words with the single most important finding | reading volume, fatigue | `plugins/dev-kit/agents/dev-reviewer.md:66-69` |
| `review.md` separates Must fix, Should fix, Unverified and Residual risks | fatigue | `plugins/dev-kit/agents/dev-reviewer.md:44-50` |
| A two-line progress note after each campaign round; a one-line blocked status | context switches | `plugins/campaign-kit/skills/campaign/SKILL.md:56-64` |
| Campaign checkpoints: every round, on pivots (default) or unattended | fatigue | `plugins/campaign-kit/skills/interview/SKILL.md:54-55` |
| Ticket sizes cap a plan at 8 slices; more means a campaign or split tickets | reading volume | `plugins/dev-kit/skills/plan/references/plan-format.md:112-120` |
| Twin docs: diagrams-first HTML for people, lean MD for agents; the checker caps sentences at 25 words | reading volume, unknown terms | `plugins/docs-kit/skills/archon-document/SKILL.md:120`, `plugins/docs-kit/skills/archon-document/scripts/check_docs.py:34-35` |

Gaps before the options: no pointer into a diff, gates with open questions and no default, no list of runs waiting across sessions, no glosses, and no shape rule for the main session's own replies.

## Options to cut the load
| # | Option | Limit | Lives in | Effort | Token effect | Value |
|---|---|---|---|---|---|---|
| 1 | Review map: where to look, what was machine-checked | fatigue | dev-kit reviewer, campaign checker | S | about +50-100 output tokens per review [inferred] | high |
| 2 | Decision card at every human gate | fatigue, reading | dev-kit plan, campaign interview and review | S | neutral | high |
| 3 | Reader-first output style | reading, terms | new plugin `focus-kit` | S | lower output (measured: 173 against 266 words) | high |
| 4 | Inbox and resume lines | context switches | `focus-kit` script, `SessionStart` hook, status line | M | one short hook output per session | high with several sessions |
| 5 | Diff budget per slice | fatigue, reading | dev-kit planner and checker | S | neutral | medium |
| 6 | Explain on demand with a personal vocabulary | terms | `focus-kit` skill plus a memory file | S-M | paid only when asked | medium |
| 7 | Pacing defaults for concurrency and notifications | fatigue, context switches | focus-kit inbox, campaign-kit loop, READMEs | S | none | medium |
| 8 | Plain-words problem and opt-in teach-back | terms, comprehension | dev-kit plan format, built-in `Explanatory` style | S | small | medium |
| 9 | Glossary lint and visual recaps | terms, reading | docs-kit checker, focus-kit runs page | S-M | small | low-medium |

All nine options are built; `## Options built` gives the files and what was tested.

### Option 1 — review map in review.md
- Add `## Where to look` to `review.md`: at most 3 hunks, each with `path:line`, the question a human should ask of it, and why a machine cannot answer it.
- Add `## Machine-checked`: what the gates and the reviewer already proved, so the human can skip it.
- The recap gains one line: `Look at: path:line — question`.
- Measure: seed a known bug in the `prototypes/ai-sdlc/` trial ticket; the map should point at it in at least 4 of 5 runs.

### Option 2 — decision card at every gate
- Every stop that needs the human prints the same 5 lines: `Decide`, `Recommend`, `If wrong`, `Undo cost`, `On "ok"` (what happens if the user just says ok).
- It applies to plan approval (`plugins/dev-kit/skills/plan/SKILL.md:60`), campaign brief approval, checkpoints and blockers.
- The undo cost points attention at one-way doors; a cheap undo needs a glance.
- Measure: decisions per ticket, and the share answered with the default.

### Option 3 — reader-first output style
- A plugin can ship output styles in `output-styles/`; the user picks one in `/config` or with the `outputStyle` setting. A plugin style is named `<plugin>:<style>`, so this one is `focus-kit:Reader-first`. It sets `force-for-plugin: true`, so it is on in every session once focus-kit is installed, with no selection.
- Rules: result or decision in line 1; about 120 words at most unless asked; detail goes to a file named by path; one question at a time; an unfamiliar term gets a gloss of at most 8 words at first use; the reply ends with `Your move: …` or `Nothing needed`.
- The style sets `keep-coding-instructions: true`, or it drops Claude Code's coding instructions.
- The built-in `Concise` style was the baseline to beat. Result on Sonnet, 3 prompts, 1 run each: default 266 mean words, `Concise` 205, `Reader-first` 173; only `Reader-first` ended with the next move (3 of 3). All three put the answer in line 1 (`prototypes/focus-kit-trial/RESULTS.md`).
- Measure next: `bench_styles.py --runs 3`; replies still average above the ~120-word target.

### Option 4 — inbox and resume lines
- A script lists every run folder under `.dev-kit/` and `.campaign-kit/` that waits on the human, one line each, oldest first: `slug · step · what it needs · since`.
- A `SessionStart` hook shows the user the first 4 runs and gives Claude the whole list as context; a status-line segment, which the user adds to their own settings because a plugin cannot set one, shows the count.
- Every kit turn that stops ends with a 3-line resume block: where the run is, what it did, what it needs.
- Claude Code's `/recap` covers one session; the inbox spans runs and sessions.

### Option 5 — diff budget per slice
- The planner states an expected size per slice; the checker flags a slice whose diff exceeds it by a set factor.
- The review map is split by slice, so each check stays small.

### Option 6 — explain on demand with a personal vocabulary
- `/focus-kit:explain <term | last>` defines a term in this repo's context in at most 80 words: what it is, where it lives (`path:line`), why it matters here. With `last`, it restates the previous reply one level simpler.
- `~/.claude/focus-kit/vocabulary.md` lists the terms the user already knows; the `SessionStart` hook hands it to Claude, so the output style glosses only the others.

### Option 7 — pacing defaults for concurrency and notifications
- Recommend supervising at most 3 sessions or agents at once. BCG found the most strain among people overseeing several tools and agents; the peak at 3 comes from secondary coverage [unverified].
- Campaign lanes report through one checkpoint per round; unattended `/goal` runs end only on a final status line.
- No extra `Notification` hook: Claude Code already notifies when a session waits for the user, so a second layer would add pings. Permission prompts are the frequent interruption; `/fewer-permission-prompts` allow-lists the repeated read-only ones.
- The inbox and the session-start message add a pacing line past 3 open runs.

### Option 8 — plain-words problem and opt-in teach-back
- `plan.md` opens with a 3-line `## In plain words`: the problem, the change and the risk, with no identifiers.
- For unfamiliar code, the user can opt in to the built-in `Explanatory` or `Learning` output style during implement; both cost more output tokens by design.

### Option 9 — glossary lint and visual recaps
- `check_docs.py` warns on an acronym used without a first-use expansion or a `## Glossary` entry.
- A static HTML page with a card per run of either kit (state, needs, recap, file links), rebuilt by a `PostToolUse` hook whenever a run's `resume.md` is written; it reloads every minute in an open tab. A page others can see stays with campaign-kit's project-artifact offer (`ROADMAP.md:60`).

## Options built
| # | Shipped in | Key files | Verified | Not verified |
|---|---|---|---|---|
| 1 | dev-kit 1.4.0, campaign-kit 0.4.0 | `plugins/dev-kit/agents/dev-reviewer.md`, `plugins/campaign-kit/agents/campaign-judge.md`, `plugins/campaign-kit/agents/campaign-checker.md` | plugins validate | seeded-bug catch rate |
| 2 | dev-kit 1.4.0, campaign-kit 0.4.0 | the `## Decision card` section of every gate skill | plugins validate | a live run's card |
| 3 | focus-kit 0.1.0 | `plugins/focus-kit/output-styles/reader-first.md` (`force-for-plugin`) | benchmark against default and `Concise`; applied headless with no style selected | more runs, other models |
| 4 | focus-kit 0.1.0, both kits | `plugins/focus-kit/scripts/focus_tool.py`, `plugins/focus-kit/hooks/hooks.json`, the `## Resume block` section of every gate skill | 7 fixture runs; a live headless session received the inbox | the message in the desktop app and VS Code |
| 5 | dev-kit 1.4.0 | `plugins/dev-kit/skills/plan/scripts/plan_tool.py` (`size`, `max_lines` checks), `plugins/dev-kit/agents/dev-checker.md` | scratch repo with edits, a rename and an untracked file | a live wave |
| 6 | focus-kit 0.1.0 | `plugins/focus-kit/skills/explain/SKILL.md`, `focus_tool.py vocab` | live `/focus-kit:explain plan-manifest` on this repo, USD 0.09 | that a known term stops being glossed |
| 7 | focus-kit 0.1.0, campaign-kit 0.4.0 | `focus_tool.py` pacing line, `plugins/campaign-kit/skills/campaign/SKILL.md` | fixture with 6 open runs | effect on fatigue |
| 8 | dev-kit 1.4.0, campaign-kit 0.4.0 | `plugins/dev-kit/skills/plan/references/plan-format.md`, `plan_tool.py check` warnings, `plugins/dev-kit/README.md` | warnings on a 4-line section and on code names | a live plan |
| 9 | docs-kit 1.1.0, focus-kit 0.1.0 | `plugins/docs-kit/skills/archon-document/scripts/check_docs.py` (`check_acronyms`), `focus_tool.py page` and `on-write` | the four `docs/ai-sdlc/` docs and a test doc; the page in a browser; the hook in a live headless session | — |

- Eval suite: `plugins/focus-kit/evals/` (two trigger cases, one should-not-fire), not run yet.

## When cognitive-load work fits a campaign
- The research and the build needed no campaign: one deliverable each, no rounds.
- Tuning is campaign-shaped: halve the words a human reads per approved ticket while the seeded-bug catch rate stays at 4 of 5 or better. Lanes: reviewer prompt, gate format, output style; the checker runs the trial harness with a word counter and the seeded bug.

## Measuring cognitive load
| Signal | How | Cheap |
|---|---|---|
| Words the human reads per ticket | sum of main-session replies, `recap.md` and the review map, from transcripts | yes |
| Decisions per ticket, share on default | count of gate stops in transcripts | yes |
| Seeded-bug catch rate | plant a known bug; check that the review map points at it | yes |
| Undefined terms per doc | glossary lint count | yes |
| Output tokens | trial cost logs | yes |
| Perceived workload | a short NASA-TLX self-rating after a few real tickets [unverified fit] | no |

- Only self-report measures fatigue; transcripts measure the rest.

## Gotchas
- Shorter can hide risk. A crisp summary invites trust, and trust in AI lowers critical thinking (Lee et al.). Keep `Unverified` and `Residual risks` in the card, not only in the file.
- Removing all effort removes understanding. Cut format and search effort; keep the explain path.
- A custom output style replaces part of the system prompt; without `keep-coding-instructions: true` it drops the coding instructions.
- Claude Code reads output-style files at start; restart after editing one.
- More notifications mean more interruptions. Notify only on states the human must act on.
- Users reported in 2026 that the away summary did not show in some desktop and VS Code builds [unverified]; check it before the inbox relies on it.

## Glossary
- `cognitive load` — the working-memory effort a task demands. Aliases: mental load.
- `extraneous load` — effort spent on format, search and noise rather than the task; the part to cut.
- `germane load` — effort that builds understanding; the part to keep.
- `attention residue` — attention left on an unfinished task after switching away (Leroy 2009).
- `oversight tax` — extra effort and fatigue from checking AI output; `AI brain fry` is its extreme (BCG 2026).
- `automation complacency` — monitoring that drops as automation proves reliable. Aliases: vigilance decrement.
- `progressive disclosure` — show the essential first; reveal detail on request.
- `decision card` — the 5-line gate format of option 2: `Decide`, `Recommend`, `If wrong`, `Undo cost`, `On "ok"`.
- `review map` — `## Where to look` plus `## Machine-checked`, option 1.
- `resume block` — `resume.md`'s three lines (`Where`, `Did`, `Needs`), option 4.
- `BCG` — Boston Consulting Group, authors of the 2026 "AI brain fry" survey.
- `DORA` — DevOps Research and Assessment, Google's yearly software delivery report.
- `METR` — Model Evaluation and Threat Research, a nonprofit that ran the 2025 developer trial.
- `CHI` — the ACM Conference on Human Factors in Computing Systems.

## Open questions
- Whether `Reader-first` keeps its lead over `Concise` across more runs and on Opus; one run per prompt on Sonnet so far.
- How much option 1 adds to review cost; not measured.
- Whether `SessionStart` hook output reaches the human in the desktop app as well as the CLI [unverified].
- The productivity peak at 3 tools comes from secondary coverage of the BCG study [unverified].

## Sources
- https://www.bcg.com/publications/2026/when-using-ai-leads-to-brain-fry — BCG, March 2026, 1,488 workers, "AI brain fry"
- https://www.helpnetsecurity.com/2026/03/09/harvard-business-review-ai-workplace-fatigue-report/ — coverage of the same study: effort, fatigue and overload figures
- https://arxiv.org/pdf/2507.09089 — METR randomized trial: 19% slower, perceived 20% faster
- https://advait.org/files/lee_2025_ai_critical_thinking_survey.pdf — Lee et al., CHI 2025: trust in GenAI and critical thinking
- https://www.anthropic.com/research/AI-assistance-coding-skills — Anthropic study on AI assistance and skill formation, January 2026
- https://www.arxiv.org/pdf/2601.20245 — the same study's preprint
- https://arxiv.org/abs/2508.10239 — personalised real-time jargon support
- https://www.splunk.com/en_us/blog/learn/state-of-devops — DORA 2025 summary: throughput, instability, small batches
- https://code.claude.com/docs/en/output-styles — built-in styles, plugin `output-styles/`, `keep-coding-instructions`
- https://code.claude.com/docs/en/hooks — `SessionStart`, `Notification` and `Stop` events
- https://code.claude.com/docs/en/whats-new/2026-w17 — session recap (away summary) and `/recap`
- https://www.youonai.ai/fieldguide/med/interruption_costs.html — secondary summary of Mark and Leroy on interruptions [unverified]
- `README.md:37`, `README.md:102` — kit recap and reply caps
- `plugins/dev-kit/agents/dev-reviewer.md:44-69` — `review.md` sections, the review map and the reviewer's reply cap
- `prototypes/focus-kit-trial/RESULTS.md` — output-style benchmark
- `plugins/focus-kit/README.md` — the focus-kit pieces and how to use them
