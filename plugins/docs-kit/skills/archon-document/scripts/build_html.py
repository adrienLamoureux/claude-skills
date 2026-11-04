#!/usr/bin/env python3
"""Assemble an archon-document HTML page: body fragment + MD twin frontmatter + Archon palette.

First build:
  build_html.py --md docs/archon/job-spine.md --body /tmp/job-spine.body.html
Rebuild existing pages (after editing the body in place, changing the MD frontmatter,
or updating assets/archon.css):
  build_html.py --rebuild docs/archon/*.html

The page shell, CSS and JS always come from the skill's assets/ folder, so every page
shares one palette. The output is self-contained apart from Mermaid, which loads from a CDN
only when the body contains a diagram.

Collection links (an "up" link to the folder's index.html, and prev/next in reading order)
are added once build_index.py has generated that index; it re-renders pages to keep them current.
Rebuilding an index.html regenerates it from the folder's MDs.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

from archon_common import (
    BODY_END,
    BODY_START,
    CSS_PATH,
    DOC_TYPES,
    JS_PATH,
    MERMAID_URL,
    NODE_KINDS,
    SHELL_PATH,
    STATUSES,
    INDEX_KIND,
    as_list,
    extract_between,
    page_nav,
    palette_version,
    parse_frontmatter,
    read_embedded_meta,
    strip_tags,
    word_count,
)

WORDS_PER_MINUTE = 200
META_KEYS = ("title", "id", "doc_type", "summary", "status", "updated", "audience", "source_commit", "tags")
H2_RE = re.compile(r"<h2(\s[^>]*)?>(.*?)</h2>", re.S)
TABLE_RE = re.compile(r'(?<!<div class="ar-scroll">)(<table\b.*?</table>)', re.S)
FIGURE_RE = re.compile(r'<figure class="ar-diagram"[^>]*>.*?</figure>', re.S)
AUTO_LEGEND_RE = re.compile(r'\s*<div class="ar-legend" data-ar-auto>.*?</div>', re.S)
KIND_USE_RE = re.compile(r":::(\w+)|^\s*class\s+[\w,\s]+?\s+(\w+)\s*;?\s*$", re.M)
DARK_BLOCK_RE = re.compile(r':root\[data-theme="dark"\]\s*\{(.*?)\}', re.S)


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", strip_tags(text).lower()).strip("-")
    return slug or "section"


def add_heading_ids(body):
    """Give every <h2> a unique id and return the TOC entries."""
    toc, used = [], set()

    def visit(match):
        attrs, inner = match.group(1) or "", match.group(2)
        found = re.search(r'\bid="([^"]+)"', attrs)
        heading_id = found.group(1) if found else slugify(inner)
        base, n = heading_id, 2
        while heading_id in used:
            heading_id, n = f"{base}-{n}", n + 1
        used.add(heading_id)
        toc.append((heading_id, strip_tags(inner).strip()))
        attrs = re.sub(r'\s*\bid="[^"]*"', "", attrs)
        return f'<h2 id="{heading_id}"{attrs}>{inner}</h2>'

    return H2_RE.sub(visit, body), toc


def add_legends(body):
    """Append a kind legend to each diagram that tags nodes with :::kind."""

    def visit(match):
        figure = AUTO_LEGEND_RE.sub("", match.group(0))
        kinds = []
        for a, b in KIND_USE_RE.findall(html.unescape(figure)):
            kind = a or b
            if kind in NODE_KINDS and kind not in kinds:
                kinds.append(kind)
        if not kinds:
            return figure
        items = "".join(f'<span data-kind="{k}">{NODE_KINDS[k]}</span>' for k in kinds)
        legend = f'\n  <div class="ar-legend" data-ar-auto>{items}</div>'
        if "<figcaption" in figure:
            return figure.replace("<figcaption", legend.lstrip("\n") + "\n  <figcaption", 1)
        return figure.replace("</figure>", legend + "\n</figure>")

    return FIGURE_RE.sub(visit, body)


def css_with_dark_media():
    css = CSS_PATH.read_text(encoding="utf-8")
    dark = DARK_BLOCK_RE.search(css)
    if not dark:
        return css
    media = (
        '\n@media (prefers-color-scheme: dark) {\n  :root:not([data-theme="light"]) {'
        + dark.group(1).rstrip()
        + "\n  }\n}\n"
    )
    return css[: dark.end()] + media + css[dark.end():]


def esc(value):
    return html.escape(str(value), quote=True)


def render_toc(toc):
    items = "".join(f'<li><a href="#{esc(i)}">{esc(t)}</a></li>' for i, t in toc)
    return f"<ol>{items}</ol>"


def render_chips(meta, minutes):
    chips = []
    status = meta.get("status")
    if status:
        cls = f" is-{status}" if status in STATUSES else ""
        chips.append(f'<span class="ar-chip{cls}">{esc(status)}</span>')
    if meta.get("updated"):
        chips.append(f'<span class="ar-chip">Updated {esc(meta["updated"])}</span>')
    if meta.get("audience"):
        chips.append(f'<span class="ar-chip">For {esc(meta["audience"])}</span>')
    if meta.get("source_commit"):
        chips.append(f'<span class="ar-chip">Commit <code>{esc(meta["source_commit"])}</code></span>')
    if meta.get("kind") == INDEX_KIND:
        count = meta.get("doc_count", 0)
        chips.append(f'<span class="ar-chip">{esc(count)} document{"" if count == 1 else "s"}</span>')
    else:
        chips.append(f'<span class="ar-chip">~{minutes} min read</span>')
    return "".join(chips)


def render_nav(nav):
    """(crumb, toc_home, pager) HTML for a page's collection links; empty strings when absent."""
    nav = nav or {}
    up = nav.get("up")
    crumb = toc_home = pager = ""
    if up:
        href, title = esc(up["href"]), esc(up["title"])
        crumb = f'<a class="ar-crumb" href="{href}">{title}</a><span class="ar-crumb-sep">/</span>'
        toc_home = f'<a class="ar-toc-home" href="{href}">← {title}</a>'
    links = []
    for key, label in (("prev", "Previous"), ("next", "Next")):
        item = nav.get(key)
        if item:
            links.append(
                f'<a class="ar-pager-{key}" href="{esc(item["href"])}">'
                f'<span class="ar-label">{label}</span>{esc(item["title"])}</a>'
            )
    if links:
        pager = f'<nav class="ar-pager" aria-label="More in this collection">{"".join(links)}</nav>'
    return crumb, toc_home, pager


def render_footer(meta, palette):
    twin = meta.get("md_twin")
    label = "Agent index" if meta.get("kind") == INDEX_KIND else "AI twin"
    left = f'{label}: <a href="{esc(twin)}">{esc(twin)}</a>' if twin else ""
    tags = " · ".join(esc(t) for t in as_list(meta.get("tags")))
    right = f"archon-document · palette {esc(palette)}"
    return f"<span>{left}</span><span>{tags}</span><span>{right}</span>"


def render_page(meta, body, nav=None):
    """The finished page. `nav` holds optional up / prev / next links (see `page_nav`)."""
    crumb, toc_home, pager = render_nav(nav)
    body, toc = add_heading_ids(body.strip())
    body = TABLE_RE.sub(r'<div class="ar-scroll">\1</div>', body)
    body = add_legends(body)
    palette = palette_version()
    minutes = max(1, round(word_count(strip_tags(body)) / WORDS_PER_MINUTE))
    has_diagram = 'class="mermaid"' in body
    head_scripts = f'<script defer src="{MERMAID_URL}"></script>' if has_diagram else ""
    meta_json = json.dumps(meta, ensure_ascii=False, indent=1).replace("</", "<\\/")
    values = {
        "PALETTE": esc(palette),
        "TITLE": esc(meta.get("title", "Untitled")),
        "SUMMARY": esc(meta.get("summary", "")),
        "DOC_TYPE": esc(DOC_TYPES.get(meta.get("doc_type"), meta.get("doc_type") or "Document")),
        "CSS": css_with_dark_media(),
        "JS": JS_PATH.read_text(encoding="utf-8"),
        "HEAD_SCRIPTS": head_scripts,
        "TOC": render_toc(toc),
        "TOC_HOME": toc_home,
        "CRUMB": crumb,
        "CHIPS": render_chips(meta, minutes),
        "BODY": body,
        "PAGER": pager,
        "FOOTER": render_footer(meta, palette),
        "META_JSON": meta_json,
    }
    shell = SHELL_PATH.read_text(encoding="utf-8")
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], shell)


def meta_from_md(md_path):
    fm, _ = parse_frontmatter(md_path.read_text(encoding="utf-8"))
    if not fm:
        sys.exit(f"error: {md_path} has no YAML frontmatter")
    meta = {k: fm[k] for k in META_KEYS if fm.get(k)}
    meta["md_twin"] = md_path.name
    return meta, fm


def build(md_path, body_path, out_path):
    meta, fm = meta_from_md(md_path)
    if out_path is None:
        out_path = md_path.parent / (fm.get("html_twin") or f"{md_path.stem}.html")
    body = body_path.read_text(encoding="utf-8")
    out_path.write_text(render_page(meta, body, page_nav(md_path)), encoding="utf-8")
    print(f"built {out_path}")


def rebuild(page_path):
    page = page_path.read_text(encoding="utf-8")
    body, meta = extract_between(page, BODY_START, BODY_END), read_embedded_meta(page)
    if body is None or meta is None:
        sys.exit(f"error: {page_path} was not built by build_html.py (markers or meta missing)")
    if meta.get("kind") == INDEX_KIND:
        from build_index import write_index  # deferred: build_index imports this module

        write_index(page_path.parent, rebuild_pages=False, cascade=False)
        return
    twin = page_path.parent / meta.get("md_twin", "")
    nav = None
    if meta.get("md_twin") and twin.is_file():
        meta, _ = meta_from_md(twin)
        nav = page_nav(twin)
    page_path.write_text(render_page(meta, body, nav), encoding="utf-8")
    print(f"rebuilt {page_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--md", type=Path, help="the MD twin (frontmatter supplies title, summary, status...)")
    parser.add_argument("--body", type=Path, help="HTML body fragment: TL;DR + <section> elements")
    parser.add_argument("--out", type=Path, help="output page (default: the MD's html_twin, next to it)")
    parser.add_argument("--rebuild", type=Path, nargs="+", metavar="PAGE", help="re-render existing pages")
    args = parser.parse_args()
    if args.rebuild:
        for page in args.rebuild:
            rebuild(page)
    elif args.md and args.body:
        build(args.md, args.body, args.out)
    else:
        parser.error("pass --md and --body, or --rebuild PAGE...")


if __name__ == "__main__":
    main()
