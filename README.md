# claude-skills

My Claude Code skills, packaged as a plugin marketplace named **`adrien-skills`**.

```
claude-skills/
├─ .claude-plugin/marketplace.json   the catalogue: my plugins + pinned picks from Anthropic
├─ plugins/
│  ├─ dev-kit/       developer family: plan → implement → review, investigate, pick-model
│  ├─ campaign-kit/  campaign family: interview → execute lanes → review and iterate (ReAct)
│  ├─ docs-kit/      skills/archon-document   twin HTML + MD engineering docs
│  └─ career-kit/    skills/tailor-resume     truthful job-tailored résumés (resume-forge)
├─ template/my-skill/SKILL.md        start a new skill from here
├─ vendor/                           skills from others (see vendor/README.md)
├─ scripts/validate.sh               `claude plugin validate` on everything
└─ ROADMAP.md                        planned work
```

A plugin is the unit you install; a skill is what you invoke. Plugin skills carry the plugin
name as a prefix: `/dev-kit:plan`, `/campaign-kit:campaign`, `/docs-kit:archon-document`.

## The two workflow families

Both keep the main session as a thin orchestrator and push reading and writing to sub-agents
on cheaper settings. Execution and checking run on **Sonnet**; planning, review and judging run
on **Opus**. Every agent writes its detail to a file and replies in a few lines, so the main
session's context stays small.

| | Developer — `dev-kit` | Campaign — `campaign-kit` |
|---|---|---|
| Pattern | plan-and-execute | ReAct (reason → act → observe, in rounds) |
| Use for | one well-defined ticket | an open-ended objective measured over many steps |
| Steps | `plan` → `implement` → `review` (+ `investigate` for bugs) | `interview` → `execute` lanes → `review` and iterate (`campaign` runs the loop) |
| Human gates | approve the plan; act on the review | approve the brief; pivots and blockers (configurable) |
| Run folder | `.dev-kit/<slug>/` | `.campaign-kit/<slug>/` |

### Model and effort routing

| Role | Agent | Model | Effort |
|---|---|---|---|
| map the repo | `dev-scout` | sonnet | medium (high for L) |
| plan | `dev-planner` | opus | S medium · M high · L xhigh |
| implement a slice | `dev-implementer` | sonnet | medium or high, set per slice by the planner |
| run gates, ownership, contract drift | `dev-checker` | sonnet | medium |
| review and judge | `dev-reviewer` | opus | S medium · M high · L or sensitive xhigh |
| investigate a bug | `dev-investigator` | sonnet | high (escalates to opus medium) |
| design the campaign | `campaign-strategist` | opus | medium / high / xhigh by scope |
| act on a lane | `campaign-runner` | sonnet | medium or high, set per action by the judge |
| measure and verify | `campaign-checker` | sonnet | medium |
| judge a round | `campaign-judge` | opus | medium routine · high on failure · xhigh final or last round |

Defaults live in each agent's `model:` / `effort:` frontmatter; skills raise or lower effort
per call. To override, copy an agent file into `~/.claude/agents/` with the same `name:`.
`/dev-kit:pick-model` gives the same routing advice for any other workflow.

## Use it

```bash
claude plugin marketplace add adrienLamoureux/claude-skills   # from GitHub
claude plugin marketplace add ./claude-skills                 # or a local checkout, for editing
claude plugin install dev-kit@adrien-skills
claude plugin install campaign-kit@adrien-skills
```

With a local checkout added, edits load at the next session or after `/reload-plugins`.
When a skill moves here from `~/.claude/skills/`, delete the old copy so only one version loads.

## Recommended from Anthropic

Listed in the catalogue from upstream, pinned to a commit, never copied (see
`vendor/README.md`). Install them like my own: `claude plugin install <name>@adrien-skills`.

| Plugin | Why it is here |
|---|---|
| `skill-creator` | write, eval and tune the skills in this repo |
| `plugin-dev` | agents, hooks, commands and manifests for these plugins |
| `commit-commands` | `/commit` and `/commit-push-pr`: the step after a dev-kit review approves |
| `webapp-testing` | Playwright checks for front-end acceptance criteria |
| `project-artifact` | a shareable status page for a campaign |
| `security-guidance` | opt-in: security warnings on edits and a per-turn LLM diff review (costs tokens every turn) |

Also recommended, but a third-party catalogue may not list a `claude-*` name, so install it from
Anthropic's own marketplace (built in to Claude Code):

```bash
claude plugin install claude-md-management@claude-plugins-official   # keeps CLAUDE.md, where dev-kit reads gates, current
```

## Add a skill

1. Copy `template/my-skill/` into a plugin's `skills/` folder (or make a new plugin with its own
   `.claude-plugin/plugin.json` and add it to `marketplace.json`; keep both names identical).
2. Write the `description` carefully: it is the only text Claude reads to decide when to load it.
3. Draft and test it with the `skill-creator` skill; add cases under the plugin's `evals/`.
4. Run `scripts/validate.sh`, bump the plugin `version`, commit.

Sub-agents go in the plugin's `agents/` folder with `model:` and `effort:` set to the cheapest
pair that does the job; skills launch them as `<plugin>:<agent>`.

## Evals

`dev-kit` and `campaign-kit` ship `claude plugin eval` suites (trigger and outcome checks,
each case run with and without the plugin). They cost real tokens, so CI runs them only on
demand: the `evals` workflow, or locally:

```bash
claude plugin eval plugins/dev-kit --max-cost-usd 5 --no-publish
```

## Where a skill belongs

- Used across projects → here.
- Only meaningful inside one repository (a deploy check, a repo-specific workflow) → that
  repository's committed `.claude/skills/`.

## Rules

- No employer names, client data, credentials or personal contact details in any skill.
- Skills from others: install first, list second, copy last (see `vendor/README.md`), licence
  checked.

## Licence

MIT, see `LICENSE`. Vendored and listed skills keep their own licence (see `vendor/README.md`).
