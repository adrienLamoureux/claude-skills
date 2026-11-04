# Archon HTML components

The body fragment you hand to `build_html.py` uses only these components. The shell adds the
header (title, summary, status chips), the contents sidebar, the footer and the palette. The
checker rejects classes that are not in `assets/archon.css`, inline `style=`, and colour literals:
that is what keeps every page on one palette.

## Contents
1. Fragment skeleton
2. Writing rules for the human page
3. Component catalogue
4. Diagrams (Mermaid)
5. Choosing a component

## 1. Fragment skeleton

```html
<div class="ar-tldr">
  <p class="ar-label">TL;DR</p>
  <ul>
    <li>One fact per bullet. The answer first.</li>
  </ul>
</div>

<section>
  <h2>Short noun phrase</h2>
  <p class="ar-lead">One sentence: the takeaway of this section.</p>
  <!-- then ONE main visual: diagram, cards, steps, table, kv ... -->
  <!-- then at most a few bullets or a callout -->
</section>
```

- One `<section>` per `<h2>`. The build numbers them and builds the contents list from them.
- Use `<h3>` inside a section for sub-parts. No `<h1>`: the shell owns the title.
- Do not add ids to headings unless you link to them; the build generates them.
- Do not write navigation. The shell adds the crumb and "← index" link to the folder's
  `index.html` and the previous / next pager; link to a sibling doc in the body only where the
  text needs it, as `<a href="other-doc.html">`.

## 2. Writing rules for the human page

The reader is an engineer scanning between other tasks. They look at the picture, read the lead,
skim the bullets, and leave. Write for that path.

- **Picture first.** Every section opens with its main visual after the lead. Text supports the
  visual, not the other way round.
- **Short sentences.** One idea per sentence, about 20 words max. Present tense, active voice.
  "The worker polls the queue", not "The queue is polled by the worker".
- **Plain words.** "use" not "utilise", "start" not "initiate". Keep the code's exact names for
  things (`JobStore`, `GET /jobs`) and put them in `<code>`: readers search for them.
- **Lists over paragraphs.** A paragraph has 3 sentences at most. A list has about 6 items at most;
  group longer lists or turn them into a table.
- **Answer first.** The TL;DR and each `ar-lead` state the conclusion, not the topic.
- **Few refs.** Only the 1-3 files a reader would actually open (`<code class="ar-ref">`).
  The MD twin holds the full list.
- **Mark doubt.** A claim you could not verify gets `<span class="ar-badge is-unverified">unverified</span>`;
  a plan gets `is-proposal`. Unmarked means verified.
- **Lighter than the MD.** Aim for 30-60% of the MD's word count. Cut, don't shrink the font.

## 3. Component catalogue

### TL;DR — top of the page, once
```html
<div class="ar-tldr"><p class="ar-label">TL;DR</p><ul><li>...</li></ul></div>
```

### Section lead
```html
<p class="ar-lead">Jobs are the single record of every generation, whatever the provider.</p>
```

### Diagram — see §4
```html
<figure class="ar-diagram">
  <pre class="mermaid">
flowchart LR
  ui[Web UI]:::user -->|POST /jobs| api[API]:::svc
  </pre>
  <figcaption>Request path for a new job</figcaption>
</figure>
```

### Cards — parallel concepts, components, options, do / don't
```html
<div class="ar-cards">
  <div class="ar-card" data-kind="svc"><h3>API</h3><p>Validates and stores the job.</p></div>
  <div class="ar-card" data-kind="data"><h3>DynamoDB</h3><ul><li>One item per job</li></ul></div>
</div>
```
`data-kind` colours the top edge: `user svc data queue ext sec hot` (same as diagram nodes) or
`ok warn danger info proposal` (for do / don't, pros / cons, risk levels). Omit it for neutral.
2-6 cards; 2 cards sit side by side, which suits before / after and do / don't.

### Steps — a sequence: request flow, procedure, lifecycle
```html
<ol class="ar-steps">
  <li><strong>Client posts the job</strong> The API returns <code>202</code> and a job id.</li>
  <li><strong>Worker picks it up</strong> ...</li>
</ol>
```
The `<strong>` opener is the step title; the rest is one short sentence.

### Callout — one per section at most
```html
<div class="ar-callout is-warn"><strong>Gotcha</strong><p>Positional calls return [].</p></div>
```
Variants: (none) = info, `is-tip`, `is-warn`, `is-danger`. The `<strong>` is the label.

### Table — comparisons, matrices, field lists
```html
<table>
  <thead><tr><th>Option</th><th>Cost</th><th>Offline</th></tr></thead>
  <tbody><tr><td>A</td><td>Low</td><td class="ar-yes">Yes</td></tr></tbody>
</table>
```
The build wraps tables for horizontal scroll on phones. Cell markers: `ar-yes`, `ar-no`, `ar-part`.

### Key / value — config, env vars, fields, glossary
```html
<dl class="ar-kv">
  <dt>JOB_TTL_DAYS</dt><dd>Days before a finished job expires.</dd>
</dl>
```

### Stats — 2-4 headline numbers
```html
<div class="ar-stats">
  <div class="ar-stat"><b>11 → 1</b><span>generation code paths</span></div>
</div>
```
Only numbers you measured or read from the source. Label estimates with a badge.

### Inline
- File ref: `<code class="ar-ref">backend/lib/jobs.js:42</code>`
- Evidence badge: `<span class="ar-badge is-verified">verified</span>`; variants `is-inferred`,
  `is-proposal`, `is-unverified`, `is-risk`.
- Code: `<code>name</code>`; blocks: `<pre><code>...</code></pre>` (keep under ~15 lines; escape `<` as `&lt;`).

## 4. Diagrams (Mermaid)

Diagrams render with Mermaid 11, themed from the palette in light and dark. Put the source in
`<pre class="mermaid">` inside `<figure class="ar-diagram">`.

**Pick the type by the question it answers:**

| Question | Mermaid type |
|---|---|
| What are the parts and who talks to whom? | `flowchart LR` (`TB` for layers) |
| What happens, in order, across actors? | `sequenceDiagram` |
| What states can X be in? | `stateDiagram-v2` |
| What is stored and how is it related? | `erDiagram` |
| How are types / classes related? | `classDiagram` |
| What happens when? | `timeline` or `gantt` |

**Node kinds (flowcharts).** Tag nodes with `:::kind` so meaning is coloured the same way on every
page. The build adds a legend automatically.

| Kind | Use for |
|---|---|
| `user` | people, browsers, client apps |
| `svc` | services, functions, workers, modules |
| `data` | databases, buckets, caches, files |
| `queue` | queues, topics, streams, schedulers |
| `ext` | third-party / external systems (dashed) |
| `sec` | auth, identity, secrets, policies |
| `hot` | the one node this section is about |

**Rules.**
- 12 nodes max. Split into two diagrams rather than shrink one.
- Label edges with a verb or the call: `-->|writes|`, `-->|GET /jobs|`.
- Use `subgraph` for boundaries (VPC, service, team), not for decoration.
- No `style`, `classDef` or `linkStyle` lines: the palette does colour; the checker rejects them.
- Write `<` as `&lt;` and `&` as `&amp;` inside the source. `<br>` is fine in labels.
- Quote labels that hold punctuation: `api["API (Lambda)"]`.
- Add a `<figcaption>` that says what to notice, not what the diagram is.

```html
<figure class="ar-diagram">
  <pre class="mermaid">
flowchart LR
  ui[Browser]:::user -->|POST /jobs| api[Express API]:::svc
  api -->|put JOB#id| db[(DynamoDB)]:::data
  api -->|start| prov[Replicate]:::ext
  prov -->|webhook| api
  </pre>
  <figcaption>The API owns the job record; providers only report back.</figcaption>
</figure>
```

Inline `<svg>` is allowed when Mermaid can't draw it, but colour it only with `var(--ar-*)`.

## 5. Choosing a component

| Content | Component |
|---|---|
| Topology, flow, lifecycle, data model | diagram |
| 2-6 parallel things (parts, options, principles) | cards |
| Ordered actions or events | steps |
| Many items x several attributes | table |
| Names with one-line meanings (config, glossary) | kv |
| A trap, a rule, a tip | callout |
| Headline numbers | stats |
