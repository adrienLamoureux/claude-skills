#!/usr/bin/env python3
"""Replay real past prompts through the routing classifier (local only, no model calls).

    python3 prototypes/dev-kit-routing/replay_transcripts.py [--show] [project-dir-name ...]

Reads the top-level session transcripts in ~/.claude/projects/<dir>/*.jsonl (subagent
transcripts excluded), keeps the user's typed prompts, classifies each one the way the
UserPromptSubmit hook would, and prints how many would fire. --show prints a 90-character
excerpt of each fired prompt so a person can label it. Nothing leaves the machine.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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


def prompts(project_dir: Path):
    for path in sorted(project_dir.glob("*.jsonl")):
        cwd = None
        for line in path.open(encoding="utf-8", errors="ignore"):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            cwd = rec.get("cwd") or cwd
            if rec.get("type") != "user" or rec.get("isMeta") or rec.get("isSidechain"):
                continue
            content = (rec.get("message") or {}).get("content")
            if isinstance(content, list):
                if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
                    continue
                content = "\n".join(c.get("text", "") for c in content
                                    if isinstance(c, dict) and c.get("type") == "text")
            if not isinstance(content, str) or not content.strip():
                continue
            if content.lstrip().startswith(SKIP_PREFIXES):
                continue
            yield cwd, content


def main() -> int:
    show = "--show" in sys.argv
    dirs = [a for a in sys.argv[1:] if not a.startswith("--")] or DEFAULT_DIRS
    total = fired = skipped = 0
    per_route: dict[str, int] = {}
    for name in dirs:
        pdir = PROJECTS / name
        if not pdir.is_dir():
            continue
        n = f = 0
        for cwd, text in prompts(pdir):
            if text.lstrip().startswith(("<", route.SYNTHETIC[0])):
                skipped += 1  # task notes and compaction summaries: the hook skips them, not typed
                continue
            root = route.find_root(cwd or "") if cwd and Path(cwd).exists() else None
            r = route.classify_prompt(text, route.list_repo_areas(root) if root else None, root)
            n += 1
            if r["route"]:
                f += 1
                per_route[r["route"]] = per_route.get(r["route"], 0) + 1
                if show:
                    detail = ",".join(r["areas"]) or r["signal"]
                    print(f"  {r['route'].upper():11} [{detail}] {text[:90]!r}")
        print(f"{name}: {f}/{n} prompts would get a note")
        total, fired = total + n, fired + f
    print(f"TOTAL: {fired}/{total} typed prompts would get a note "
          f"({(fired / total * 100 if total else 0):.1f}%), by route: {per_route}; "
          f"{skipped} task notes and compaction summaries skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
