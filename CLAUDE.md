# claude-skills

The `adrien-skills` plugin marketplace: plugins in `plugins/`, the catalogue in
`.claude-plugin/marketplace.json`, Archon twin docs in `docs/ai-sdlc/`. Overview: `README.md`.

## Route changes through the kits

- A change that touches two or more areas goes through dev-kit: `/dev-kit:plan`, then
  `/dev-kit:implement`, then `/dev-kit:review`. This holds when the request says "build",
  "implement", "add" or "do all of these", not only when it says "plan".
- Areas: each `plugins/<kit>/`, `docs/`, `scripts/`, `prototypes/`, `.claude-plugin/`.
- Edit directly only inside one area: a typo, one prompt or doc, one script fix with its test.
- An objective measured over rounds goes to `/campaign-kit:campaign`; an unexplained failure
  goes to `/dev-kit:investigate` first.
- If you edited directly when this rule applied, say so in your reply.

## Gates

- `bash scripts/validate.sh`: `claude plugin validate` on the marketplace and every plugin.
- `python3 -m py_compile <file>` for each changed Python script; scripts use the standard
  library only.
- Each changed doc in `docs/ai-sdlc/`:
  `python3 plugins/docs-kit/skills/archon-document/scripts/check_docs.py <doc>.md --repo .`,
  then `python3 plugins/docs-kit/skills/archon-document/scripts/build_index.py docs/ai-sdlc`.

## Conventions

- Bump `version` in `plugins/<kit>/.claude-plugin/plugin.json` when a plugin's behaviour
  changes, and record the change in `ROADMAP.md`.
- `.dev-kit/` and `.campaign-kit/` are working state: never commit them.
