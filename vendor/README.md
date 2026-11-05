# vendor/

Skills copied from other people, kept here only because they are changed locally.

Prefer, in order:
1. **Install, don't copy** — `claude plugin marketplace add <owner>/<repo>`, then
   `claude plugin install <plugin>@<marketplace>`. Updates arrive on their own.
2. **List without copying** — add a `git-subdir` entry to `.claude-plugin/marketplace.json`,
   pinned with `sha`, so the catalogue includes it while the files stay upstream.
3. **Copy here** — only when you will edit it. Each copied skill gets a `NOTICE.md`:

```
Upstream: https://github.com/<owner>/<repo>/tree/<sha>/<path>
Commit:   <sha>   Copied: <yyyy-mm-dd>
Licence:  <SPDX id, from the skill's own LICENSE file>
Changes:  <one line per local change>
```

Check the licence per skill before copying: some public skill repositories have no
repository-wide licence and license each skill separately.
To ship a vendored skill, move it into a plugin under `plugins/` and list that plugin.

## Listed upstream (option 2)

Entries in `.claude-plugin/marketplace.json` that point at someone else's repository. Nothing
is copied; bump a `sha` deliberately, after reading the diff and re-checking the licence.

| Entry | Upstream | Commit | Licence |
|---|---|---|---|
| `skill-creator` | anthropics/claude-plugins-official `plugins/skill-creator` | `fa4eb54` | Apache-2.0 |
| `plugin-dev` | anthropics/claude-plugins-official `plugins/plugin-dev` | `fa4eb54` | Apache-2.0 |
| `commit-commands` | anthropics/claude-plugins-official `plugins/commit-commands` | `fa4eb54` | Apache-2.0 |
| `security-guidance` | anthropics/claude-plugins-official `plugins/security-guidance` | `fa4eb54` | Apache-2.0 |
| `project-artifact` | anthropics/claude-plugins-official `plugins/project-artifact` | `fa4eb54` | Apache-2.0 |
| `webapp-testing` | anthropics/skills `skills/webapp-testing` | `ca45fc4` | Apache-2.0 (its `LICENSE.txt`) |

Not listable here: names starting with `claude-` or `anthropic-` are reserved for Anthropic's
own catalogue (`claude-md-management` is installed from `claude-plugins-official` instead).
Not listed: anthropics/skills document skills (`docx`, `pdf`, `pptx`, `xlsx`: source-available,
not open source) and skills without a licence file (`doc-coauthoring`).
