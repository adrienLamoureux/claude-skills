#!/usr/bin/env python3
"""Fixture for plugins/focus-kit/scripts/focus_tool.py (standard library only).

Run:  python3 -I prototypes/focus-kit-trial/check_focus_tool.py

Builds run folders in a throw-away temp dir (not a git repo), calls the script by subprocess
with FOCUS_KIT_HOME pointed inside that dir (never the real ~/.claude), and prints
PASS <case> / FAIL <case>: <detail>, then "ok: N/N". Exits 1 on any failure.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "plugins" / "focus-kit" / "scripts" / "focus_tool.py"
HOOKS = REPO / "plugins" / "focus-kit" / "hooks" / "hooks.json"
DAY = 86400

TMP = Path(tempfile.mkdtemp(prefix="focus-tool-check-")).resolve()
HOME = TMP / "home"
RESULTS: list[tuple[str, str | None]] = []


def env(home: Path = HOME) -> dict:
    out = dict(os.environ)
    for name in ("FOCUS_KIT_ROOTS", "FOCUS_KIT_PAGE", "FOCUS_KIT_VOCAB"):
        out.pop(name, None)
    out["FOCUS_KIT_HOME"] = str(home)
    return out


def tool(args: list[str], cwd: Path, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], cwd=cwd, input=stdin, env=env(),
                          capture_output=True, text=True, timeout=60)


def make_root(name: str) -> Path:
    root = TMP / name
    root.mkdir(parents=True)
    return root


def write(path: Path, text: str = "x\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def age(path: Path, seconds: float) -> None:
    stamp = time.time() - seconds
    os.utime(path, (stamp, stamp))


def review_manifest(verdict: str, needs: list[str]) -> str:
    body = json.dumps({"verdict": verdict, "needs_user": needs})
    return f"# Review\n\n```json review-manifest\n{body}\n```\n"


def resume(where: str, needs: str) -> str:
    return f"# Resume — r\n- Where: {where}\n- Did: something\n- Needs: {needs}\n"


def runs(root: Path, *flags: str) -> list[dict]:
    done = tool(["inbox", "--root", str(root), "--json", *flags], cwd=root)
    if done.returncode != 0:
        raise AssertionError(f"inbox exit {done.returncode}: {done.stderr.strip()}")
    return json.loads(done.stdout)["runs"]


def only(root: Path, *flags: str) -> dict:
    found = runs(root, *flags)
    if len(found) != 1:
        raise AssertionError(f"expected one run, got {[r['slug'] for r in found]}")
    return found[0]


def case(name: str):
    def wrap(fn):
        try:
            fn()
            RESULTS.append((name, None))
            print(f"PASS {name}")
        except Exception as exc:  # noqa: BLE001 - report every failure, keep going
            RESULTS.append((name, str(exc)))
            print(f"FAIL {name}: {exc}")
        return fn
    return wrap


def expect(actual, wanted, label: str = "") -> None:
    if actual != wanted:
        raise AssertionError(f"{label}expected {wanted!r}, got {actual!r}")


def dev_review(name: str, body: str) -> Path:
    root = make_root(name)
    run = root / ".dev-kit" / "r"
    write(run / "review.md", body)
    age(run / "review.md", 100)
    return root


@case("campaign-blocked-with-outcome")
def _():
    root = make_root("campaign-blocked")
    run = root / ".campaign-kit" / "c1"
    write(run / "rounds" / "2" / "review.md", review_manifest("stop-blocked",
                                                              ["grant DB access"]))
    write(run / "outcome.md")
    entry = only(root)
    expect(entry["where"], "round 2 · stop-blocked", "where ")
    expect(entry["needs"], "answer: grant DB access", "needs ")


@case("campaign-done")
def _():
    root = make_root("campaign-done")
    run = root / ".campaign-kit" / "c1"
    write(run / "rounds" / "1" / "review.md", review_manifest("stop-done", []))
    write(run / "outcome.md")
    expect(only(root, "--all")["where"], "done", "where ")


@case("verdict-bold")
def _():
    root = dev_review("verdict-bold", "# Review\n\n## Verdict\n\n**approve**\n")
    expect(only(root, "--all")["where"], "review · approve")


@case("verdict-inline")
def _():
    root = dev_review("verdict-inline", "# Review\n\n## Verdict: approve\n\nLooks fine.\n")
    expect(only(root, "--all")["where"], "review · approve")


@case("verdict-in-sentence")
def _():
    root = dev_review("verdict-sentence",
                      "# Review\n\n### Verdict\n\nThe verdict is changes-required.\n")
    expect(only(root, "--all")["where"], "review · changes-required")


@case("fix-in-progress")
def _():
    root = dev_review("fix-in-progress", "# Review\n\n## Verdict\n\napprove\n")
    write(root / ".dev-kit" / "r" / "slices" / "a.md")
    entry = only(root, "--all")
    expect(entry["where"], "implement · fix in progress", "where ")
    expect(entry["needs"], "", "needs ")


def stale_run(name: str, where: str) -> Path:
    root = make_root(name)
    run = root / ".dev-kit" / "r"
    path = write(run / "resume.md", resume(where, "commit it"))
    age(path, 8 * DAY)
    age(run, 8 * DAY)
    return root


@case("finished-free-text")
def _():
    root = stale_run("finished-free-text", "Review — Approved.")
    expect(runs(root), [], "inbox ")


@case("implement-done-not-finished")
def _():
    root = stale_run("implement-done", "implement · done")
    expect(only(root)["where"], "implement · done", "where ")


def count(root: Path) -> str:
    payload = json.dumps({"cwd": str(root)})
    done = tool(["statusline"], cwd=root, stdin=payload)
    if done.returncode != 0:
        raise AssertionError(f"statusline exit {done.returncode}: {done.stderr.strip()}")
    return done.stdout.strip()


@case("statusline-cached")
def _():
    root = make_root("statusline")
    run = root / ".dev-kit" / "r"
    path = write(run / "resume.md", resume("plan · ready", "approve the plan"))
    age(run, 10)
    expect(count(root), "focus: 1 waiting", "first ")
    path.write_text(resume("plan · ready", "nothing"), encoding="utf-8")
    expect(count(root), "focus: 1 waiting", "cached ")
    payload = json.dumps({"tool_input": {"file_path": str(path)}, "cwd": str(root)})
    tool(["on-write"], cwd=root, stdin=payload)
    expect(count(root), "", "after on-write ")
    path.write_text(resume("plan · ready", "approve the plan"), encoding="utf-8")
    expect(count(root), "", "cached zero ")
    cache = HOME / "statusline.json"
    data = json.loads(cache.read_text(encoding="utf-8"))
    for entry in data.values():
        entry["at"] = time.time() - 400
    cache.write_text(json.dumps(data), encoding="utf-8")
    expect(count(root), "focus: 1 waiting", "expired ")


@case("hook-writes-cache")
def _():
    root = make_root("hook")
    write(root / ".dev-kit" / "r" / "resume.md", resume("plan · ready", "approve the plan"))
    (HOME / "statusline.json").unlink(missing_ok=True)
    done = tool(["hook"], cwd=root, stdin=json.dumps({"cwd": str(root)}))
    if done.returncode != 0:
        raise AssertionError(f"hook exit {done.returncode}: {done.stderr.strip()}")
    data = json.loads((HOME / "statusline.json").read_text(encoding="utf-8"))
    expect(data[str(root)]["waiting"], 1, "waiting ")


@case("page")
def _():
    root = make_root("page")
    write(root / ".dev-kit" / "r" / "resume.md", resume("plan · ready", "approve the plan"))
    out = TMP / "runs.html"
    done = tool(["page", "--root", str(root), "--out", str(out)], cwd=root)
    if done.returncode != 0:
        raise AssertionError(f"page exit {done.returncode}: {done.stderr.strip()}")
    expect(json.loads(done.stdout).get("ok"), True, "ok ")
    if not out.exists():
        raise AssertionError("page file missing")


@case("hook-guard")
def _():
    command = json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]["PostToolUse"][0]["hooks"][0]
    if "args" in command:
        raise AssertionError("hook entry must not carry an args key")
    guard_home, fake_bin, log = TMP / "guard-home", TMP / "fake-bin", TMP / "python-calls.log"
    write(fake_bin / "python3",
          f'#!/bin/sh\necho called >> "{log}"\nexec "{sys.executable}" "$@"\n')
    (fake_bin / "python3").chmod(0o755)
    run_env = env(guard_home)
    run_env["PATH"] = f"{fake_bin}{os.pathsep}{run_env['PATH']}"
    run_env["CLAUDE_PLUGIN_ROOT"] = str(REPO / "plugins" / "focus-kit")

    def fire(path: str) -> None:
        done = subprocess.run(["sh", "-c", command["command"]], env=run_env, cwd=TMP,
                              input=json.dumps({"tool_input": {"file_path": path}}),
                              capture_output=True, text=True, timeout=60)
        expect(done.returncode, 0, "exit ")

    def calls() -> int:
        return len(log.read_text().splitlines()) if log.exists() else 0

    fire("/x/notes.md")
    expect(calls(), 0, "notes.md python calls ")
    guarded = make_root("guarded")
    fire(str(guarded / ".dev-kit" / "r" / "resume.md"))
    expect(calls(), 1, "resume.md python calls ")
    roots = (guard_home / "roots.txt").read_text(encoding="utf-8").split()
    if str(guarded) not in roots:
        raise AssertionError(f"{guarded} not in roots.txt: {roots}")


@case("dismiss-clears-cache")
def _():
    root = make_root("dismiss")
    run = root / ".dev-kit" / "r"
    write(run / "resume.md", resume("review · approve", "read Where to look, then commit"))
    age(run, 10)
    expect(count(root), "focus: 1 waiting", "before dismiss ")
    done = tool(["dismiss", str(run)], cwd=root)
    expect(done.returncode, 0, "dismiss exit ")
    expect(count(root), "", "after dismiss ")


@case("on-write-survives-cache-error")
def _():
    # A directory where the cache file should be: unlink raises, the hook must go on anyway.
    home = TMP / "stuck-home"
    write(home / "statusline.json" / "keep", "x\n")
    root = make_root("stuck")
    path = write(root / ".dev-kit" / "r" / "resume.md", resume("plan · ready", "approve"))
    payload = json.dumps({"tool_input": {"file_path": str(path)}, "cwd": str(root)})
    done = subprocess.run([sys.executable, str(TOOL), "on-write"], cwd=root, input=payload,
                          env=env(home), capture_output=True, text=True, timeout=60)
    expect(done.returncode, 0, "exit ")
    roots = (home / "roots.txt").read_text(encoding="utf-8").split() \
        if (home / "roots.txt").exists() else []
    if str(root) not in roots:
        raise AssertionError(f"{root} not registered after a cache error: {roots}")
    if not (home / "runs.html").exists():
        raise AssertionError("runs page not rebuilt after a cache error")


passed = sum(1 for _, err in RESULTS if err is None)
shutil.rmtree(TMP, ignore_errors=True)
print(f"ok: {passed}/{len(RESULTS)}")
sys.exit(0 if passed == len(RESULTS) else 1)
