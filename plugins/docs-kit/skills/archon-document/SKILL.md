---
name: archon-document
description: Write an engineering document as a twin pair from one fact base — an HTML page for engineers (diagrams first, short sentences, the shared Archon palette) and a token-lean Markdown file for AI agents (frontmatter, exact identifiers, path:line refs). Use whenever the user runs /archon-document or asks for "archon" docs, and whenever they want to document, explain or write up a codebase area, module, architecture, design decision / ADR, runbook, onboarding guide, review or technical concept for software engineers — especially for both people and agents.
argument-hint: "<topic or path> [type=architecture|module|decision|runbook|concept|onboarding|review] [out=<dir>]"
---

# Archon document

One fact base, two renderings, both for software engineers:

| File | Reader | Optimised for |
|---|---|---|
| `<slug>.html` | an engineer scanning | pictures first, short sentences, lists, cards; the shared Archon palette |
| `<slug>.md` | a coding agent (and grep) | finding it, trusting it, few tokens: frontmatter, exact names, `path:line` refs |

A folder of docs is one **collection** with two indexes: `index.html` for people (grouped cards
in reading order, a filter, sub-collections) and `INDEX.md` for agents. Every page links up to
`index.html` and to the previous and next doc in reading order.

The MD is canonical: it holds every fact and ref. The HTML is a visual digest of the same facts —
never a fact the MD lacks, never a different name or number. When the two disagree, readers stop
trusting both.

`<skill-dir>` below is the base directory shown when this skill loads.

## Bundled files

- `assets/archon.css` — **the palette.** Every page inlines this exact file through the build, so
  all Archon pages look like one set. Never write CSS, `style=` or colour values in a page. To
  change the look, edit this file once and run `build_html.py --rebuild` on existing pages.
- `assets/shell.html`, `assets/archon.js` — page shell and runtime (theme toggle, Mermaid
  theming, contents scroll-spy, index filter). Used by the build; you never copy them.
- `scripts/build_html.py` — body fragment + MD frontmatter → finished page, with its
  collection links once an index exists.
- `scripts/check_docs.py` — lints the pair: palette drift, sentence length, text-only sections,
  frontmatter, refs that do not resolve, HTML heavier than MD.
- `scripts/build_index.py` — writes the folder's `INDEX.md` and `index.html`, then re-renders
  every page so its up and prev/next links are current. Never hand-edit either index.
- `references/html-components.md` — component catalogue, human writing rules, diagram rules.
  **Read before writing the HTML body.**
- `references/md-format.md` — frontmatter schema, body skeleton, agent writing rules.
  **Read before writing the MD.**
- `references/doc-types.md` — section blueprint per doc type. Read the part for your type.

## Workflow

### 1. Frame
Work out from the request (ask one question only if the topic itself is unclear):
- **Topic and scope** — what is in, what is out.
- **Doc type** — `architecture`, `module`, `decision`, `runbook`, `concept`, `onboarding`, `review`.
- **Slug** — kebab-case, 2-5 words; it names both files and becomes the `id`.
- **Output folder** — the one the user names; else `docs/archon/` at the repo root inside a git
  repo; else the current directory. Both files go in the same folder.
- **Collection place** — when the folder already holds docs, or this request makes several,
  decide the doc's `group` (its index section) and `order` (reading position; leave gaps of 10
  so later docs fit between). A set of related docs gets its own sub-folder, which becomes a
  collection listed by the parent index.

Say the plan in one line (type, slug, folder, group), then go.

### 2. Research — facts before prose
Read the real sources: code, configs, existing docs, `git log` for the topic, the web for
concepts. Write nothing about a codebase from memory. Collect a working fact list where each
fact has a source (`path:line`, URL, or command output) and a status: verified, inferred,
unverified, or proposal. Record the commit you read (`git rev-parse --short HEAD`).

Large codebases: read entry points and the files the flow passes through, not every file.

### 3. Write the MD twin first
Follow `references/md-format.md` and the blueprint in `references/doc-types.md`.
Save as `<folder>/<slug>.md` with `html_twin: <slug>.html`.

### 4. Write the HTML body, then build
Follow `references/html-components.md` and the same blueprint. Choose for each section the visual
that shows its idea best; trim the MD's detail rather than restating it. Write only the body
fragment (TL;DR + `<section>`s) to a temporary file, then:

```bash
python3 <skill-dir>/scripts/build_html.py --md <folder>/<slug>.md --body <tmp>/<slug>.body.html
```

The build writes `<folder>/<slug>.html` with the header, contents list, legends and footer.
Delete the temporary fragment afterwards.

### 5. Check and fix
```bash
python3 <skill-dir>/scripts/check_docs.py <folder>/<slug>.md --repo <repo-root>
```
Fix every ERROR. Treat warnings as a review: fix the real problems (a long sentence, a
text-only section) and leave the ones that are justified. Re-run until clean.

Then read the HTML body once as the target reader would: does each section's visual alone
convey its point? If you can open a browser, look at the page in light and dark.

### 6. Index and navigation
```bash
python3 <skill-dir>/scripts/build_index.py <folder> [--title "<collection name>"] [--summary "<one sentence>"]
```
Run it after every build, even for one doc. It writes `INDEX.md` and `index.html`, then
re-renders the folder's pages so each one links up to the index and on to its neighbours.
Pass `--title` and `--summary` the first time (a name of 2-4 words, then one sentence on what
the collection teaches); the index remembers them. It also refreshes the parent folder's index
and any sub-collection indexes, so links between collections stay correct.

### 7. Report
Reply briefly: the page path, the collection's `index.html`, one line on what the doc covers, and
any `[unverified]` points the user should confirm. Offer to open the HTML.

## Updating an existing doc

1. Edit the MD (facts, frontmatter, `updated`, `source_commit`).
2. Edit the HTML body in place between `<!--ar:body-->` and `<!--ar:/body-->`.
3. `build_html.py --rebuild <folder>/<slug>.html` — refreshes header, contents, legends and
   palette from the current MD and `archon.css`.
4. Check and re-index as above. Re-index also after changing `title`, `group` or `order`: the
   index and the neighbours' prev/next links read them.

## Principles (why the rules exist)

- **Two readers, two shapes.** People skim and remember pictures; agents grep and pay per
  token. Writing one doc for both serves neither, so the same facts get two layouts.
- **One palette, enforced by the build.** Consistency across many docs only survives if no
  single doc can drift. That is why CSS lives only in `archon.css` and the checker rejects
  inline styles, colour literals and unknown classes.
- **One way in, one reading order.** A doc nobody can find is not read. The index is generated
  from the same frontmatter as the pages, so the index, `INDEX.md` and every prev/next link
  agree, and none of them can be edited out of step.
- **Truth over polish.** A wrong fact costs more than a missing one. Refs are checked against
  the repo; anything not seen in a source carries a tag (`[inferred]`, `[unverified]`,
  `[proposal]`) in the MD and a badge in the HTML.
