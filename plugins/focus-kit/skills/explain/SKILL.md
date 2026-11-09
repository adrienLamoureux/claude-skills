---
name: explain
description: Explain a term in this project's context in under 80 words (what it is, where it lives in the code, why it matters here), restate the last reply one level simpler, or record terms the user already knows so they are never glossed again. Use when the user runs /focus-kit:explain, asks "what does X mean", "what is X here", "explain that more simply", "I don't follow", or says they already know a term.
argument-hint: "<term> | last | known <term> ... | forget <term> ..."
effort: low
---

# Explain

Jargon support works best when it is personal: explain what this reader does not know, at the
moment they need it, and nothing they already know.

`TOOL` is `python3 <skill-dir>/../../scripts/focus_tool.py`, where `<skill-dir>` is the base
directory shown when this skill loads.

## `<term>` — explain one term

1. If the term looks like a code name (an identifier, file, flag, config key, internal
   acronym), find where it is defined: one Grep, two at most. Skip this for general terms.
2. Answer in at most 80 words, not counting paths and the closing line, in this order:
   - **What:** one plain sentence, no new jargon; if a second term is unavoidable, gloss it in
     a few words.
   - **Here:** where it lives or shows up in this project, with `path:line` when you found it.
   - **Why it matters:** what goes wrong when it is misunderstood or misused.
   - An analogy only if it makes the idea click; never one that is wrong in the details.
3. End with: ``Know it now? `/focus-kit:explain known <term>` ``.

## `last` — the previous reply, one level simpler

Restate your previous reply with the same facts, decisions and identifiers: shorter sentences,
every term the user may not know glossed or replaced, the conclusion first. Never drop a risk,
a failed check or an open question to make it shorter. If the user named the part they did not
follow, restate only that part.

## `known <term> ...` and `forget <term> ...`

Run `TOOL vocab add <term> ...` or `TOOL vocab remove <term> ...` and say the count in one line.
The list loads into the next session, through focus-kit's SessionStart hook; in this session,
treat the terms as known from now on. `TOOL vocab list` shows the list and its file.
