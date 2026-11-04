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
