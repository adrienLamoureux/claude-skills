# claude-skills

My Claude Code skills, packaged as a plugin marketplace named **`adrien-skills`**.

```
claude-skills/
├─ .claude-plugin/marketplace.json   the catalogue: one entry per plugin
├─ plugins/
│  ├─ docs-kit/     skills/archon-document   twin HTML + MD engineering docs
│  ├─ dev-kit/      skills/pick-model        Claude model-tier routing
│  └─ career-kit/   skills/tailor-resume     truthful job-tailored résumés (resume-forge)
├─ template/my-skill/SKILL.md        start a new skill from here
├─ vendor/                           skills copied from others (see vendor/README.md)
└─ scripts/validate.sh               `claude plugin validate` on everything
```

A plugin is the unit you install; a skill is what you invoke. Plugin skills carry the plugin
name as a prefix: `/docs-kit:archon-document`, `/dev-kit:pick-model`,
`/career-kit:tailor-resume`.

## Use it

```bash
claude plugin marketplace add adrienLamoureux/claude-skills   # from GitHub
claude plugin marketplace add ./claude-skills                 # or a local checkout, for editing
claude plugin install docs-kit@adrien-skills
```

With a local checkout added, edits load at the next session or after `/reload-plugins`.
When a skill moves here from `~/.claude/skills/`, delete the old copy so only one version loads.

## Add a skill

1. Copy `template/my-skill/` into a plugin's `skills/` folder (or make a new plugin with its own
   `.claude-plugin/plugin.json` and add it to `marketplace.json`; keep both names identical).
2. Write the `description` carefully: it is the only text Claude reads to decide when to load it.
3. Draft and test it with the built-in `skill-creator` skill.
4. Run `scripts/validate.sh`, bump the plugin `version`, commit.

## Where a skill belongs

- Used across projects → here.
- Only meaningful inside one repository (a deploy check, a repo-specific workflow) → that
  repository's committed `.claude/skills/`.

## Rules

- No employer names, client data, credentials or personal contact details in any skill.
- Skills from others: install first, copy last (see `vendor/README.md`), licence checked.

## Licence

MIT, see `LICENSE`. Vendored skills keep their own licence (see `vendor/README.md`).
