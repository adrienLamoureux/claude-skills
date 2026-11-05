#!/usr/bin/env python3
"""State and checks for a campaign-kit run folder (standard library only).

  campaign_tool.py next <dir>
      Read the folder and print the next step of the ReAct loop as JSON, with the round
      number, the lanes still to run, and the effort the judge should get. Resumable: run it
      after any interruption.

  campaign_tool.py check <dir> [round]
      Validate brief.md and a round plan (default: the latest). Exit 1 on errors.

  campaign_tool.py approve <dir> brief | round <n>
      Mark the brief or a round plan approved (only after the user says yes, or when the
      brief's autonomy allows it).

  campaign_tool.py status <dir>
      Criteria values per round and the last verdict, for a compact progress report.

Every machine-read block is a fenced ```json <kind>-manifest``` inside a Markdown file.

The final report is outcome.md. Runs started before campaign-kit 0.2.0 wrote report.md, which
is still accepted. Claude Code refuses a subagent's Write to any .md file whose name starts with
report, summary, findings or analysis, so no file the agents write may be named that way, and
lane ids (a lane writes rounds/<n>/<lane>.md) may not start with those words either.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AUTONOMY = {"checkpoint-each-round", "checkpoint-on-pivot", "unattended"}
LANE_KINDS = {"code", "research", "docs", "data", "ops", "other"}
RUNNER_EFFORTS = {"medium", "high"}
VERDICTS = {"continue", "pivot", "stop-done", "stop-blocked", "stop-budget"}
LANE_STATUS = {"pass", "partial", "fail", "needs-human"}
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WILDCARDS = "*?["
# Claude Code blocks a subagent's Write to `^(REPORT|SUMMARY|FINDINGS|ANALYSIS).*\.md$` (any case).
BLOCKED_NAME = re.compile(r"^(report|summary|findings|analysis)", re.I)
BLOCKED_HINT = ("must not start with report, summary, findings or analysis: Claude Code blocks "
                "subagent writes to such .md files")
OUTCOME = "outcome.md"
LEGACY_OUTCOME = "report.md"


# ---------------------------------------------------------------- IO

def fence(kind: str) -> re.Pattern[str]:
    return re.compile(r"```json[ \t]+" + kind + r"-manifest[ \t]*\n(.*?)\n```", re.S)


def read(path: Path, kind: str) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, f"{path} does not exist"
    match = fence(kind).search(path.read_text(encoding="utf-8"))
    if not match:
        return None, f"{path}: no ```json {kind}-manifest``` block"
    try:
        return json.loads(match.group(1)), None
    except json.JSONDecodeError as exc:
        return None, f"{path}: {kind}-manifest is not valid JSON: {exc}"


def write(path: Path, kind: str, manifest: dict) -> None:
    body = json.dumps(manifest, indent=2, ensure_ascii=False)
    text = path.read_text(encoding="utf-8")
    path.write_text(fence(kind).sub(lambda _: f"```json {kind}-manifest\n{body}\n```", text, 1),
                    encoding="utf-8")


def outcome(root: Path) -> Path | None:
    """The final report, or None. outcome.md wins; report.md is from runs before 0.2.0."""
    for name in (OUTCOME, LEGACY_OUTCOME):
        if (root / name).exists():
            return root / name
    return None


def rounds(root: Path) -> list[int]:
    base = root / "rounds"
    if not base.is_dir():
        return []
    return sorted(int(p.name) for p in base.iterdir()
                  if p.is_dir() and p.name.isdigit() and (p / "plan.md").exists())


def emit(payload: dict) -> int:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("ok", True) else 1


# ---------------------------------------------------------------- overlap

def literal_prefix(pattern: str) -> str:
    pattern = pattern[2:] if pattern.startswith("./") else pattern
    cut = min((pattern.find(ch) for ch in WILDCARDS if ch in pattern), default=len(pattern))
    return pattern[:cut]


def may_overlap(a: str, b: str) -> bool:
    pa, pb = literal_prefix(a), literal_prefix(b)
    return pa.startswith(pb) or pb.startswith(pa)


# ---------------------------------------------------------------- check

def check_brief(brief: dict) -> list[str]:
    errors = []
    if not brief.get("objective"):
        errors.append("brief: objective is empty")
    criteria = brief.get("criteria") or []
    if not criteria:
        errors.append("brief: at least one done criterion is needed")
    for c in criteria:
        cid = c.get("id", "?")
        if not KEBAB.match(cid):
            errors.append(f"brief: criterion id '{cid}' must be kebab-case")
        for key in ("metric", "target", "check"):
            if not c.get(key):
                errors.append(f"brief: criterion '{cid}' needs '{key}'")
    lanes = brief.get("lanes") or []
    if not lanes:
        errors.append("brief: at least one lane is needed")
    ids = [lane.get("id") for lane in lanes]
    for lane in lanes:
        lid = lane.get("id", "?")
        if not KEBAB.match(str(lid)):
            errors.append(f"brief: lane id '{lid}' must be kebab-case")
        elif BLOCKED_NAME.match(str(lid)):
            errors.append(f"brief: lane id '{lid}' {BLOCKED_HINT}")
        if ids.count(lid) > 1:
            errors.append(f"brief: lane id '{lid}' is duplicated")
        if lane.get("kind") not in LANE_KINDS:
            errors.append(f"brief: lane '{lid}' kind must be one of {sorted(LANE_KINDS)}")
        if lane.get("kind") == "code" and not lane.get("owns"):
            errors.append(f"brief: code lane '{lid}' needs 'owns' paths")
    budget = brief.get("budget") or {}
    for key in ("max_rounds", "max_actions_per_round"):
        if not isinstance(budget.get(key), int) or budget.get(key) < 1:
            errors.append(f"brief: budget.{key} must be a positive integer")
    if brief.get("autonomy") not in AUTONOMY:
        errors.append(f"brief: autonomy must be one of {sorted(AUTONOMY)}")
    return errors


def check_round(brief: dict, plan: dict, n: int) -> list[str]:
    errors = []
    if plan.get("round") != n:
        errors.append(f"round {n}: manifest says round {plan.get('round')}")
    if not plan.get("thought"):
        errors.append(f"round {n}: 'thought' (why these actions) is empty")
    actions = plan.get("actions") or []
    if not actions:
        errors.append(f"round {n}: no actions")
    limit = (brief.get("budget") or {}).get("max_actions_per_round", 0)
    if limit and len(actions) > limit:
        errors.append(f"round {n}: {len(actions)} actions exceed max_actions_per_round={limit}")
    lanes = [a.get("lane") for a in actions]
    for a in actions:
        lane = a.get("lane", "?")
        if not KEBAB.match(str(lane)):
            errors.append(f"round {n}: lane '{lane}' must be kebab-case")
        elif BLOCKED_NAME.match(str(lane)):
            errors.append(f"round {n}: lane '{lane}' {BLOCKED_HINT}")
        if lanes.count(lane) > 1:
            errors.append(f"round {n}: lane '{lane}' has more than one action")
        if a.get("effort") not in RUNNER_EFFORTS:
            errors.append(f"round {n}: lane '{lane}' effort must be medium or high")
        for key in ("task", "acceptance"):
            if not a.get(key):
                errors.append(f"round {n}: lane '{lane}' needs '{key}'")
    for i, a in enumerate(actions):
        for b in actions[i + 1:]:
            for pa in a.get("owns", []):
                for pb in b.get("owns", []):
                    if may_overlap(pa, pb):
                        errors.append(f"round {n}: lanes '{a.get('lane')}' and '{b.get('lane')}' "
                                      f"run in parallel and may both touch '{pa}' / '{pb}'")
    return errors


def cmd_check(root: Path, n: int | None) -> int:
    brief, err = read(root / "brief.md", "brief")
    if err:
        return emit({"ok": False, "errors": [err]})
    errors = check_brief(brief)
    found = rounds(root)
    target = n if n is not None else (found[-1] if found else None)
    if target is not None:
        plan, err = read(root / "rounds" / str(target) / "plan.md", "round")
        errors.extend([err] if err else check_round(brief, plan, target))
    return emit({"ok": not errors, "errors": errors, "round": target})


# ---------------------------------------------------------------- next

def judge_effort(check: dict | None, n: int, max_rounds: int) -> str:
    if check is None:
        return "high"
    criteria = check.get("criteria") or []
    if (criteria and all(c.get("met") for c in criteria)) or n >= max_rounds:
        return "xhigh"
    lanes = check.get("lanes") or []
    if check.get("regressions") or any(l.get("status") in {"fail", "needs-human"} for l in lanes):
        return "high"
    return "medium"


def cmd_next(root: Path) -> int:
    if not (root / "brief.md").exists():
        return emit({"step": "interview", "reason": "no brief.md yet"})
    brief, err = read(root / "brief.md", "brief")
    if err:
        return emit({"ok": False, "step": "fix-brief", "errors": [err]})
    errors = check_brief(brief)
    if errors:
        return emit({"ok": False, "step": "fix-brief", "errors": errors})
    criteria = brief.get("criteria") or []
    if any("baseline" not in c for c in criteria):
        return emit({"step": "baseline", "reason": "criteria lack a measured baseline",
                     "criteria": [c["id"] for c in criteria if "baseline" not in c]})
    if brief.get("approved") is not True:
        return emit({"step": "approve-brief", "needs_user": True})

    max_rounds = brief["budget"]["max_rounds"]
    autonomy = brief["autonomy"]
    found = rounds(root)
    if not found:
        return emit({"step": "plan-round", "round": 1, "reason": "no round plan yet"})
    n = found[-1]
    rdir = root / "rounds" / str(n)
    plan, err = read(rdir / "plan.md", "round")
    if err:
        return emit({"ok": False, "step": "fix-round", "round": n, "errors": [err]})
    errors = check_round(brief, plan, n)
    if errors:
        return emit({"ok": False, "step": "fix-round", "round": n, "errors": errors})

    if plan.get("approved") is not True:
        previous = None
        if n > 1:
            previous, _ = read(root / "rounds" / str(n - 1) / "review.md", "review")
        pivot = bool(previous and previous.get("verdict") == "pivot")
        needs_user = n > 1 and (autonomy == "checkpoint-each-round"
                                or (pivot and autonomy != "unattended"))
        return emit({"step": "approve-round", "round": n, "needs_user": needs_user,
                     "pivot": pivot})

    missing = [a["lane"] for a in plan["actions"] if not (rdir / f"{a['lane']}.md").exists()]
    if missing:
        return emit({"step": "execute", "round": n, "lanes": missing,
                     "efforts": {a["lane"]: a["effort"] for a in plan["actions"]
                                 if a["lane"] in missing}})
    if not (rdir / "check.md").exists():
        return emit({"step": "check", "round": n})
    check, err = read(rdir / "check.md", "check")
    if err:
        return emit({"ok": False, "step": "fix-check", "round": n, "errors": [err]})
    if not (rdir / "review.md").exists():
        return emit({"step": "review", "round": n,
                     "judge_effort": judge_effort(check, n, max_rounds)})
    review, err = read(rdir / "review.md", "review")
    if err:
        return emit({"ok": False, "step": "fix-review", "round": n, "errors": [err]})
    verdict = review.get("verdict")
    if verdict not in VERDICTS:
        return emit({"ok": False, "step": "fix-review", "round": n,
                     "errors": [f"verdict '{verdict}' is not one of {sorted(VERDICTS)}"]})
    final = outcome(root)
    if verdict in {"continue", "pivot"}:
        if n < max_rounds:
            return emit({"step": "plan-round", "round": n + 1,
                         "reason": f"verdict {verdict} but rounds/{n + 1}/plan.md is missing"})
        verdict = "stop-budget"
    if final is None:
        return emit({"step": "report", "round": n, "final": verdict, "judge_effort": "xhigh",
                     "write": str(root / OUTCOME)})
    return emit({"step": "done", "round": n, "final": verdict, "outcome": str(final)})


# ---------------------------------------------------------------- approve / status

def cmd_approve(root: Path, what: list[str]) -> int:
    if what[:1] == ["brief"]:
        path, kind = root / "brief.md", "brief"
    elif what[:1] == ["round"] and len(what) > 1 and what[1].isdigit():
        path, kind = root / "rounds" / what[1] / "plan.md", "round"
    else:
        print(__doc__)
        return 2
    manifest, err = read(path, kind)
    if err:
        return emit({"ok": False, "errors": [err]})
    manifest["approved"] = True
    write(path, kind, manifest)
    return emit({"ok": True, "approved": str(path)})


def cmd_status(root: Path) -> int:
    brief, err = read(root / "brief.md", "brief")
    if err:
        return emit({"ok": False, "errors": [err]})
    table = {c["id"]: {"target": c.get("target"), "baseline": c.get("baseline"), "rounds": {}}
             for c in brief.get("criteria", [])}
    last = None
    for n in rounds(root):
        review, _ = read(root / "rounds" / str(n) / "review.md", "review")
        if not review:
            continue
        last = {"round": n, "verdict": review.get("verdict"), "reason": review.get("reason")}
        for c in review.get("criteria", []):
            if c.get("id") in table:
                table[c["id"]]["rounds"][n] = {"value": c.get("value"), "met": c.get("met")}
    final = outcome(root)
    return emit({"ok": True, "objective": brief.get("objective"), "criteria": table,
                 "last": last, "max_rounds": (brief.get("budget") or {}).get("max_rounds"),
                 "outcome": str(final) if final else None})


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in {"next", "check", "approve", "status"}:
        print(__doc__)
        return 2
    command, root = argv[0], Path(argv[1])
    if command == "next":
        return cmd_next(root)
    if command == "check":
        return cmd_check(root, int(argv[2]) if len(argv) > 2 and argv[2].isdigit() else None)
    if command == "approve":
        return cmd_approve(root, argv[2:])
    return cmd_status(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
