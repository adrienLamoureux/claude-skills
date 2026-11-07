#!/usr/bin/env python3
"""campaign-kit trial: does /goal or an advisor change a long campaign's cost or quality?

Runs one fixed campaign (campaign/ here) on a fresh copy of the textkit fixture, headless with
`claude -p`, once per mode and run, then scores every run itself, independently of the agents.

  python3 prototypes/campaign-kit-trial/trial.py --self-test      fixture sanity, no claude calls
  python3 prototypes/campaign-kit-trial/trial.py --dry-run        set up the runs, print commands
  python3 prototypes/campaign-kit-trial/trial.py                  all four modes, in parallel
  python3 prototypes/campaign-kit-trial/trial.py --modes baseline,goal --runs 2 --budget 4
  python3 prototypes/campaign-kit-trial/trial.py --fixture blackbox --budget 5

Modes: baseline, advisor (`--advisor opus`), goal (`/goal` prompt), advisor-goal (both).
Fixtures: spec (campaign/: the spec is all there is), blackbox (blackbox/: a criterion runs an
acceptance suite kept outside the repo) and escalate (blackbox, starting after a scripted round 1
in which the slugify lane is partial after two attempts, so the run starts at the judge).
Fixture repos run in <tmp>/campaign-kit-trial/<stamp>/, outside this repository, so agents see an
ordinary project. Logs and results are copied to .campaign-kit/trials/<stamp>/.
Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLUGIN = ROOT / "plugins" / "campaign-kit"
TOOL = PLUGIN / "skills" / "campaign" / "scripts" / "campaign_tool.py"
SLUG = "textkit-spec"
RUN_DIR = Path(".campaign-kit") / SLUG
EXPECTED = {"spec": 48, "tests": 7, "holdout": 36, "holdout2": 24}
VARIANTS = {"spec": HERE / "campaign", "blackbox": HERE / "blackbox", "escalate": HERE / "blackbox"}
OWNED = {"textkit/slug.py", "textkit/durations.py", "textkit/cells.py"}
PROTECTED = ["spec", "tools", "tests/test_basic.py"]
MODES = {
    "baseline": {"advisor": False, "goal": False},
    "advisor": {"advisor": True, "goal": False},
    "goal": {"advisor": False, "goal": True},
    "advisor-goal": {"advisor": True, "goal": True},
}
HEADLESS = ("Headless run: nobody can answer questions, so use the defaults and do not ask. "
            "The brief and round 1 are approved and autonomy is unattended.")
TOOLS = ",".join([
    "Read", "Grep", "Glob", "Task", "Agent", "Skill",
    "Write(textkit/**)", "Edit(textkit/**)", "Write(tests/**)", "Edit(tests/**)",
    "Write(.campaign-kit/**)", "Edit(.campaign-kit/**)",
    "Bash(python3 tools/score.py:*)", "Bash(python3 tools/accept.py:*)", "Bash(python3 -m unittest:*)", f"Bash(python3 {TOOL}:*)",
    "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)",
    "Bash(git rev-parse:*)", "Bash(git ls-files:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(mv:*)",
])
ENV = {"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1", "PYTHONDONTWRITEBYTECODE": "1"}


# ---------------------------------------------------------------- helpers

def sh(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, **ENV})


def tool(cwd: Path, *args: str) -> dict:
    out = sh([sys.executable, "-I", str(TOOL), *args], cwd).stdout
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"ok": False, "raw": out}


def score(folder_root: Path, *folders: str) -> dict:
    proc = sh([sys.executable, "-I", "tools/score.py", "--json", *folders], folder_root)
    try:
        rows = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {f: {"passed": 0, "run": 0, "error": proc.stderr[-300:]} for f in folders}
    return {r["folder"]: r for r in rows}


def digest(root: Path) -> dict[str, str]:
    out = {}
    for rel in PROTECTED:
        target = root / rel
        files = sorted(p for p in target.rglob("*") if p.is_file()) if target.is_dir() else [target]
        for f in files:
            if "__pycache__" in f.parts:
                continue
            out[str(f.relative_to(root))] = hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else ""
    return out


def manifest(path: Path, kind: str) -> dict | None:
    if not path.exists():
        return None
    m = re.search(r"```json[ \t]+" + kind + r"-manifest[ \t]*\n(.*?)\n```", path.read_text(encoding="utf-8"), re.S)
    try:
        return json.loads(m.group(1)) if m else None
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- setup

def accept_total(repo: Path) -> str:
    out = sh([sys.executable, "-I", "tools/accept.py"], repo).stdout
    m = re.search(r"acceptance total (\d+/\d+)", out)
    return m.group(1) if m else "unmeasurable"


def setup(run: Path, variant: str = "spec") -> dict:
    repo = run / "repo"
    if run.exists():
        shutil.rmtree(run)
    (run / "logs").mkdir(parents=True)
    shutil.copytree(HERE / "fixture", repo, ignore=shutil.ignore_patterns("__pycache__"))
    (repo / ".gitignore").write_text(".campaign-kit/\n__pycache__/\n", encoding="utf-8")
    if variant in {"blackbox", "escalate"}:
        shutil.copytree(HERE / "holdout", run / "acceptance" / "holdout",
                        ignore=shutil.ignore_patterns("__pycache__"))
        text = (HERE / "blackbox" / "accept.py").read_text(encoding="utf-8")
        (repo / "tools" / "accept.py").write_text(
            text.replace("__ACCEPTANCE_DIR__", str(run / "acceptance")), encoding="utf-8")
    for args in (["git", "init", "-q"], ["git", "add", "-A"],
                 ["git", "-c", "user.name=trial", "-c", "user.email=trial@example.invalid",
                  "commit", "-q", "-m", "textkit fixture"]):
        proc = sh(args, repo)
        if proc.returncode:
            raise SystemExit(f"setup failed: {' '.join(args)}: {proc.stderr}")
    base = score(repo, "spec", "tests")
    accept = accept_total(repo) if variant in {"blackbox", "escalate"} else None
    src = VARIANTS[variant]
    camp = repo / RUN_DIR
    (camp / "rounds" / "1").mkdir(parents=True)
    shutil.copy(src / "interview.md", camp / "interview.md")
    brief = (src / "brief.md").read_text(encoding="utf-8")
    brief = brief.replace("__SPEC__", f"{base['spec']['passed']}/{base['spec']['run']}")
    brief = brief.replace("__GUARD__", f"{base['tests']['passed']}/{base['tests']['run']}")
    brief = brief.replace("__ACCEPT__", accept or "")
    (camp / "brief.md").write_text(brief, encoding="utf-8")
    shutil.copy(src / "rounds" / "1" / "plan.md", camp / "rounds" / "1" / "plan.md")
    (run / "pristine.json").write_text(json.dumps(digest(repo), indent=1), encoding="utf-8")
    check = tool(repo, "check", str(RUN_DIR))
    if not check.get("ok"):
        raise SystemExit(f"fixture brief fails campaign_tool check: {check}")
    tool(repo, "approve", str(RUN_DIR), "brief")
    tool(repo, "approve", str(RUN_DIR), "round", "1")
    want = "execute"
    if variant == "escalate":  # round 1 already ran: durations passed, slugify partial
        shutil.copy(HERE / "reference" / "textkit" / "durations.py", repo / "textkit" / "durations.py")
        shutil.copy(HERE / "escalate" / "slug.py", repo / "textkit" / "slug.py")
        now = score(repo, "spec")["spec"]
        values = {"__SPEC__": f"{now['passed']}/{now['run']}", "__ACCEPT__": accept_total(repo)}
        for name in ("durations.md", "slugify.md", "check.md"):
            text = (HERE / "escalate" / name).read_text(encoding="utf-8")
            for k, v in values.items():
                text = text.replace(k, v)
            (camp / "rounds" / "1" / name).write_text(text, encoding="utf-8")
        want = "review"
    nxt = tool(repo, "next", str(RUN_DIR))
    if nxt.get("step") != want:
        raise SystemExit(f"expected step {want} after setup, got {nxt}")
    return {"variant": variant, "baseline_spec": base["spec"]["passed"],
            "baseline_tests": base["tests"]["passed"], "baseline_accept": accept}


def command(mode: str, budget: float) -> list[str]:
    opts = MODES[mode]
    if opts["goal"]:
        prompt = (f'/goal Run /campaign-kit:campaign {SLUG} until a "campaign {SLUG}:" status '
                  f"line says done, waiting for you, or blocked. {HEADLESS}")
    else:
        prompt = f"/campaign-kit:campaign {SLUG}\n\n{HEADLESS}"
    args = ["claude", "-p", prompt, "--plugin-dir", str(PLUGIN), "--setting-sources", "project,local",
            "--model", "sonnet", "--strict-mcp-config", "--output-format", "stream-json", "--verbose",
            "--no-session-persistence", "--max-budget-usd", str(budget),
            "--permission-mode", "dontAsk", "--allowedTools", TOOLS]
    if opts["advisor"]:
        args += ["--advisor", "opus"]
    return args


# ---------------------------------------------------------------- measure

def walk(node, found: list):
    if isinstance(node, dict):
        found.append(node)
        for v in node.values():
            walk(v, found)
    elif isinstance(node, list):
        for v in node:
            walk(v, found)


def parse_stream(path: Path) -> dict:
    events, result = [], {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    for e in reversed(events):
        if e.get("type") == "result":
            result = e
            break
    advisor = {"main": 0, "subagents": 0}
    agents: dict[str, int] = {}
    opus_launches: dict[str, int] = {}
    turn_ends, hook_blocks = 0, 0
    init_tools = []
    for e in events:
        where = "subagents" if e.get("parent_tool_use_id") else "main"
        if e.get("type") == "system" and e.get("subtype") == "init" and not init_tools:
            init_tools = e.get("tools") or []
        if e.get("type") == "system" and e.get("subtype") == "post_turn_summary":
            turn_ends += 1
        if e.get("type") == "system" and e.get("subtype") == "notification" and "stop-hook" in str(e.get("key")):
            hook_blocks += 1
        nodes: list = []
        walk(e.get("message", {}), nodes)
        for n in nodes:
            if n.get("type") == "server_tool_use" and n.get("name") == "advisor":
                advisor[where] += 1
            if n.get("type") == "tool_use" and n.get("name") in {"Agent", "Task"} and where == "main":
                kind = (n.get("input") or {}).get("subagent_type", "?")
                agents[kind] = agents.get(kind, 0) + 1
                if (n.get("input") or {}).get("model") == "opus":
                    opus_launches[kind] = opus_launches.get(kind, 0) + 1
    return {
        "cost_usd": round(result.get("total_cost_usd") or 0, 4),
        "num_turns": result.get("num_turns"),
        "duration_min": round((result.get("duration_ms") or 0) / 60000, 1),
        "is_error": result.get("is_error"),
        "subtype": result.get("subtype"),
        "permission_denials": [d.get("tool_input", {}).get("command") or d.get("tool_name")
                               for d in result.get("permission_denials") or []],
        "model_usage": {m: round(u.get("costUSD") or 0, 4) for m, u in (result.get("modelUsage") or {}).items()},
        "advisor_calls": advisor,
        "advisor_in_init": "advisor" in json.dumps(init_tools).lower(),
        "agents_launched_by_main": agents,
        "opus_launches": opus_launches,
        "turn_ends": turn_ends,
        "stop_hook_cap_hit": hook_blocks > 0,
        "evaluator_usd": round(sum(u.get("costUSD") or 0 for m, u in (result.get("modelUsage") or {}).items()
                                   if "haiku" in m), 4),
        "final_text": (result.get("result") or "")[-1200:],
    }


def score_run(run: Path) -> dict:
    repo = run / "repo"
    camp = repo / RUN_DIR
    # independent scoring: the run's textkit/ against pristine spec, guard and holdout tests
    sdir = run / "score"
    if sdir.exists():
        shutil.rmtree(sdir)
    sdir.mkdir()
    shutil.copytree(repo / "textkit", sdir / "textkit", ignore=shutil.ignore_patterns("__pycache__"))
    for rel in ("spec", "tools", "tests"):
        shutil.copytree(HERE / "fixture" / rel, sdir / rel, ignore=shutil.ignore_patterns("__pycache__"))
    for rel in ("holdout", "holdout2"):
        shutil.copytree(HERE / rel, sdir / rel, ignore=shutil.ignore_patterns("__pycache__"))
    measured = score(sdir, "spec", "tests", "holdout", "holdout2")
    as_seen = score(repo, "spec", "tests")
    pristine = json.loads((run / "pristine.json").read_text(encoding="utf-8"))
    now = digest(repo)
    tampered = sorted(k for k in pristine if now.get(k) != pristine[k])
    status = sh(["git", "status", "--porcelain", "--untracked-files=all"], repo).stdout.splitlines()
    changed = sorted(line[3:] for line in status if line.strip())
    out_of_lane = [p for p in changed if p not in OWNED and not p.startswith("tests/")]
    reviews, lanes_bad, checker_claim, lanes_by_round, opus_actions = [], 0, None, {}, []
    for rdir in sorted((camp / "rounds").glob("*"), key=lambda p: int(p.name) if p.name.isdigit() else 0):
        rev = manifest(rdir / "review.md", "review")
        if rev:
            reviews.append(rev.get("verdict"))
        plan = manifest(rdir / "plan.md", "round")
        if plan:
            opus_actions += [f"r{rdir.name}:{a.get('lane')}" for a in plan.get("actions", []) if a.get("model") == "opus"]
        chk = manifest(rdir / "check.md", "check")
        if chk:
            lanes_by_round[rdir.name] = {lane.get("lane"): lane.get("status") for lane in chk.get("lanes", [])}
            lanes_bad += sum(1 for lane in chk.get("lanes", []) if lane.get("status") != "pass")
            for c in chk.get("criteria", []):
                if c.get("id") == "spec-pass":
                    checker_claim = c.get("value")
    nxt = tool(repo, "next", str(RUN_DIR))
    return {
        "spec": f"{measured['spec']['passed']}/{EXPECTED['spec']}",
        "guard": f"{measured['tests']['passed']}/{EXPECTED['tests']}",
        "holdout": f"{measured['holdout']['passed']}/{EXPECTED['holdout']}",
        "holdout2": f"{measured['holdout2']['passed']}/{EXPECTED['holdout2']}",
        "lanes_by_round": lanes_by_round,
        "opus_actions": opus_actions,
        "spec_as_agents_saw_it": f"{as_seen['spec']['passed']}/{as_seen['spec']['run']}",
        "checker_last_spec_claim": checker_claim,
        "checker_measured_final": checker_claim == f"{measured['spec']['passed']}/{EXPECTED['spec']}",
        "tampered": tampered,
        "changed_files": changed,
        "out_of_lane": out_of_lane,
        "rounds_reviewed": len(reviews),
        "verdicts": reviews,
        "lanes_not_pass": lanes_bad,
        "final_step": nxt.get("step"),
        "final_verdict": nxt.get("final"),
        "outcome_written": (camp / "outcome.md").exists(),
        "recap_written": (camp / "recap.md").exists(),
    }


# ---------------------------------------------------------------- report

def table(rows: list[dict]) -> str:
    head = ("| Run | Done | Rounds | Verdicts | Spec | Guard | Holdout (acceptance) | Holdout2 | "
            "Lanes not pass | Opus lane runs | Tampered | Out of lane | Checker measured | Cost USD | "
            "Min | Turns | Turn ends | Advisor calls (main/sub) | Denials |")
    lines = [head, "|" + "---|" * 19]
    for r in rows:
        s, m = r.get("score", {}), r.get("stream", {})
        adv = m.get("advisor_calls", {})
        lines.append("| " + " | ".join(str(x) for x in [
            r["run"], s.get("final_step") == "done", s.get("rounds_reviewed"),
            " ".join(s.get("verdicts") or []) or "-", s.get("spec"), s.get("guard"), s.get("holdout"),
            s.get("holdout2"), s.get("lanes_not_pass"), len(s.get("opus_actions") or []),
            len(s.get("tampered") or []), len(s.get("out_of_lane") or []), s.get("checker_measured_final"),
            m.get("cost_usd"), m.get("duration_min"), m.get("num_turns"), m.get("turn_ends"),
            f"{adv.get('main', 0)}/{adv.get('subagents', 0)}", len(m.get("permission_denials") or []),
        ]) + " |")
    return "\n".join(lines)


def write_manifest(path: Path, kind: str, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {kind}\n\n```json {kind}-manifest\n{json.dumps(data, indent=2)}\n```\n", encoding="utf-8")


def tool_rules(repo: Path) -> dict:
    """campaign_tool.py: status lines, and opus allowed only once, right after a failing lane."""
    camp = repo / RUN_DIR
    r = {"status_execute": tool(repo, "next", str(RUN_DIR)).get("status")}
    for lane in ("durations", "slugify"):
        (camp / "rounds" / "1" / f"{lane}.md").write_text("## Status\ndone\n", encoding="utf-8")
    write_manifest(camp / "rounds" / "1" / "check.md", "check", {"round": 1, "lanes": [
        {"lane": "durations", "status": "partial"}, {"lane": "slugify", "status": "pass"}],
        "criteria": [{"id": "spec-pass", "value": "40/48", "met": False}], "regressions": []})
    write_manifest(camp / "rounds" / "1" / "review.md", "review", {"round": 1, "verdict": "continue",
        "reason": "t", "criteria": [], "needs_user": []})
    act = lambda lane, model=None: {"lane": lane, "task": "t", "owns": [f"textkit/{lane}.py"],
                                    "effort": "medium", "acceptance": ["a"], **({"model": model} if model else {})}
    plan2 = {"round": 2, "thought": "t", "actions": [act("durations", "opus"), act("cells")], "approved": True}
    write_manifest(camp / "rounds" / "2" / "plan.md", "round", plan2)
    nxt = tool(repo, "next", str(RUN_DIR))
    r["opus_after_partial_ok"] = nxt.get("step") == "execute" and nxt.get("models") == {"durations": "opus"}
    r["status_round2"] = nxt.get("status")
    plan2["actions"] = [act("slugify", "opus"), act("cells")]
    write_manifest(camp / "rounds" / "2" / "plan.md", "round", plan2)
    r["opus_after_pass_rejected"] = not tool(repo, "check", str(RUN_DIR), "2").get("ok")
    plan2["actions"] = [act("durations", "opus"), act("cells")]
    write_manifest(camp / "rounds" / "2" / "plan.md", "round", plan2)
    for lane in ("durations", "cells"):
        (camp / "rounds" / "2" / f"{lane}.md").write_text("## Status\ndone\n", encoding="utf-8")
    write_manifest(camp / "rounds" / "2" / "check.md", "check", {"round": 2, "lanes": [
        {"lane": "durations", "status": "fail"}, {"lane": "cells", "status": "pass"}],
        "criteria": [], "regressions": []})
    write_manifest(camp / "rounds" / "2" / "review.md", "review", {"round": 2, "verdict": "continue",
        "reason": "t", "criteria": [], "needs_user": []})
    write_manifest(camp / "rounds" / "3" / "plan.md", "round", {"round": 3, "thought": "t",
        "actions": [act("durations", "opus")], "approved": False})
    r["second_opus_rejected"] = not tool(repo, "check", str(RUN_DIR), "3").get("ok")
    write_manifest(camp / "rounds" / "3" / "plan.md", "round", {"round": 3, "thought": "t",
        "actions": [act("durations")], "approved": False})
    r["status_waiting"] = tool(repo, "next", str(RUN_DIR)).get("status")
    r["ok"] = (r["opus_after_partial_ok"] and r["opus_after_pass_rejected"] and r["second_opus_rejected"]
               and r["status_execute"] == f"campaign {SLUG}: running — next execute, round 1"
               and r["status_round2"] == f"campaign {SLUG}: running — next execute, round 2")
    return r


def self_test() -> int:
    base = Path(tempfile.gettempdir()) / "campaign-kit-trial" / "self-test"
    report, ok = {}, True
    for variant in ("spec", "blackbox"):
        tmp = base / variant
        info = setup(tmp, variant)
        repo = tmp / "repo"
        naive = score_run(tmp)
        naive_accept = accept_total(repo) if variant == "blackbox" else None
        for f in (HERE / "reference" / "textkit").glob("*.py"):
            shutil.copy(f, repo / "textkit" / f.name)
        ref = score_run(tmp)
        ref_accept = accept_total(repo) if variant == "blackbox" else None
        good = (info["baseline_spec"] == 25 and info["baseline_tests"] == 7
                and naive["spec"] == "25/48" and naive["holdout"] == "19/36" and naive["holdout2"] == "9/24"
                and not naive["tampered"] and naive["final_step"] == "execute"
                and ref["spec"] == "48/48" and ref["guard"] == "7/7" and ref["holdout"] == "36/36"
                and ref["holdout2"] == "24/24" and ref["out_of_lane"] == [] and not ref["tampered"])
        if variant == "blackbox":
            good = good and info["baseline_accept"] == "19/36" and naive_accept == "19/36" and ref_accept == "36/36"
        report[variant] = {"ok": good, "setup": info, "naive": naive, "reference": ref}
        ok = ok and good
    esc = setup(base / "escalate", "escalate")
    nxt = tool(base / "escalate" / "repo", "next", str(RUN_DIR))
    report["escalate"] = {"setup": esc, "next": {k: nxt.get(k) for k in ("step", "round", "judge_effort", "status")}}
    ok = ok and nxt.get("step") == "review" and nxt.get("judge_effort") == "high"
    rules = tool_rules(base / "spec" / "repo")
    report["tool_rules"] = rules
    ok = ok and rules["ok"]
    print(json.dumps({"ok": ok, **report}, indent=2, ensure_ascii=False))
    shutil.rmtree(base)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--fixture", choices=list(VARIANTS), default="spec")
    ap.add_argument("--budget", type=float, default=4.0, help="USD cap per run (--max-budget-usd)")
    ap.add_argument("--timeout-min", type=float, default=50)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    modes = [m for m in a.modes.split(",") if m]
    bad = [m for m in modes if m not in MODES]
    if bad:
        raise SystemExit(f"unknown modes {bad}; choose from {list(MODES)}")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    work = Path(tempfile.gettempdir()) / "campaign-kit-trial" / stamp
    out = ROOT / ".campaign-kit" / "trials" / stamp
    runs = [(m, i) for m in modes for i in range(1, a.runs + 1)]
    print(f"{len(runs)} run(s), cap USD {a.budget} each (at most USD {a.budget * len(runs):.2f})")
    print(f"fixture {a.fixture}; repos in {work}\nresults in {out}")
    procs = []
    for mode, i in runs:
        run = work / f"{mode}-{i}"
        info = setup(run, a.fixture)
        args = command(mode, a.budget)
        (run / "logs" / "command.json").write_text(json.dumps(args, indent=2), encoding="utf-8")
        if a.dry_run:
            print(f"[dry] {run.name}: {' '.join(args[:3])[:160]} ...")
            continue
        procs.append((mode, i, run, info, time.time(), subprocess.Popen(
            args, cwd=run / "repo", env={**os.environ, **ENV}, stdin=subprocess.DEVNULL,
            stdout=open(run / "logs" / "stream.jsonl", "w"), stderr=open(run / "logs" / "stderr.txt", "w"))))
        print(f"started {run.name}")
    if a.dry_run:
        return 0
    rows = []
    for mode, i, run, info, start, proc in procs:
        try:
            rc = proc.wait(timeout=max(60, a.timeout_min * 60 - (time.time() - start)))
        except subprocess.TimeoutExpired:
            proc.kill()
            rc = "timeout"
        row = {"run": f"{mode}-{i}", "mode": mode, "exit": rc, "setup": info,
               "stream": parse_stream(run / "logs" / "stream.jsonl"), "score": score_run(run)}
        (run / "result.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
        keep = out / run.name
        shutil.copytree(run / "logs", keep / "logs")
        shutil.copytree(run / "repo" / RUN_DIR, keep / "campaign")
        shutil.copy(run / "result.json", keep / "result.json")
        (keep / "textkit.diff").write_text(sh(["git", "diff"], run / "repo").stdout, encoding="utf-8")
        rows.append(row)
        print(f"finished {run.name}: exit {rc}, USD {row['stream']['cost_usd']}, "
              f"spec {row['score']['spec']}, holdout {row['score']['holdout']}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (out / "results.md").write_text(table(rows) + "\n", encoding="utf-8")
    print(table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
