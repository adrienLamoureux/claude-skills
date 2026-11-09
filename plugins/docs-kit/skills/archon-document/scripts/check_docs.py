#!/usr/bin/env python3
"""Lint an archon-document pair. Errors exit 1; warnings are advice to weigh.

  check_docs.py docs/archon/job-spine.md [--repo .]

The HTML twin is found through the MD's `html_twin` key. `--repo` (default: cwd) is the
root that backticked `path/file.ext:line` references must resolve against.
"""

import argparse
import html
import re
import sys
from pathlib import Path

from archon_common import (
    BODY_END,
    BODY_START,
    CARD_KINDS,
    CSS_PATH,
    DOC_TYPES,
    REQUIRED_MD_KEYS,
    STATUSES,
    doc_order,
    extract_between,
    palette_version,
    parse_frontmatter,
    read_embedded_meta,
    strip_tags,
    word_count,
)

# Human page (HTML) budgets
MAX_SENTENCE_WORDS = 25
MAX_PARAGRAPH_SENTENCES = 3
MAX_LIST_ITEMS = 7
MAX_HTML_TO_MD_RATIO = 0.9
# Agent file (MD) budgets
MD_SOFT_WORD_CAP = 2500
CHARS_PER_TOKEN = 4
REPORT_SAMPLE = 3

FILLER_PHRASES = (
    "as mentioned above", "as mentioned earlier", "see above", "see below", "as discussed",
    "it is important to note", "it's worth noting", "in this document", "in this section",
    "let's", "let us", "simply", "basically",
)
VISUAL_MARKERS = (
    'class="ar-diagram', 'class="ar-cards', 'class="ar-steps', 'class="ar-kv', 'class="ar-stats',
    'class="ar-callout', "<table", "<pre",
)
REF_RE = re.compile(r"`((?:[\w.-]+/)+[\w.-]+\.\w+)(?::(\d+)(?:-(\d+))?)?`")
HISTORY_RE = re.compile(r"\b(deleted|removed|renamed)\b", re.I)  # lines about gone files skip the existence check
CLASS_ATTR_RE = re.compile(r'class="([^"]*)"')
KIND_ATTR_RE = re.compile(r'data-kind="([^"]*)"')
CSS_CLASS_RE = re.compile(r"\.((?:ar|is)-[a-z0-9-]+)")
MERMAID_RE = re.compile(r'<pre class="mermaid">(.*?)</pre>', re.S)
SECTION_RE = re.compile(r"<section\b.*?</section>", re.S)
H2_TEXT_RE = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9`\"(])")
COLOR_LITERAL_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|\brgba?\(|\bhsla?\(")
MERMAID_STYLE_RE = re.compile(r"^\s*(style|classDef|linkStyle)\b", re.M)
RAW_HTML_RE = re.compile(r"<(?!!--)/?[a-zA-Z][^>]*>")
FENCE_RE = re.compile(r"^```.*?^```", re.S | re.M)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ACRONYM_RE = re.compile(r"^([A-Z][A-Z0-9]{1,5})s?$")  # 7+ capitals is a shouted word or a constant
# Known to any software engineer: never flagged. Everything else needs an expansion at first
# use ("Architecture Decision Record (ADR)" or "ADR (architecture decision record)"), a
# `## Glossary` entry, or a place in the frontmatter's aliases.
COMMON_ACRONYMS = {
    "AI", "API", "AWS", "CI", "CD", "CLI", "CPU", "CSS", "CSV", "DB", "DNS", "GCP", "GPU", "HTML",
    "HTTP", "HTTPS", "ID", "IDE", "IO", "IP", "JS", "JSON", "MD", "MIT", "OK", "OS", "PDF", "PR",
    "RAM", "README", "SDK", "SQL", "SSH", "TCP", "TL", "DR", "TLS", "TS", "UI", "URL", "USD",
    "UTC", "UX", "VM", "XML", "YAML", "IAM", "PATH", "US", "UK", "EU", "VS",
    "MUST", "NEVER", "NOT", "ALWAYS", "SHOULD", "AND", "OR", "TODO", "NOTE",
}


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, where, msg):
        self.errors.append(f"  ERROR  {where:<4} {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"  WARN   {where:<4} {msg}")


def short(text, limit=80):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def check_md(md_path, repo, report):
    text = md_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    if not meta:
        report.error("md", "no YAML frontmatter")
        return meta, body
    for key in REQUIRED_MD_KEYS:
        if not meta.get(key):
            report.error("md", f"frontmatter key missing or empty: {key}")
    if meta.get("id") and meta["id"] != md_path.stem:
        report.error("md", f"id '{meta['id']}' must equal the file name '{md_path.stem}'")
    if meta.get("doc_type") and meta["doc_type"] not in DOC_TYPES:
        report.warn("md", f"doc_type '{meta['doc_type']}' not one of {', '.join(DOC_TYPES)}")
    if "order" in meta and doc_order(meta) is None:
        report.error("md", f"order '{meta['order']}' must be an integer (it sets the reading order)")
    if meta.get("status") and meta["status"] not in STATUSES:
        report.warn("md", f"status '{meta['status']}' not one of {', '.join(STATUSES)}")
    if meta.get("updated") and not DATE_RE.match(str(meta["updated"])):
        report.error("md", "updated must be an absolute date YYYY-MM-DD")

    prose = FENCE_RE.sub("", body)
    if not re.search(r"^# ", prose, re.M):
        report.warn("md", "no '# Title' heading after the frontmatter")
    if not re.search(r"^## TL;DR", prose, re.M):
        report.warn("md", "no '## TL;DR' section")
    if not re.search(r"^## Sources", prose, re.M):
        report.warn("md", "no '## Sources' section")
    raw = RAW_HTML_RE.findall(re.sub(r"`[^`]*`", "", prose))
    if raw:
        report.warn("md", f"raw HTML tags (agents pay tokens for markup): {', '.join(raw[:REPORT_SAMPLE])}")
    if "![" in prose:
        report.warn("md", "image embed: agents cannot see it; state the content as text")
    lowered = prose.lower()
    fillers = [p for p in FILLER_PHRASES if p in lowered]
    if fillers:
        report.warn("md", f"filler / position-dependent phrases: {', '.join(fillers)}")
    headings = re.findall(r"^#{2,4} (.+)$", prose, re.M)
    dupes = sorted({h for h in headings if headings.count(h) > 1})
    if dupes:
        report.warn("md", f"duplicate headings (ambiguous anchors): {', '.join(dupes)}")

    refs = [ref for line in body.splitlines() if not HISTORY_RE.search(line) for ref in REF_RE.findall(line)]
    for path, start, end in refs:
        target = repo / path
        if not target.is_file():
            report.error("md", f"ref not found under {repo}: {path}")
            continue
        last = int(end or start or 0)
        if last:
            length = sum(1 for _ in target.open(encoding="utf-8", errors="ignore"))
            if last > length:
                report.error("md", f"ref {path}:{last} is past the end of the file ({length} lines)")

    check_acronyms(prose, meta, report)

    words = word_count(prose)
    if words > MD_SOFT_WORD_CAP:
        report.warn("md", f"{words} words > {MD_SOFT_WORD_CAP}: split by subtopic and link via 'related'")
    return meta, body


def check_acronyms(prose, meta, report):
    """Warn on acronyms a reader may not know that the doc never expands or defines."""
    # The glossary is read before code spans are dropped: its terms are written in backticks.
    glossary = re.search(r"^## Glossary\s*\n(.*?)(?=^## |\Z)", prose, re.M | re.S)
    text = re.sub(r"`[^`]*`", " ", prose)
    text = re.sub(r"\]\([^)]*\)|https?://\S+", " ", text)
    defined = set(re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", glossary.group(1))) if glossary else set()
    aliases = meta.get("aliases") or []
    aliases = aliases if isinstance(aliases, list) else [aliases]
    defined |= {w for a in aliases for w in re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", str(a))}
    defined |= set(re.findall(r"\(([A-Z][A-Z0-9]{1,})s?\)", text))          # Expansion (ACR)
    defined |= set(re.findall(r"\b([A-Z][A-Z0-9]{1,})s? \([a-z]", text))     # ACR (expansion)
    unknown = []
    for token in text.split():
        if re.search(r"[/_.\-]\w", token):
            continue  # a path, identifier, version or hyphenated name, not prose
        match = ACRONYM_RE.match(token.strip(",;:()[]{}\"'!?.*"))
        if match:
            acronym = match.group(1)
            if (acronym not in COMMON_ACRONYMS and acronym not in defined
                    and acronym not in unknown):
                unknown.append(acronym)
    if unknown:
        report.warn("md", f"acronyms never expanded or defined (expand at first use, or add to "
                          f"## Glossary or aliases): {', '.join(unknown[:REPORT_SAMPLE * 3])}")


def known_classes():
    return set(CSS_CLASS_RE.findall(CSS_PATH.read_text(encoding="utf-8"))) | {"mermaid"}


def check_html(html_path, md_meta, report):
    page = html_path.read_text(encoding="utf-8")
    body, meta = extract_between(page, BODY_START, BODY_END), read_embedded_meta(page)
    if body is None or meta is None:
        report.error("html", "not built by build_html.py (body markers or meta missing)")
        return ""
    current = palette_version()
    if f'data-ar-palette="{current}"' not in page:
        report.warn("html", f"built with an older palette: run build_html.py --rebuild {html_path.name}")
    if md_meta.get("title") and meta.get("title") != md_meta.get("title"):
        report.error("html", "title differs from the MD twin: run build_html.py --rebuild")

    if re.search(r"\sstyle=", body):
        report.error("html", "inline style= attribute: use Archon components so the palette stays shared")
    if re.search(r"<(style|script|link)\b", body):
        report.error("html", "<style>/<script>/<link> inside the body: the shell owns CSS and JS")
    mermaid_src = MERMAID_RE.findall(body)
    non_diagram = MERMAID_RE.sub("", body)
    if any(COLOR_LITERAL_RE.search(tag) for tag in re.findall(r"<[^>]+>", non_diagram)):
        report.error("html", "colour literal in markup (e.g. an SVG fill): use var(--ar-*) or a kind instead")
    for src in mermaid_src:
        decoded = html.unescape(src)
        if MERMAID_STYLE_RE.search(decoded):
            report.error("html", "Mermaid style/classDef/linkStyle: tag nodes with :::kind instead")
        if re.search(r"<(?!br\s*/?>)[a-zA-Z]", decoded):
            report.warn("html", "unescaped '<' in a diagram: write &lt; so the browser keeps it as text")

    allowed = known_classes()
    unknown = sorted({c for attr in CLASS_ATTR_RE.findall(body) for c in attr.split() if c not in allowed})
    if unknown:
        report.error("html", f"classes not in archon.css: {', '.join(unknown)}")
    bad_kinds = sorted({k for k in KIND_ATTR_RE.findall(body) if k not in CARD_KINDS})
    if bad_kinds:
        report.error("html", f"unknown data-kind: {', '.join(bad_kinds)} (allowed: {', '.join(CARD_KINDS)})")

    if not mermaid_src and "<svg" not in body:
        report.warn("html", "no diagram: engineers scan pictures first, add at least one")
    if 'class="ar-tldr"' not in body:
        report.warn("html", "no TL;DR block at the top")
    for section in SECTION_RE.findall(body):
        if not any(marker in section for marker in VISUAL_MARKERS):
            title = H2_TEXT_RE.search(section)
            name = strip_tags(title.group(1)).strip() if title else "untitled"
            report.warn("html", f"text-only section '{short(name, 40)}': lead with a visual")

    readable = re.sub(r"<pre\b.*?</pre>|<code\b.*?</code>", " ", non_diagram, flags=re.S)
    long_sentences, long_paragraphs = [], 0
    for block in re.findall(r"<(p|li|dd|td)\b[^>]*>(.*?)</\1>", readable, re.S):
        text = " ".join(strip_tags(block[1]).split())
        sentences = [s for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]
        long_sentences += [s for s in sentences if word_count(s) > MAX_SENTENCE_WORDS]
        if block[0] == "p" and len(sentences) > MAX_PARAGRAPH_SENTENCES:
            long_paragraphs += 1
    if long_sentences:
        samples = "; ".join(f'"{short(s, 60)}"' for s in long_sentences[:REPORT_SAMPLE])
        report.warn("html", f"{len(long_sentences)} sentence(s) over {MAX_SENTENCE_WORDS} words, e.g. {samples}")
    if long_paragraphs:
        report.warn("html", f"{long_paragraphs} paragraph(s) over {MAX_PARAGRAPH_SENTENCES} sentences: use a list")
    for items in re.findall(r"<(?:ul|ol)\b[^>]*>(.*?)</(?:ul|ol)>", body, re.S):
        count = len(re.findall(r"<li\b", items))
        if count > MAX_LIST_ITEMS:
            report.warn("html", f"list of {count} items > {MAX_LIST_ITEMS}: group it or use a table")
    return readable


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("md", type=Path)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()

    report = Report()
    md_meta, md_body = check_md(args.md, args.repo.resolve(), report)
    html_path = args.md.parent / md_meta.get("html_twin", f"{args.md.stem}.html")
    stats = []
    md_words = word_count(FENCE_RE.sub("", md_body))
    stats.append(f"md {md_words} words (~{len(md_body) // CHARS_PER_TOKEN} tokens)")
    if html_path.is_file():
        readable = check_html(html_path, md_meta, report)
        html_words = word_count(strip_tags(MERMAID_RE.sub("", readable)))
        ratio = html_words / md_words if md_words else 0
        if ratio > MAX_HTML_TO_MD_RATIO:
            report.warn("html", f"HTML has {ratio:.0%} of the MD's words: the human page should be the lighter one")
        diagrams = len(MERMAID_RE.findall(html_path.read_text(encoding="utf-8")))
        stats.append(f"html {html_words} words ({ratio:.0%} of md), {diagrams} diagram(s)")
    else:
        report.error("html", f"HTML twin not found: {html_path}")

    print(f"archon check: {args.md}")
    for line in report.errors + report.warnings:
        print(line)
    print("  stats  " + " · ".join(stats))
    print(f"→ {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    sys.exit(1 if report.errors else 0)


if __name__ == "__main__":
    main()
