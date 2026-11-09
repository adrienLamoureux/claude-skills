#!/usr/bin/env python3
"""focus-kit: what waits on you, across dev-kit and campaign-kit runs (standard library only).

  focus_tool.py inbox [--root DIR ...] [--all] [--json]
      One line per run folder that waits on you, oldest first. Run folders are
      <root>/.dev-kit/*/ and <root>/.campaign-kit/*/; the default root is the repository that
      holds the current directory (or the current directory), plus every folder listed in
      FOCUS_KIT_ROOTS (separated by the OS path separator). --all also lists runs that need
      nothing.

  focus_tool.py hook
      SessionStart hook: prints JSON whose systemMessage shows you the inbox, and whose
      additionalContext tells Claude the same, so it can offer to resume a run. Prints nothing
      when no run waits on you.

  focus_tool.py statusline
      Status-line segment: reads Claude Code's status-line JSON on stdin and prints
      "focus: N waiting" for that project, or nothing.

  focus_tool.py vocab list | add <term> ... | remove <term> ...
      The terms you already know, kept in ~/.claude/focus-kit/vocabulary.md (or the file in
      FOCUS_KIT_VOCAB), one "- term" line each. The SessionStart hook hands them to Claude, so
      the Reader-first style and /focus-kit:explain gloss only the terms you do not know.

  focus_tool.py page [--root DIR ...] [--out FILE]
      One self-contained HTML page with a card per run (waiting first): where it is, what it
      needs, what it did, its recap.md, and links to its key files. Default output:
      ~/.claude/focus-kit/runs.html. Prints the path as JSON. The page covers every repository
      the hooks have seen a run in (~/.claude/focus-kit/roots.txt) and reloads itself every
      minute in an open browser tab. The hooks rebuild it on their own; FOCUS_KIT_PAGE=0 stops
      them.

  focus_tool.py on-write
      PostToolUse hook for Write and Edit: when the file written is a run's resume.md, remember
      that repository and rebuild the runs page. Silent; does nothing for any other file.

  focus_tool.py dismiss <run-dir>
      Mark a run as needing nothing (writes "Needs: nothing" to its resume.md), e.g. after you
      committed an approved change but kept the run folder.

focus-kit's own files live in ~/.claude/focus-kit/, or in FOCUS_KIT_HOME when set.

Where a run stands comes from <run-dir>/resume.md, which the kits write at every stop:

    # Resume — <slug>
    - Where: <step, e.g. plan · ready, review · approve, round 2 · stop-blocked>
    - Did: <one line>
    - Needs: <what you must do or decide> | nothing

When resume.md is missing, or older than the run's other files, the state is derived from the
run's files instead (plan.md, review.md, checks, brief.md, rounds, outcome.md).
"""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

KITS = {".dev-kit": "dev-kit", ".campaign-kit": "campaign-kit"}
# Where focus-kit keeps its own files (vocabulary, known roots, runs page).
BASE = Path(os.environ.get("FOCUS_KIT_HOME") or Path.home() / ".claude" / "focus-kit").expanduser()
RESUME = "resume.md"
IDLE_SECONDS = 30 * 60      # a run untouched this long, not done, was probably interrupted
STALE_GRACE = 5             # seconds a resume.md may lag the files it describes
HOOK_LINES = 4              # runs listed in the SessionStart message; the rest are counted
DONE_QUIET_DAYS = 7         # a finished run that waited this long stops asking on its own
PACING_LIMIT = 3            # open runs one person supervises well; strain rises past it
NOTHING = re.compile(r"^\s*(nothing|none|-)?\s*\.?\s*$", re.I)
VOCAB_DEFAULT = BASE / "vocabulary.md"
VOCAB_HEADER = ("# Vocabulary\n\nTerms I already know: Claude skips their gloss. "
                "Edit freely, one '- term' per line.\n\n")
VOCAB_LIMIT = 400           # terms handed to Claude at session start
FIELD = re.compile(r"^\s*-\s*(Where|Did|Needs|Next)\s*:\s*(.*)$", re.I)


# ---------------------------------------------------------------- helpers

def manifest(path: Path, kind: str) -> dict | None:
    if not path.exists():
        return None
    match = re.search(r"```json[ \t]+" + kind + r"-manifest[ \t]*\n(.*?)\n```",
                      path.read_text(encoding="utf-8", errors="replace"), re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def verdict(path: Path) -> str | None:
    """First word after '## Verdict' in a dev-kit review.md or check report."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^##\s+Verdict\s*\n+\s*`?([a-z-]+)", text, re.M | re.I)
    return match.group(1).lower() if match else None


def newest(run: Path, skip: str | None = None) -> float:
    times = [p.stat().st_mtime for p in run.rglob("*") if p.is_file() and p.name != skip]
    return max(times, default=run.stat().st_mtime)


def ago(seconds: float) -> str:
    seconds = max(0, int(seconds))
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if seconds >= size:
            return f"{seconds // size}{unit}"
    return "now"


def repo_root(start: Path) -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start,
                         capture_output=True, text=True)
    return Path(out.stdout.strip()) if out.returncode == 0 else start


def roots(extra: list[str], start: Path | None = None) -> list[Path]:
    found = [repo_root(start or Path.cwd())]
    found += [Path(p) for p in os.environ.get("FOCUS_KIT_ROOTS", "").split(os.pathsep) if p]
    found += [Path(p) for p in extra]
    unique: list[Path] = []
    for path in found:
        path = path.expanduser().resolve()
        if path.is_dir() and path not in unique:
            unique.append(path)
    return unique


# ---------------------------------------------------------------- state

def read_resume(run: Path) -> dict | None:
    path = run / RESUME
    if not path.exists():
        return None
    fields = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = FIELD.match(line)
        if match:
            fields[match.group(1).lower()] = match.group(2).strip()
    if "needs" not in fields:
        return None
    fields["mtime"] = path.stat().st_mtime
    return fields


def dev_state(run: Path, slug: str) -> tuple[str, str]:
    """(where, needs) for a dev-kit run folder, from its files."""
    review, integration = run / "review.md", run / "checks" / "integration.md"
    plan = manifest(run / "plan.md", "plan")
    if review.exists() and not (integration.exists()
                                and integration.stat().st_mtime > review.stat().st_mtime):
        v = verdict(review)
        if v == "approve":
            return "review · approve", "read Where to look in review.md, then commit"
        if v == "changes-required":
            return "review · changes-required", f"decide: /dev-kit:implement {slug} fix"
        if v == "blocked":
            return "review · blocked", "replan: /dev-kit:plan with review.md as the ticket"
        return "review", "read review.md"
    if integration.exists():
        if verdict(integration) == "fail":
            return "implement · integration failed", "read checks/integration.md"
        return "implement · done", f"run /dev-kit:review {slug}"
    if plan is not None:
        if plan.get("approved") is not True:
            return "plan · ready", "approve, edit or resize the plan"
        if (run / "base.txt").exists():
            return "implement · in progress", ""
        return "plan · approved", f"run /dev-kit:implement {slug}"
    if (run / "investigation.md").exists():
        return "investigate · done", "choose: run the experiment or plan a fix"
    return "plan · in progress", ""


def campaign_state(run: Path, slug: str) -> tuple[str, str]:
    """(where, needs) for a campaign-kit run folder, from its files."""
    if (run / "outcome.md").exists() or (run / "report.md").exists():
        return "done", "read Where to look in outcome.md, then keep or drop the work"
    brief = manifest(run / "brief.md", "brief")
    if brief is None:
        return "interview", ""
    if brief.get("approved") is not True:
        return "brief · ready", "approve or edit the brief"
    numbers = sorted(int(p.name) for p in (run / "rounds").glob("*") if p.name.isdigit())
    if not numbers:
        return "round 1 · planning", ""
    n = numbers[-1]
    rdir = run / "rounds" / str(n)
    review = manifest(rdir / "review.md", "review")
    if review:
        asks = review.get("needs_user") or []
        if asks or review.get("verdict") == "stop-blocked":
            first = asks[0] if asks else review.get("reason", "see the review")
            return f"round {n} · {review.get('verdict')}", f"answer: {first}"
    plan = manifest(rdir / "plan.md", "round")
    if plan and plan.get("approved") is not True and n > 1:
        prev = manifest(run / "rounds" / str(n - 1) / "review.md", "review") or {}
        autonomy = brief.get("autonomy")
        if autonomy == "checkpoint-each-round" or (prev.get("verdict") == "pivot"
                                                    and autonomy != "unattended"):
            return f"round {n} · plan ready", f"approve round {n}"
    return f"round {n} · running", ""


def run_entry(run: Path, kit: str, now: float) -> dict:
    slug = run.name
    resume = read_resume(run)
    latest = newest(run, skip=RESUME)
    stale = resume is not None and resume["mtime"] + STALE_GRACE < latest
    explicit_nothing = False
    if resume and not stale:
        explicit_nothing = bool(NOTHING.match(resume["needs"]))
        needs = "" if explicit_nothing else resume["needs"]
        where, did, since = resume.get("where", ""), resume.get("did", ""), resume["mtime"]
    else:
        where, needs = (dev_state if kit == "dev-kit" else campaign_state)(run, slug)
        did, since = "", latest
    finished = where.startswith("done") or where == "review · approve"
    if finished and needs and now - since > DONE_QUIET_DAYS * 86400:
        needs = ""  # nobody acted on it for a week: stop asking
    if (not needs and not explicit_nothing and not finished
            and now - latest > IDLE_SECONDS):
        needs = "interrupted? resume it"
        if kit == "campaign-kit":
            needs += f" with /campaign-kit:campaign {slug}"
        elif where.startswith("implement"):
            needs += f" with /dev-kit:implement {slug}"
        elif where.startswith("plan"):
            needs += " with /dev-kit:plan"
    return {"kit": kit, "slug": slug, "run": str(run), "where": where, "did": did,
            "needs": needs, "since": since, "age": ago(now - since), "stale": stale}


def collect(extra: list[str], everything: bool, start: Path | None = None) -> list[dict]:
    now = time.time()
    entries = []
    for root in roots(extra, start):
        for folder, kit in KITS.items():
            base = root / folder
            if not base.is_dir():
                continue
            for run in sorted(p for p in base.iterdir() if p.is_dir()):
                entry = run_entry(run, kit, now)
                entry["root"] = str(root)
                if everything or entry["needs"]:
                    entries.append(entry)
    return sorted(entries, key=lambda e: e["since"])


def line(entry: dict, many_roots: bool) -> str:
    where = f" · {entry['where']}" if entry["where"] else ""
    place = f"{Path(entry['root']).name}/" if many_roots else ""
    needs = entry["needs"] or "nothing"
    return f"- {entry['age']:>4} · {entry['kit']} {place}{entry['slug']}{where} — {needs}"


def render(entries: list[dict], limit: int | None = None) -> str:
    waiting = [e for e in entries if e["needs"]]
    many = len({e["root"] for e in entries}) > 1
    head = (f"{len(waiting)} run(s) wait on you, oldest first:" if waiting
            else "Nothing waits on you.")
    shown = entries if limit is None else entries[:limit]
    rows = [head] + [line(e, many) for e in shown]
    if len(entries) > len(shown):
        rows.append(f"- and {len(entries) - len(shown)} more: /focus-kit:inbox")
    if len(waiting) > PACING_LIMIT:
        rows.append(f"Pacing: {len(waiting)} open at once, more than {PACING_LIMIT}. Close or "
                    "dismiss one before starting another.")
    return "\n".join(rows)


# ---------------------------------------------------------------- vocabulary

def vocab_path() -> Path:
    return Path(os.environ.get("FOCUS_KIT_VOCAB") or VOCAB_DEFAULT).expanduser()


def vocab_terms() -> list[str]:
    path = vocab_path()
    if not path.exists():
        return []
    terms = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"^\s*[-*]\s+(.+?)\s*(?:—.*)?$", raw)
        if match and match.group(1).lower() not in {t.lower() for t in terms}:
            terms.append(match.group(1))
    return terms


def vocab_write(terms: list[str]) -> None:
    path = vocab_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(f"- {term}\n" for term in sorted(terms, key=str.lower))
    path.write_text(VOCAB_HEADER + body, encoding="utf-8")


def cmd_vocab(args: list[str]) -> int:
    action, terms = (args[0] if args else "list"), [a.strip() for a in args[1:] if a.strip()]
    known = vocab_terms()
    lower = {t.lower() for t in known}
    if action == "list":
        print(json.dumps({"ok": True, "file": str(vocab_path()), "terms": known},
                         ensure_ascii=False))
        return 0
    if action == "add" and terms:
        added = []
        for term in terms:
            if term.lower() not in lower:
                added.append(term)
                lower.add(term.lower())
        vocab_write(known + added)
        print(json.dumps({"ok": True, "added": added, "count": len(known) + len(added)},
                         ensure_ascii=False))
        return 0
    if action == "remove" and terms:
        drop = {t.lower() for t in terms}
        kept = [t for t in known if t.lower() not in drop]
        vocab_write(kept)
        print(json.dumps({"ok": True, "removed": len(known) - len(kept), "count": len(kept)},
                         ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


# ---------------------------------------------------------------- page

PAGE_DEFAULT = BASE / "runs.html"
ROOTS_FILE = BASE / "roots.txt"


def known_roots() -> list[str]:
    if not ROOTS_FILE.exists():
        return []
    return [line.strip() for line in ROOTS_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and Path(line.strip()).is_dir()]


def remember_root(root: Path) -> None:
    root = str(root.resolve())
    if root in known_roots():
        return
    ROOTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ROOTS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(root + "\n")


def write_page(extra: list[str], out: Path) -> dict:
    entries = collect(extra + known_roots(), True)
    entries.sort(key=lambda e: (not e["needs"], e["since"]))
    waiting = sum(1 for e in entries if e["needs"])
    stamp = time.strftime("%Y-%m-%d %H:%M")
    body = ("".join(card(e) for e in entries) if entries
            else '<p class="empty">No dev-kit or campaign-kit runs found.</p>')
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="refresh" content="60">'
            f'<title>Runs waiting on you</title><style>{PAGE_CSS}</style></head><body><main>'
            f'<h1>{waiting} of {len(entries)} run(s) wait on you</h1>'
            f'<p class="sub">focus-kit · {stamp} · waiting first, oldest first · '
            f'refreshes every minute</p>'
            f'<div class="grid">{body}</div></main></body></html>')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return {"ok": True, "page": str(out), "runs": len(entries), "waiting": waiting}


def auto_page() -> None:
    """Rebuild the default page from a hook; never fails the hook."""
    if os.environ.get("FOCUS_KIT_PAGE") == "0" or not known_roots():
        return
    try:
        write_page([], PAGE_DEFAULT)
    except OSError:
        pass
KEY_FILES = ("resume.md", "recap.md", "review.md", "plan.md", "outcome.md", "brief.md",
             "investigation.md", "ledger.md")
PAGE_CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--mute:#6b6b66;--line:#e3e2dc;--wait:#b4570b;
--wait-bg:#fff3e6;--ok:#2f7d4f;--ok-bg:#eaf6ee;--code:#f0efea}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#20201e;--ink:#ecebe6;--mute:#a3a29b;
--line:#34332f;--wait:#f0a35c;--wait-bg:#3a2a1a;--ok:#7cc79a;--ok-bg:#1d3326;--code:#2a2a27}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mute);margin:0 0 20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;
min-width:0}.card.wait{border-top:4px solid var(--wait)}.card.ok{border-top:4px solid var(--ok)}
.top{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.slug{font-weight:650;overflow-wrap:anywhere}.age{color:var(--mute);font-size:13px;white-space:nowrap}
.kit{color:var(--mute);font-size:13px}.chip{display:inline-block;border-radius:999px;padding:2px 9px;
font-size:12.5px;margin:8px 0 6px}.wait .chip{background:var(--wait-bg);color:var(--wait)}
.ok .chip{background:var(--ok-bg);color:var(--ok)}.needs{font-weight:600;margin:2px 0 6px}
.did{color:var(--mute);margin:0 0 6px}pre{background:var(--code);border-radius:6px;padding:8px 10px;
font-size:12.5px;white-space:pre-wrap;overflow-wrap:anywhere;margin:8px 0}
.files a{color:inherit;font-size:13px;margin-right:10px}.empty{color:var(--mute)}
"""


def card(entry: dict) -> str:
    run = Path(entry["run"])
    esc = html.escape
    waiting = bool(entry["needs"])
    recap = run / "recap.md"
    recap_html = ""
    if recap.exists():
        lines = recap.read_text(encoding="utf-8", errors="replace").strip().splitlines()[:9]
        recap_html = f"<pre>{esc(chr(10).join(lines))}</pre>"
    links = " ".join(f'<a href="{esc(p.as_uri())}">{esc(p.name)}</a>'
                     for p in (run / name for name in KEY_FILES) if p.exists())
    did = f'<p class="did">{esc(entry["did"])}</p>' if entry["did"] else ""
    return (f'<article class="card {"wait" if waiting else "ok"}">'
            f'<div class="top"><span class="slug">{esc(entry["slug"])}</span>'
            f'<span class="age">{esc(entry["age"])} ago</span></div>'
            f'<div class="kit">{esc(entry["kit"])} · {esc(Path(entry["root"]).name)}</div>'
            f'<span class="chip">{esc(entry["where"] or "—")}</span>'
            f'<p class="needs">{esc(entry["needs"] or "Nothing needed")}</p>{did}{recap_html}'
            f'<div class="files">{links}</div></article>')


def cmd_page(args: list[str]) -> int:
    extra, out = [], PAGE_DEFAULT
    while args:
        flag = args.pop(0)
        if flag == "--root" and args:
            extra.append(args.pop(0))
        elif flag == "--out" and args:
            out = Path(args.pop(0)).expanduser()
        else:
            print(__doc__)
            return 2
    print(json.dumps(write_page(extra, out)))
    return 0


def cmd_on_write() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith("/" + RESUME):
        return 0
    run = Path(path)
    if not run.is_absolute():
        run = Path(payload.get("cwd") or Path.cwd()) / run
    kit_dir = run.parent.parent
    if kit_dir.name in KITS:
        remember_root(kit_dir.parent)
        auto_page()
    return 0


# ---------------------------------------------------------------- commands

def cmd_inbox(args: list[str]) -> int:
    extra, everything, as_json = [], False, False
    while args:
        flag = args.pop(0)
        if flag == "--root" and args:
            extra.append(args.pop(0))
        elif flag == "--all":
            everything = True
        elif flag == "--json":
            as_json = True
        else:
            print(__doc__)
            return 2
    entries = collect(extra, everything)
    if as_json:
        print(json.dumps({"ok": True, "waiting": sum(1 for e in entries if e["needs"]),
                          "runs": entries}, indent=2, ensure_ascii=False))
    else:
        print(render(entries))
    return 0


def cmd_hook() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}
    start = Path(payload.get("cwd") or Path.cwd())
    entries = collect([], False, start)
    for root in {e["root"] for e in entries}:
        remember_root(Path(root))
    auto_page()
    terms = vocab_terms()[:VOCAB_LIMIT]
    if not entries and not terms:
        return 0
    context, out = [], {}
    if entries:
        out["systemMessage"] = "focus-kit · " + render(entries, limit=HOOK_LINES)
        context.append("focus-kit inbox (runs waiting on the user; offer to resume one only if "
                       "the user's request is about it):\n" + render(entries))
        if sum(1 for e in entries if e["needs"]) > PACING_LIMIT:
            context.append(f"focus-kit pacing: more than {PACING_LIMIT} runs already wait on the "
                           "user. If they start a new dev-kit or campaign-kit run, say so once, "
                           "in one line, and go on.")
    if terms:
        context.append("focus-kit vocabulary — terms the user already knows; do not gloss "
                       "them: " + ", ".join(terms))
    out["hookSpecificOutput"] = {"hookEventName": "SessionStart",
                                 "additionalContext": "\n\n".join(context)}
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_statusline() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}
    workspace = payload.get("workspace") or {}
    start = Path(workspace.get("project_dir") or payload.get("cwd") or Path.cwd())
    if start.is_dir():
        waiting = sum(1 for e in collect([], False, start) if e["needs"])
        if waiting:
            print(f"focus: {waiting} waiting")
    return 0


def cmd_dismiss(args: list[str]) -> int:
    if len(args) != 1 or not Path(args[0]).is_dir():
        print(__doc__)
        return 2
    run = Path(args[0])
    path = run / RESUME
    fields = read_resume(run) or {}
    where = fields.get("where") or "dismissed"
    did = fields.get("did") or "dismissed from the focus-kit inbox"
    path.write_text(f"# Resume — {run.name}\n- Where: {where}\n- Did: {did}\n- Needs: nothing\n",
                    encoding="utf-8")
    print(json.dumps({"ok": True, "dismissed": str(path)}))
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    command, rest = argv[0], argv[1:]
    if command == "inbox":
        return cmd_inbox(rest)
    if command == "hook":
        return cmd_hook()
    if command == "statusline":
        return cmd_statusline()
    if command == "on-write":
        return cmd_on_write()
    if command == "page":
        return cmd_page(rest)
    if command == "vocab":
        return cmd_vocab(rest)
    if command == "dismiss":
        return cmd_dismiss(rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
