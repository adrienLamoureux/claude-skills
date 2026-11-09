#!/usr/bin/env python3
"""Fixture: `plan_tool.py size` counts untracked files when run from a subdirectory.

Run as: python3 -I prototypes/focus-kit-trial/check_plan_size.py
Builds a temp git repo, runs `size` from `src/`, and expects the untracked files at the
repo top and under src/ to be counted for their slices. Prints `ok: 2/2`; exits 1 on failure.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = (Path(__file__).resolve().parents[2]
        / "plugins/dev-kit/skills/plan/scripts/plan_tool.py")

MANIFEST = {
    "slug": "x",
    "size": "S",
    "approved": True,
    "slices": [
        {"id": "top", "title": "top", "owns": ["top.txt"], "depends_on": [],
         "effort": "medium", "max_lines": 100, "gates": ["true"], "acceptance": ["ok"]},
        {"id": "src", "title": "src", "owns": ["src/**"], "depends_on": [],
         "effort": "medium", "max_lines": 100, "gates": ["true"], "acceptance": ["ok"]},
    ],
    "merge_order": ["top", "src"],
    "integration_gates": ["true"],
}

PLAN = "\n\n".join(
    [f"# Plan\n\n## {s}\n\nx" for s in
     ["Problem", "Non-goals", "Frozen contracts", "Slices", "Gates", "Merge order", "Risks"]]
    + ["## Manifest\n\n```json plan-manifest\n" + json.dumps(MANIFEST, indent=2) + "\n```\n"]
)


def run(args, cwd, **kw):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, **kw)


def main() -> int:
    repo = Path(tempfile.mkdtemp()).resolve()
    for cmd in (["git", "init", "-q"], ["git", "config", "user.name", "t"],
                ["git", "config", "user.email", "t@example.com"]):
        run(cmd, repo)
    (repo / "src").mkdir()
    (repo / "src/a.py").write_text("print(1)\n")
    run(["git", "add", "src/a.py"], repo)
    run(["git", "commit", "-q", "-m", "init"], repo)
    (repo / ".dev-kit/x").mkdir(parents=True)
    (repo / ".dev-kit/x/plan.md").write_text(PLAN)
    py = sys.executable
    chk = run([py, "-I", str(TOOL), "check", ".dev-kit/x/plan.md"], repo)
    if chk.returncode != 0:
        print(f"FAIL setup: plan check failed: {chk.stdout[-300:]}")
        return 1
    base = run([py, "-I", str(TOOL), "baseline", ".dev-kit/x/plan.md", ".dev-kit/x"], repo)
    if base.returncode != 0:
        print(f"FAIL setup: baseline failed: {base.stdout[-300:]}{base.stderr[-300:]}")
        return 1
    (repo / "top.txt").write_text("a\nb\nc\n")
    (repo / "src/new.py").write_text("1\n2\n3\n4\n5\n")
    out = run([py, "-I", str(TOOL), "size", "../.dev-kit/x/plan.md", "../.dev-kit/x"],
              repo / "src")
    try:
        by_slice = json.loads(out.stdout)["by_slice"]
    except (ValueError, KeyError):
        print(f"FAIL size: no JSON: {out.stdout[-300:]}{out.stderr[-300:]}")
        return 1
    passed = 0
    for sid, want in (("top", 3), ("src", 5)):
        got = by_slice.get(sid, {}).get("lines")
        if got == want:
            print(f"PASS {sid}")
            passed += 1
        else:
            print(f"FAIL {sid}: lines {got}, expected {want}")
    print(f"ok: {passed}/2")
    return 0 if passed == 2 else 1


if __name__ == "__main__":
    sys.exit(main())
