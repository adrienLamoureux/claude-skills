#!/usr/bin/env python3
"""Deterministic checks for a dev-kit plan.md (standard library only).

  plan_tool.py check <plan.md>
      Validate the required sections and the ```json plan-manifest``` block, then print the
      execution waves. Exit 1 when the plan has errors.

  plan_tool.py ownership <plan.md> [--baseline FILE] [--ignore DIR ...]
      List files changed in the working tree (tracked and untracked) and the slice that owns
      each. Files that no slice owns are violations. Exit 1 when there are any. --ignore skips
      files under DIR (relative to the cwd or absolute; a DIR outside the repository is a no-op).

  plan_tool.py approve <plan.md>
      Set "approved": true in the manifest (run only after the user approves the plan).

  plan_tool.py branch <plan.md> [--name BRANCH]
      Before the first wave: when the repository is on its default branch (or on a detached
      HEAD), create and switch to a working branch, default dev-kit/<slug>, or switch to it if
      it already exists. On any other branch, stay. Never fetches, pushes or touches a remote.

  plan_tool.py size <plan.md> <run-dir> [--factor F]
      Changed lines per slice since <run-dir>/base.txt (added + deleted for tracked files, all
      lines for untracked ones), against each slice's "max_lines" budget. Files already dirty
      before the first wave (baseline-dirty.txt) and the run folder are left out. A slice over
      max_lines x F (default 1.5) is listed in "over": a warning for the checker's report, not
      a failure, so the exit code is 0 unless the tool itself fails.

  plan_tool.py baseline <plan.md> <run-dir>
      First run only: write <run-dir>/base.txt (HEAD) and <run-dir>/baseline-dirty.txt (files
      already changed before any slice ran). Later runs leave both untouched. Reports dirty
      files that fall under a slice's owned paths, since a worker would overwrite them.
      <run-dir> may be anywhere, inside the repository or outside it (a CI artifacts folder,
      a scratch directory); only a run folder inside the repository is left out of the dirty
      list.

Git commands run in the repository that contains the current directory. Paths are compared
relative to that repository's root, whichever subdirectory the tool runs from.

Output is JSON on stdout so the orchestrator reads a few lines, not the whole plan.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "problem",
    "non-goals",
    "frozen contracts",
    "slices",
    "gates",
    "merge order",
    "risks",
    "manifest",
]
SIZES = {"S", "M", "L"}
# A person reviews a diff well up to a few hundred changed lines; past this a slice should split.
SLICE_LINES_CEILING = 400
SIZE_FACTOR = 1.5
IMPLEMENTER_EFFORTS = {"medium", "high"}
SLICE_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# A slice report is slices/<id>.md, and Claude Code blocks a subagent's Write to
# `^(REPORT|SUMMARY|FINDINGS|ANALYSIS).*\.md$` (any case), so ids may not start with those words.
BLOCKED_NAME = re.compile(r"^(report|summary|findings|analysis)", re.I)
MANIFEST_FENCE = re.compile(r"```json[ \t]+plan-manifest[ \t]*\n(.*?)\n```", re.S)
WILDCARDS = "*?["


# ---------------------------------------------------------------- manifest IO

def read_manifest(text: str) -> tuple[dict | None, str | None]:
    match = MANIFEST_FENCE.search(text)
    if not match:
        return None, "no ```json plan-manifest``` block found"
    try:
        return json.loads(match.group(1)), None
    except json.JSONDecodeError as exc:
        return None, f"plan-manifest is not valid JSON: {exc}"


def write_manifest(path: Path, text: str, manifest: dict) -> None:
    body = json.dumps(manifest, indent=2, ensure_ascii=False)
    new = MANIFEST_FENCE.sub(lambda _: f"```json plan-manifest\n{body}\n```", text, count=1)
    path.write_text(new, encoding="utf-8")


# ---------------------------------------------------------------- globs

def glob_regex(pattern: str) -> re.Pattern[str]:
    """`**` crosses directories, `*` and `?` stay inside one. A bare path also owns its subtree."""
    pattern = pattern.strip()
    if pattern.startswith("./"):
        pattern = pattern[2:]
    if not any(ch in pattern for ch in WILDCARDS):
        return re.compile(re.escape(pattern.rstrip("/")) + r"(/.*)?$")
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append(r"(.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(r".*")
            i += 2
        elif pattern[i] == "*":
            out.append(r"[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append(r"[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + "$")


def literal_prefix(pattern: str) -> str:
    cut = min((pattern.find(ch) for ch in WILDCARDS if ch in pattern), default=len(pattern))
    return pattern[:cut]


def may_overlap(a: str, b: str) -> bool:
    """Conservative: two patterns may overlap when one literal prefix contains the other."""
    pa, pb = literal_prefix(a), literal_prefix(b)
    if not any(ch in a for ch in WILDCARDS) and glob_regex(b).match(a.rstrip("/")):
        return True
    if not any(ch in b for ch in WILDCARDS) and glob_regex(a).match(b.rstrip("/")):
        return True
    return pa.startswith(pb) or pb.startswith(pa)


# ---------------------------------------------------------------- check

def reachable(graph: dict[str, list[str]], start: str) -> set[str]:
    seen, stack = set(), list(graph.get(start, []))
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node)
            stack.extend(graph.get(node, []))
    return seen


def check(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    headings = [h.strip().lower() for h in re.findall(r"^##\s+(.+)$", text, re.M)]
    for section in REQUIRED_SECTIONS:
        if not any(h.startswith(section) for h in headings):
            errors.append(f"missing section '## {section.title()}'")

    plain = re.search(r"^##\s+In plain words\s*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    if not plain:
        warnings.append("no '## In plain words' section: add three jargon-free lines for the "
                        "person approving the plan")
    else:
        body = [l for l in plain.group(1).splitlines() if l.strip()]
        if len(body) > 3:
            warnings.append(f"'## In plain words' has {len(body)} lines; keep it to three")
        if "`" in plain.group(1):
            warnings.append("'## In plain words' holds code names; keep them for the sections "
                            "below")

    manifest, err = read_manifest(text)
    if err:
        errors.append(err)
        return emit({"ok": False, "errors": errors, "warnings": warnings})

    if manifest.get("size") not in SIZES:
        errors.append("manifest.size must be S, M or L")
    slices = manifest.get("slices") or []
    if not slices:
        errors.append("manifest.slices is empty")
    ids = [s.get("id", "") for s in slices]
    by_id = {s.get("id"): s for s in slices}

    for s in slices:
        sid = s.get("id", "?")
        if not SLICE_ID.match(sid):
            errors.append(f"slice id '{sid}' must be kebab-case")
        elif BLOCKED_NAME.match(sid):
            errors.append(f"slice id '{sid}' must not start with report, summary, findings or "
                          "analysis: Claude Code blocks subagent writes to slices/<id>.md then")
        if ids.count(sid) > 1:
            errors.append(f"slice id '{sid}' is duplicated")
        for key in ("owns", "gates", "acceptance"):
            if not s.get(key):
                errors.append(f"slice '{sid}' needs a non-empty '{key}' list")
        budget = s.get("max_lines")
        if budget is None:
            warnings.append(f"slice '{sid}' has no 'max_lines' budget: the size check skips it")
        elif not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
            errors.append(f"slice '{sid}' max_lines must be a positive integer")
        elif budget > SLICE_LINES_CEILING:
            warnings.append(f"slice '{sid}' expects {budget} changed lines (> "
                            f"{SLICE_LINES_CEILING}): consider splitting it so a person can "
                            "review it in one sitting")
        if s.get("effort") not in IMPLEMENTER_EFFORTS:
            errors.append(f"slice '{sid}' effort must be one of {sorted(IMPLEMENTER_EFFORTS)}")
        for dep in s.get("depends_on", []):
            if dep not in by_id:
                errors.append(f"slice '{sid}' depends on unknown slice '{dep}'")

    graph = {s.get("id"): [d for d in s.get("depends_on", []) if d in by_id] for s in slices}
    for sid in graph:
        if sid in reachable(graph, sid):
            errors.append(f"dependency cycle through slice '{sid}'")

    order = manifest.get("merge_order") or []
    if sorted(order) != sorted(ids):
        errors.append("merge_order must list every slice exactly once")
    else:
        position = {sid: i for i, sid in enumerate(order)}
        for sid, deps in graph.items():
            for dep in deps:
                if position[dep] > position[sid]:
                    errors.append(f"merge_order puts '{sid}' before its dependency '{dep}'")

    if not manifest.get("integration_gates"):
        errors.append("manifest.integration_gates is empty")

    # Slices with no dependency path between them may run in parallel: their paths must not meet.
    for i, a in enumerate(slices):
        for b in slices[i + 1:]:
            ida, idb = a.get("id"), b.get("id")
            if idb in reachable(graph, ida) or ida in reachable(graph, idb):
                continue
            for pa in a.get("owns", []):
                for pb in b.get("owns", []):
                    if may_overlap(pa, pb):
                        errors.append(
                            f"parallel slices '{ida}' and '{idb}' may both touch '{pa}' / '{pb}': "
                            "narrow 'owns' or add a depends_on")

    if manifest.get("approved") is not True:
        warnings.append("plan is not approved yet (manifest.approved != true)")

    waves = compute_waves(slices, order) if not errors else []
    return emit({
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "slug": manifest.get("slug"),
        "size": manifest.get("size"),
        "approved": manifest.get("approved") is True,
        "waves": waves,
        "efforts": {s.get("id"): s.get("effort") for s in slices},
    })


def compute_waves(slices: list[dict], order: list[str]) -> list[list[str]]:
    position = {sid: i for i, sid in enumerate(order)}
    pending = {s["id"]: set(s.get("depends_on", [])) for s in slices}
    done: set[str] = set()
    waves = []
    while pending:
        ready = sorted((sid for sid, deps in pending.items() if deps <= done), key=position.get)
        if not ready:
            break
        waves.append(ready)
        done.update(ready)
        for sid in ready:
            pending.pop(sid)
    return waves


# ---------------------------------------------------------------- git

class GitError(RuntimeError):
    pass


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def repo_root() -> Path:
    out = git("rev-parse", "--show-toplevel")
    if out.returncode != 0:
        raise GitError("not inside a git repository: run plan_tool.py from the repository "
                       "being changed")
    return Path(out.stdout.strip()).resolve()


def repo_prefix(path: Path) -> str | None:
    """`path` as a prefix relative to the repository root (`.dev-kit/x/`), or None outside it."""
    try:
        rel = path.resolve().relative_to(repo_root())
    except ValueError:
        return None
    return rel.as_posix() + "/" if rel.parts else None


# ---------------------------------------------------------------- ownership

def changed_files() -> list[str]:
    result = git("status", "--porcelain=v1", "-uall", "-z")
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or "git status failed")
    out = result.stdout  # porcelain paths are relative to the repository root
    entries, files = out.split("\0"), []
    i = 0
    while i < len(entries):
        entry = entries[i]
        if not entry:
            i += 1
            continue
        status, name = entry[:2], entry[3:]
        files.append(name)
        if "R" in status or "C" in status:
            i += 1  # the next entry is the rename source
        i += 1
    return files


def ownership(path: Path, baseline: Path | None, ignore: list[str]) -> int:
    manifest, err = read_manifest(path.read_text(encoding="utf-8"))
    if err:
        return emit({"ok": False, "errors": [err]})
    skip = set()
    if baseline and baseline.exists():
        skip = {line.strip() for line in baseline.read_text().splitlines() if line.strip()}
    # An ignore prefix may be given relative to the cwd or absolute; git reports paths relative
    # to the repository root. A prefix outside the repository matches nothing, so it is dropped.
    ignore = [p for p in (repo_prefix(Path(i)) for i in ignore) if p]
    owners = [(s["id"], [glob_regex(p) for p in s.get("owns", [])]) for s in manifest["slices"]]
    by_slice: dict[str, list[str]] = {}
    unowned = []
    for name in changed_files():
        if name in skip or any(name.startswith(prefix) for prefix in ignore):
            continue
        hit = [sid for sid, pats in owners if any(p.match(name) for p in pats)]
        if hit:
            for sid in hit:
                by_slice.setdefault(sid, []).append(name)
        else:
            unowned.append(name)
    return emit({"ok": not unowned, "unowned": unowned, "by_slice": by_slice})


# ---------------------------------------------------------------- size

def line_count(path: Path) -> int:
    try:
        with path.open("rb") as handle:
            data = handle.read()
    except OSError:
        return 0
    if b"\0" in data[:8000]:
        return 0  # binary: no lines to review
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def size(path: Path, run_dir: Path, factor: float) -> int:
    manifest, err = read_manifest(path.read_text(encoding="utf-8"))
    if err:
        return emit({"ok": False, "errors": [err]})
    root = repo_root()
    base_file = run_dir / "base.txt"
    if not base_file.exists():
        return emit({"ok": False, "errors": [f"{base_file} is missing: run baseline first"]})
    base = base_file.read_text().strip()
    dirty_file = run_dir / "baseline-dirty.txt"
    skip = {l.strip() for l in dirty_file.read_text().splitlines() if l.strip()} \
        if dirty_file.exists() else set()
    prefix = repo_prefix(run_dir)
    numstat = git("diff", "--numstat", "-z", base)
    if numstat.returncode != 0:
        raise GitError(numstat.stderr.strip() or f"git diff {base} failed")
    lines: dict[str, int] = {}
    parts, i = numstat.stdout.split("\0"), 0
    while i < len(parts):
        entry = parts[i]
        if not entry:
            i += 1
            continue
        added, deleted, name = (entry.split("\t", 2) + ["", "", ""])[:3]
        if not name:  # a rename: the next two fields are the old and the new path
            name = parts[i + 2] if i + 2 < len(parts) else ""
            i += 2
        i += 1
        if added.isdigit() and deleted.isdigit():
            lines[name] = int(added) + int(deleted)
    untracked = git("-C", str(root), "ls-files", "--others", "--exclude-standard", "-z")
    for name in filter(None, untracked.stdout.split("\0")):
        lines.setdefault(name, line_count(root / name))
    owners = [(s["id"], [glob_regex(p) for p in s.get("owns", [])]) for s in manifest["slices"]]
    by_slice = {s["id"]: {"lines": 0, "max_lines": s.get("max_lines"), "files": 0}
                for s in manifest["slices"]}
    for name, count in lines.items():
        if name in skip or (prefix and name.startswith(prefix)):
            continue
        for sid, pats in owners:
            if any(p.match(name) for p in pats):
                by_slice[sid]["lines"] += count
                by_slice[sid]["files"] += 1
    over = []
    for sid, row in by_slice.items():
        budget = row["max_lines"]
        if isinstance(budget, int) and budget > 0:
            row["ratio"] = round(row["lines"] / budget, 2)
            if row["lines"] > budget * factor:
                over.append(f"{sid}: {row['lines']} changed lines, budget {budget} "
                            f"({row['ratio']} x): review it in parts or split it next time")
    return emit({"ok": True, "base": base, "factor": factor, "by_slice": by_slice, "over": over})


# ---------------------------------------------------------------- emit / baseline

def emit(payload: dict) -> int:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("ok") else 1


def baseline(path: Path, run_dir: Path) -> int:
    manifest, err = read_manifest(path.read_text(encoding="utf-8"))
    if err:
        return emit({"ok": False, "errors": [err]})
    repo_root()  # fail early, with a clear message, outside a repository
    run_dir.mkdir(parents=True, exist_ok=True)
    base_file, dirty_file = run_dir / "base.txt", run_dir / "baseline-dirty.txt"
    created = not base_file.exists()
    if created:
        head = git("rev-parse", "HEAD")
        if head.returncode != 0:
            raise GitError(head.stderr.strip() or "git rev-parse HEAD failed")
        head = head.stdout.strip()
        prefix = repo_prefix(run_dir)  # None when the run folder lies outside the repository
        dirty = [f for f in changed_files() if not (prefix and f.startswith(prefix))]
        base_file.write_text(head + "\n", encoding="utf-8")
        dirty_file.write_text("".join(f + "\n" for f in dirty), encoding="utf-8")
    dirty = [line for line in dirty_file.read_text().splitlines() if line] \
        if dirty_file.exists() else []
    owners = [(s["id"], [glob_regex(p) for p in s.get("owns", [])]) for s in manifest["slices"]]
    at_risk = {f: [sid for sid, pats in owners if any(p.match(f) for p in pats)] for f in dirty}
    at_risk = {f: sids for f, sids in at_risk.items() if sids}
    return emit({
        "ok": True,
        "created": created,
        "run_dir": str(run_dir.resolve()),
        "base": base_file.read_text().strip(),
        "dirty_before_start": dirty,
        "dirty_under_owned_paths": at_risk,
    })


# ---------------------------------------------------------------- branch

def default_branch() -> str | None:
    """origin's HEAD if known, else init.defaultBranch, main or master, whichever exists."""
    ref = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if ref.returncode == 0 and "/" in ref.stdout.strip():
        return ref.stdout.strip().split("/", 1)[1]
    configured = git("config", "--get", "init.defaultBranch").stdout.strip()
    for name in [configured, "main", "master"]:
        if name and git("show-ref", "--verify", "--quiet", f"refs/heads/{name}").returncode == 0:
            return name
    return None


def branch(path: Path, name: str | None) -> int:
    manifest, err = read_manifest(path.read_text(encoding="utf-8"))
    if err:
        return emit({"ok": False, "errors": [err]})
    repo_root()  # fail early, with a clear message, outside a repository
    target = name or f"dev-kit/{manifest.get('slug') or path.resolve().parent.name}"
    valid = git("check-ref-format", "--branch", target)
    if valid.returncode != 0:
        return emit({"ok": False, "errors": [f"'{target}' is not a valid branch name"]})
    current = git("symbolic-ref", "--quiet", "--short", "HEAD").stdout.strip() or None
    default = default_branch()
    result = {"default": default, "was": current or "(detached HEAD)"}
    if current is not None and current != default:
        return emit({"ok": True, **result, "branch": current, "action": "stayed",
                     "reason": "already on a branch other than the default"})
    exists = git("show-ref", "--verify", "--quiet", f"refs/heads/{target}").returncode == 0
    switch = git("switch", target) if exists else git("switch", "-c", target)
    if switch.returncode != 0:
        return emit({"ok": False, **result, "branch": target,
                     "errors": [switch.stderr.strip() or f"git switch {target} failed"]})
    return emit({"ok": True, **result, "branch": target,
                 "action": "switched" if exists else "created",
                 "reason": "was on the default branch" if current else "was on a detached HEAD"})


# ---------------------------------------------------------------- main

def main(argv: list[str]) -> int:
    try:
        return run(argv)
    except GitError as exc:
        return emit({"ok": False, "errors": [str(exc)]})


def run(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in {"check", "ownership", "approve", "baseline", "branch",
                                        "size"}:
        print(__doc__)
        return 2
    command, plan = argv[0], Path(argv[1])
    if not plan.exists():
        return emit({"ok": False, "errors": [f"{plan} does not exist"]})
    if command == "check":
        return check(plan)
    if command == "branch":
        rest = argv[2:]
        if rest and (rest[0] != "--name" or len(rest) != 2):
            print(__doc__)
            return 2
        return branch(plan, rest[1] if rest else None)
    if command == "size":
        rest = argv[2:]
        if not rest:
            print(__doc__)
            return 2
        factor = SIZE_FACTOR
        if len(rest) == 3 and rest[1] == "--factor":
            try:
                factor = float(rest[2])
            except ValueError:
                print(__doc__)
                return 2
        elif len(rest) != 1:
            print(__doc__)
            return 2
        return size(plan, Path(rest[0]), factor)
    if command == "baseline":
        if len(argv) < 3:
            print(__doc__)
            return 2
        return baseline(plan, Path(argv[2]))
    if command == "approve":
        text = plan.read_text(encoding="utf-8")
        manifest, err = read_manifest(text)
        if err:
            return emit({"ok": False, "errors": [err]})
        manifest["approved"] = True
        write_manifest(plan, text, manifest)
        return emit({"ok": True, "approved": True})
    baseline_file, ignore, rest = None, [], argv[2:]
    while rest:
        flag = rest.pop(0)
        if flag == "--baseline" and rest:
            baseline_file = Path(rest.pop(0))
        elif flag == "--ignore" and rest:
            ignore.append(rest.pop(0))
    return ownership(plan, baseline_file, ignore)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
