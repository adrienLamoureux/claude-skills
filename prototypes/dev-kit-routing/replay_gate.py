#!/usr/bin/env python3
"""Replay real sessions' Edit/Write calls through the routing gate (local only, no model calls).

    python3 prototypes/dev-kit-routing/replay_gate.py [--show] [project-dir-name ...]

For each top-level session transcript in ~/.claude/projects/<dir>/*.jsonl, it feeds the typed
prompts and the main thread's Edit/Write/MultiEdit/NotebookEdit calls, in order, through the same
record_prompt() and decide_edit() the hooks use (mode gate, both kits, no approved plan). A
"task" is a typed prompt plus the edits until the next typed prompt; task notes and compaction
summaries continue the task.

It reports, per area-tracking scope ("task": areas restart at each typed prompt; "session":
they never restart):
  - one-area tasks (all repo edits in at most one area) that the gate would hold: the
    false-positive column. Root files and tests count as no area;
  - multi-area tasks it would hold, and those it would miss.
After a hold the real session went on editing, so later decisions in that task are
counterfactual; only "held at least once" is counted. Subagent edits are not replayed. When a
session's repo no longer exists on disk, its first working folder stands in as the root for
areas, and prompts are classified without on-disk path checks.
--show prints a 90-character excerpt of each held or missed task's prompt for labelling.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

os.environ.pop("CLAUDE_PROJECT_DIR", None)
REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("route", REPO / "plugins/dev-kit/hooks/route.py")
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)

PROJECTS = Path.home() / ".claude" / "projects"
DEFAULT_DIRS = ["-Users-adrienlamoureux-Documents-code-claude-skills",
                "-Users-adrienlamoureux-Documents-code-whisk-proto-gcp",
                "-Users-adrienlamoureux-Documents-code-static-web-aws-ai",
                "-Users-adrienlamoureux-Documents-code"]
SKIP_PREFIXES = ("<command-", "<local-command", "Caveat:", "[Request interrupted", "<bash-")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def events(path: Path):
    """Yield ("prompt", cwd, text) and ("edit", cwd, file_path) in transcript order."""
    cwd = None
    for line in path.open(encoding="utf-8", errors="ignore"):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        cwd = rec.get("cwd") or cwd
        if rec.get("isSidechain") or rec.get("isMeta"):
            continue
        msg = rec.get("message") or {}
        content = msg.get("content")
        if rec.get("type") == "user":
            if isinstance(content, list):
                if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
                    continue
                content = "\n".join(c.get("text", "") for c in content
                                    if isinstance(c, dict) and c.get("type") == "text")
            if isinstance(content, str) and content.strip() and not content.lstrip().startswith(SKIP_PREFIXES):
                yield "prompt", cwd, content
        elif rec.get("type") == "assistant" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") in EDIT_TOOLS:
                    inp = block.get("input") or {}
                    fp = inp.get("file_path") or inp.get("notebook_path")
                    if fp:
                        yield "edit", cwd, fp


def replay(dirs: list[str], scope: str) -> list[dict]:
    tasks: list[dict] = []
    for name in dirs:
        pdir = PROJECTS / name
        if not pdir.is_dir():
            continue
        for path in sorted(pdir.glob("*.jsonl")):
            states = {k: route.new_state() for k in route.KIT_ROUTES}
            task = None
            session_root = None  # a repo that no longer exists: the session's first working folder
            for kind, cwd, value in events(path):
                live = route.find_root(cwd or "") if cwd and Path(cwd).exists() else None
                if session_root is None and cwd:
                    session_root = live or Path(cwd)
                root = live or session_root
                if kind == "prompt":
                    result = route.classify_prompt(value, route.list_repo_areas(live) if live else None, live)
                    for kit, st in states.items():
                        route.record_prompt(st, result, kit, spread_scope=scope)
                    if result["why"] in route.ENVELOPE_WHYS:
                        continue
                    task = {"project": name, "prompt": value, "route": result["route"],
                            "areas": set(), "edits": 0, "held": set()}
                    tasks.append(task)
                    continue
                if task is None or root is None:
                    continue
                parts = route._repo_relative(value, root)
                if not parts or parts[0] in (".dev-kit", ".campaign-kit", ".git"):
                    continue
                task["edits"] += 1
                area = route._area_of_parts(parts)
                if area:
                    task["areas"].add(area)
                for kit, st in states.items():
                    out = route.decide_edit(st, value, root, "gate", kit, plan_ok=lambda: False)
                    if out and out.get("permissionDecision") == "deny":
                        reason = out["permissionDecisionReason"]
                        task["held"].add("campaign" if kit == "campaign-kit" else
                                         "plan" if "Repo edits are held" in reason else
                                         "investigate" if "bug report" in reason else "spread")
    return [t for t in tasks if t["edits"]]


def summarise(tasks: list[dict], scope: str, show: bool) -> dict:
    one = [t for t in tasks if len(t["areas"]) <= 1]
    multi = [t for t in tasks if len(t["areas"]) >= 2]
    one_held = [t for t in one if t["held"]]
    multi_held = [t for t in multi if t["held"]]
    kinds: dict[str, int] = {}
    for t in one_held:
        for k in t["held"]:
            kinds[k] = kinds.get(k, 0) + 1
    print(f"\n== scope {scope}: {len(tasks)} tasks with repo edits")
    print(f"  one-area tasks: {len(one)}; held: {len(one_held)} "
          f"({len(one_held) / len(one) * 100 if one else 0:.1f}%) by kind {kinds}")
    print(f"  multi-area tasks: {len(multi)}; held: {len(multi_held)}; missed: {len(multi) - len(multi_held)}")
    if show:
        for label, group in (("ONE-AREA HELD", one_held), ("MULTI HELD", multi_held),
                             ("MULTI MISSED", [t for t in multi if not t["held"]])):
            for t in group:
                print(f"  {label:13} {sorted(t['held']) or '-'} areas={sorted(t['areas'])} "
                      f"edits={t['edits']} {t['prompt'][:90]!r}")
    return {"tasks": len(tasks), "one_area": len(one), "one_area_held": len(one_held),
            "one_area_held_by_kind": kinds, "multi_area": len(multi), "multi_area_held": len(multi_held)}


def main() -> int:
    show = "--show" in sys.argv
    dirs = [a for a in sys.argv[1:] if not a.startswith("--")] or DEFAULT_DIRS
    for scope in ("task", "session"):
        summarise(replay(dirs, scope), scope, show)
    return 0


if __name__ == "__main__":
    sys.exit(main())
