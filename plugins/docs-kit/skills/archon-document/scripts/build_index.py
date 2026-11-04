#!/usr/bin/env python3
"""Regenerate a folder's two indexes and every page's collection links.

  build_index.py docs/archon [--title "Archon docs"] [--summary "..."]

Writes, from each MD's frontmatter:
- INDEX.md   one row per doc, for agents: they read this small file instead of every doc.
- index.html the human way in: docs grouped and in reading order, a filter box, and any
             sub-folder that has its own index listed as a collection.
Then re-renders every page in the folder so its "up" link and prev/next links are current.

Grouping and order come from the optional `group` and `order` frontmatter keys; without them,
docs group by type and sort by title. `--title` and `--summary` are remembered in index.html,
so later runs need no flags. The parent folder's index (if any) is refreshed to list this
folder, and child indexes are refreshed to link up to it.
Refuses to overwrite an INDEX.md or index.html it did not generate.
"""

import argparse
import html
import sys
from pathlib import Path

from archon_common import (
    DOC_TYPE_KINDS,
    DOC_TYPES,
    INDEX_HTML_NAME,
    INDEX_KIND,
    INDEX_MARKER,
    INDEX_NAME,
    START_KIND,
    STATUSES,
    as_list,
    doc_group,
    doc_order,
    group_docs,
    load_docs,
    read_index_meta,
)
from build_html import rebuild, render_page

FILTER_MIN_ITEMS = 6  # below this many cards a filter box is noise
DEFAULT_SUMMARY = "Every document in this collection, grouped and in reading order."


def esc(value):
    return html.escape(str(value), quote=True)


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def collections_in(folder):
    """Direct sub-folders that have a generated index.html, as (folder, meta)."""
    found = []
    for sub in sorted(p for p in folder.iterdir() if p.is_dir()):
        meta = read_index_meta(sub)
        if meta:
            found.append((sub, meta))
    return found


# ---------- INDEX.md (agents) ----------

def render_index_md(docs, collections):
    rows = []
    for doc in docs:
        meta = doc["meta"]
        twin = meta.get("html_twin", "")
        rows.append(
            f"| [{cell(meta['id'])}]({doc['md'].name}) | {cell(doc_group(meta))} "
            f"| {cell(meta.get('doc_type', ''))} | {cell(meta['summary'])} "
            f"| {cell(', '.join(as_list(meta.get('tags'))))} | {cell(meta.get('status', ''))} "
            f"| {cell(meta.get('updated', ''))} | {f'[html]({twin})' if twin else ''} |"
        )
    lines = [
        INDEX_MARKER,
        "# Archon docs index",
        "",
        "One row per doc, in reading order. Open the `.md` for agent use, the `.html` for human reading.",
        "",
        "| id | group | type | summary | tags | status | updated | page |",
        "|---|---|---|---|---|---|---|---|",
        *rows,
        "",
    ]
    if collections:
        lines += ["## Collections", ""]
        for sub, meta in collections:
            lines.append(f"- [{sub.name}/]({sub.name}/{INDEX_NAME}) — {meta.get('summary', '')}")
        lines.append("")
    return "\n".join(lines)


# ---------- index.html (people) ----------

def chip(text, cls=""):
    return f'<span class="ar-chip{cls}">{esc(text)}</span>'


def doc_card(doc, is_start):
    meta = doc["meta"]
    kind = START_KIND if is_start else DOC_TYPE_KINDS.get(meta.get("doc_type"), "info")
    href = doc["html"].name if doc["html"].is_file() else doc["md"].name
    status = meta.get("status", "")
    chips = [chip(DOC_TYPES.get(meta.get("doc_type"), meta.get("doc_type") or "Document"))]
    if status:
        chips.append(chip(status, f" is-{status}" if status in STATUSES else ""))
    if meta.get("updated"):
        chips.append(chip(meta["updated"]))
    chips.append(f'<a class="ar-chip" href="{esc(doc["md"].name)}">MD</a>')
    haystack = " ".join(
        [meta.get("id", ""), meta.get("title", ""), meta.get("summary", ""), doc_group(meta)]
        + as_list(meta.get("tags"))
        + as_list(meta.get("aliases"))
    ).lower()
    return (
        f'<div class="ar-card is-link" data-kind="{kind}" data-ar-filter-text="{esc(haystack)}">'
        f'<h3><a href="{esc(href)}">{esc(meta.get("title", doc["md"].stem))}</a></h3>'
        f'<p>{esc(meta["summary"])}</p><div class="ar-meta">{"".join(chips)}</div></div>'
    )


def collection_card(sub, meta):
    haystack = f"{sub.name} {meta.get('title', '')} {meta.get('summary', '')}".lower()
    chips = [chip("Collection"), chip(plural(meta.get('doc_count', 0), "document"))]
    if meta.get("updated"):
        chips.append(chip(meta["updated"]))
    chips.append(f'<a class="ar-chip" href="{esc(sub.name)}/{INDEX_NAME}">MD</a>')
    return (
        f'<div class="ar-card is-link" data-kind="data" data-ar-filter-text="{esc(haystack)}">'
        f'<h3><a href="{esc(sub.name)}/{INDEX_HTML_NAME}">{esc(meta.get("title", sub.name))}</a></h3>'
        f'<p>{esc(meta.get("summary", ""))}</p><div class="ar-meta">{"".join(chips)}</div></div>'
    )


def render_index_body(docs, collections):
    groups = group_docs(docs)
    ordered = any(doc_order(d["meta"]) is not None for d in docs)
    counts = plural(len(docs), "document") + " in " + plural(len(groups), "group")
    if collections:
        counts += ", plus " + plural(len(collections), "collection")
    tldr = [f"<li>{counts}.</li>"]
    if docs:
        first = docs[0]
        href = first["html"].name if first["html"].is_file() else first["md"].name
        tldr.append(f'<li>Start with <a href="{esc(href)}">{esc(first["meta"].get("title", ""))}</a>.</li>')
    if ordered:
        tldr.append("<li>Groups and documents are in reading order; each page links to the next.</li>")
    tldr.append(f'<li>Every page has a Markdown twin for agents. <a href="{INDEX_NAME}">{INDEX_NAME}</a> lists them all.</li>')
    parts = [f'<div class="ar-tldr"><p class="ar-label">Start here</p><ul>{"".join(tldr)}</ul></div>']

    if len(docs) + len(collections) >= FILTER_MIN_ITEMS:
        parts.append(
            '<div class="ar-filter"><label class="ar-label" for="ar-filter-input">Filter</label>'
            '<input id="ar-filter-input" type="search" autocomplete="off" '
            'placeholder="Title, tag or topic. Press / to focus." data-ar-filter></div>'
        )

    start_path = docs[0]["md"] if docs else None
    for name, members in groups:
        in_order = ordered and len(members) > 1
        lead = plural(len(members), "document") + (", in reading order" if in_order else "") + "."
        cards = "".join(doc_card(d, d["md"] == start_path) for d in members)
        parts.append(
            f'<section data-ar-filter-group><h2>{esc(name)}</h2><p class="ar-lead">{lead}</p>'
            f'<div class="ar-cards">{cards}</div></section>'
        )
    if collections:
        cards = "".join(collection_card(sub, meta) for sub, meta in collections)
        parts.append(
            '<section data-ar-filter-group><h2>Collections</h2>'
            '<p class="ar-lead">Sub-folders with their own index.</p>'
            f'<div class="ar-cards">{cards}</div></section>'
        )
    parts.append('<p class="ar-lead" data-ar-filter-empty hidden>No document matches the filter.</p>')
    return "\n".join(parts)


def index_meta(docs, collections, title, summary):
    audiences = {d["meta"].get("audience") for d in docs if d["meta"].get("audience")}
    dates = [str(d["meta"]["updated"]) for d in docs if d["meta"].get("updated")]
    dates += [str(m["updated"]) for _, m in collections if m.get("updated")]
    tags = []
    for doc in docs:
        tags += [t for t in as_list(doc["meta"].get("tags")) if t not in tags]
    meta = {
        "title": title,
        "summary": summary,
        "doc_type": "Collection index",
        "kind": INDEX_KIND,
        "doc_count": len(docs),
        "tags": tags[:12],
        "md_twin": INDEX_NAME,
    }
    if dates:
        meta["updated"] = max(dates)
    if len(audiences) == 1:
        meta["audience"] = audiences.pop()
    return meta


def write_index(folder, title=None, summary=None, rebuild_pages=True, cascade=True):
    """Write INDEX.md and index.html for `folder`; optionally refresh pages and neighbours."""
    folder = folder.resolve()
    md_path, html_path = folder / INDEX_NAME, folder / INDEX_HTML_NAME
    if md_path.exists() and INDEX_MARKER not in md_path.read_text(encoding="utf-8"):
        sys.exit(f"error: {md_path} exists and was not generated by build_index.py; not overwriting")
    previous = read_index_meta(folder)
    if html_path.exists() and previous is None:
        sys.exit(f"error: {html_path} exists and was not generated by build_index.py; not overwriting")

    docs, collections = load_docs(folder), collections_in(folder)
    previous = previous or {}
    title = title or previous.get("title") or folder.name.replace("-", " ").replace("_", " ").capitalize()
    summary = summary or previous.get("summary") or DEFAULT_SUMMARY
    parent = read_index_meta(folder.parent)
    nav = {"up": {"href": f"../{INDEX_HTML_NAME}", "title": parent.get("title", "Index")}} if parent else None

    md_path.write_text(render_index_md(docs, collections), encoding="utf-8")
    meta = index_meta(docs, collections, title, summary)
    html_path.write_text(render_page(meta, render_index_body(docs, collections), nav), encoding="utf-8")
    print(f"indexed {len(docs)} doc(s), {len(collections)} collection(s) -> {md_path.name}, {html_path}")

    if rebuild_pages:
        for doc in docs:
            if doc["html"].is_file():
                rebuild(doc["html"])
    if cascade:
        for sub, _ in collections:
            write_index(sub, rebuild_pages=False, cascade=False)
        if parent:
            write_index(folder.parent, rebuild_pages=False, cascade=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--title", help="collection title (remembered in index.html)")
    parser.add_argument("--summary", help="one-sentence collection summary (remembered in index.html)")
    parser.add_argument("--no-pages", action="store_true", help="skip re-rendering the folder's pages")
    args = parser.parse_args()
    if not args.folder.is_dir():
        sys.exit(f"error: {args.folder} is not a folder")
    write_index(args.folder, args.title, args.summary, rebuild_pages=not args.no_pages)


if __name__ == "__main__":
    main()
