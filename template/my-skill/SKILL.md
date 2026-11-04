---
name: my-skill
description: One or two sentences. Say what the skill does AND when to use it — the phrases a user would type, the files or tasks that should trigger it. This text is all Claude sees when deciding whether to load the skill.
argument-hint: "<what the user passes>"
---

# My skill

One paragraph: the job, the reader of the output, what "done" looks like.

## Inputs
- What the skill needs, and what to do when it is missing (ask one question, or stop).

## Workflow
1. Gather facts from real sources before writing anything.
2. Do the work.
3. Check the result (a script, a linter, a test) and fix what fails.
4. Report briefly: paths, what changed, anything unverified.

## Rules
- Each rule with its reason, so the model can apply it to cases the rule does not name.

## Bundled files
- `references/…` — load only when the step that needs it starts.
- `scripts/…` — deterministic work belongs in a script, not in prose.
