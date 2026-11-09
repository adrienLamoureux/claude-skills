# focus-kit

Spend the human's attention where it matters. Agents get cheaper and faster each release; the
person who reads, decides and checks does not. The research behind every piece here, and the
options it came from, is in `docs/ai-sdlc/cognitive-load.md` at the repo root.

Nothing here needs a command: install the plugin and it works. The slash commands exist for
when you want something now.

| Piece | Limit it addresses | How it reaches you |
|---|---|---|
| `Reader-first` output style | reading volume, unknown terms | on in every session once installed |
| Inbox and resume lines | context switches | shown at session start; `/focus-kit:inbox` any time |
| Explain on demand, personal vocabulary | unknown terms | ask in your own words: "what does X mean?", "simpler please", "I know X" |
| Pacing | fatigue, context switches | a line at session start past 3 open runs |
| Runs page | reading volume, context switches | rebuilt by a hook whenever a run stops; keep it open in a browser tab |

## Install

```bash
claude plugin marketplace add adrienLamoureux/claude-skills
claude plugin install focus-kit@adrien-skills
```

## Reader-first output style

Every reply puts the answer or the decision in line 1, stays near 120 words unless you ask for
depth, asks one question at a time, glosses an unfamiliar term in at most eight words, and ends
with `Your move: …` or `Nothing needed.` Failed checks and risks come before good news, and
documents or code you ask for come in full.

- It is on in every session once focus-kit is installed: the style sets `force-for-plugin: true`,
  which overrides your `outputStyle` setting. To use another style, disable focus-kit
  (`claude plugin disable focus-kit@adrien-skills`). Because it is forced, `/config` styles such
  as `Explanatory` are unavailable while focus-kit is on.
- Learning mode, on request: say `teach me as we go` (or that the code is new to you) and each
  step gets a short `Why:` line plus a `Worth asking:` question, for the rest of the session.
  Say `learning mode off` to stop.
- Its name is `focus-kit:Reader-first` (a plugin style is `<plugin>:<style>`).
- It sets `keep-coding-instructions: true`, so Claude Code's coding instructions stay on.
- Claude Code reads style files when a session starts: changes apply to the next session.

## Inbox and resume lines

dev-kit and campaign-kit write `<run-dir>/resume.md` at every stop: where the run is, what it
did, what it needs from you. The inbox lists every run that needs something, oldest first:

```
3 run(s) wait on you, oldest first:
-   1d · dev-kit api-pagination · implement · in progress — interrupted? resume it with /dev-kit:implement api-pagination
-   2h · dev-kit login-rate-limit · review · approve — read Where to look in review.md, then commit
-  20m · campaign-kit coverage-80 · round 3 · stop-blocked — answer: grant read access to the staging DB
```

- **At session start** a `SessionStart` hook shows the first four lines to you and gives the
  list to Claude, so "pick up where I left off" works without re-explaining. It prints nothing
  when nothing waits.
- **Any time:** `/focus-kit:inbox` (`--all` also lists runs that need nothing).
- **Done with a run:** a finished run (review `approve`, campaign `done`) stops asking after 7
  days on its own. To clear one sooner, say so ("I committed login-rate-limit") or use
  `/focus-kit:inbox dismiss <run-dir>`.
- **Other repositories:** the session-start list covers the current repository, plus any folder
  in `FOCUS_KIT_ROOTS` (separated by `:`). The runs page covers every repository the hooks have
  seen a run in, with no setup.
- A run with no `resume.md` (older kit versions), or one whose files are newer than it, is read
  from its own files instead: `plan.md`, `review.md`, `checks/`, `brief.md`, `rounds/`,
  `outcome.md`. A run untouched for 30 minutes that is not done shows as interrupted.

**Status line.** A plugin cannot set your status line, so add the segment yourself in
`~/.claude/settings.json`; the path is the installed plugin's folder under
`~/.claude/plugins/` (or your checkout):

```json
{ "statusLine": { "type": "command",
  "command": "python3 /path/to/focus-kit/scripts/focus_tool.py statusline" } }
```

It prints `focus: N waiting`, or nothing. The count is cached up to 3 minutes in
`statusline.json` under `FOCUS_KIT_HOME` (default `~/.claude/focus-kit`); session start refreshes
it, and a run's `resume.md` write clears it. To keep an existing status line, call both from one
script and pass the same stdin to each.

## Explain on demand and your vocabulary

- `/focus-kit:explain <term>` — what it is, where it lives in this project (`path:line`), why
  it matters here; about 80 words.
- `/focus-kit:explain last` — the previous reply again, one level simpler, same facts.
- `/focus-kit:explain known <term> ...` — you know these now: they go in
  `~/.claude/focus-kit/vocabulary.md` (or the file in `FOCUS_KIT_VOCAB`), one `- term` per
  line, and you can edit it by hand. `forget <term>` takes one out.

The SessionStart hook hands the list to Claude at the start of every session, so the
Reader-first style and `explain` gloss only the terms you do not know. Personal support beats
glossing everything for everyone (`docs/ai-sdlc/cognitive-load.md`, option 6).

## Pacing

Parallel agents cost tokens; parallel decisions cost attention. Keep the second small.

- **At most three open runs.** BCG's 2026 survey found the most mental fatigue among people
  overseeing several AI tools or agents at once; coverage puts the turning point at three
  (unverified). The inbox and the session-start message add a pacing line past three, and
  Claude mentions it once if you start another run anyway.
- **One checkpoint per round.** campaign-kit holds a `needs-human` lane until its round's review,
  so every question of a round reaches you together. dev-kit stops at plan approval, at
  blockers, and at the verdict, each with a decision card.
- **Unattended means one ping.** The `/goal` lines dev-kit and campaign-kit print end only on a
  final status (approve, blocked, done), so you hear from the run once.
- **Fewer permission prompts.** Each prompt is an interruption. Allow-list the read-only
  commands you approve again and again: Claude Code's `/fewer-permission-prompts` finds them in
  your transcripts.

## Runs page

`~/.claude/focus-kit/runs.html` has one card per run, waiting first, with where it is, what it
needs, what it did, its `recap.md`, and links to its files. A `PostToolUse` hook rebuilds it
whenever a kit writes a run's `resume.md`, and the session-start hook rebuilds it too. Open it
once (`open ~/.claude/focus-kit/runs.html` on macOS) and leave the tab: it reloads every
minute. `FOCUS_KIT_PAGE=0` stops the rebuilds; `/focus-kit:inbox page` forces one.
`FOCUS_KIT_HOME` moves focus-kit's files (vocabulary, known repositories, page) elsewhere. For a page others can see, campaign-kit already offers a project-artifact status page
when that plugin is installed.

## Evals

`evals/` holds a `claude plugin eval` suite (two trigger cases, one should-not-fire). Run it
with `claude plugin eval plugins/focus-kit --max-cost-usd 3`. The output-style benchmark is
`prototypes/focus-kit-trial/bench_styles.py`.
