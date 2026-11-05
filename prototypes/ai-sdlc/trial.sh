#!/usr/bin/env bash
# AI-SDLC prototype trial: approach plugins-ci, project type web-app.
#
# Runs the dev-kit pipeline (plan -> implement -> review) headless with `claude -p` on a fresh
# --no-hardlinks clone of a sibling repo, under a hard spend cap, and writes trial-result.json.
#
#   bash prototypes/ai-sdlc/trial.sh                    # real run (spends usage, cap USD 5)
#   TRIAL_DRY_RUN=1 bash prototypes/ai-sdlc/trial.sh    # plumbing only, no `claude` calls
#
# Run from the repo root. Never writes to the sibling repo: it only uses `git -C <sibling>`
# (read-only, optional locks off) and `git clone`. Compatible with macOS bash 3.2.
set -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
SIBLING="${SIBLING:-/Users/adrienlamoureux/Documents/code/whisk-proto-gcp}"
REPO_NAME="$(basename "$SIBLING")"
TRIAL="$ROOT/.campaign-kit/ai-sdlc-approaches/trial"
CLONE="$TRIAL/$REPO_NAME"
LOGS="$TRIAL/logs"
RESULT="$TRIAL/trial-result.json"
PLUGIN="$ROOT/plugins/dev-kit"
PLAN_TOOL="$PLUGIN/skills/plan/scripts/plan_tool.py"
TICKET_FILE="$HERE/ticket.md"
SLUG="retry-hint"
RUN_DIR=".dev-kit/$SLUG"                       # inside the clone (plan_tool requires it)
DRY="${TRIAL_DRY_RUN:-0}"

# Per-phase spend caps (USD). They sum to 4.8, under the USD 5 contract cap.
BUDGET_PLAN=1.4
BUDGET_IMPLEMENT=1.6
BUDGET_REVIEW=1.8

[ -f "$TICKET_FILE" ] || { echo "missing $TICKET_FILE" >&2; exit 2; }

git_ro() { GIT_OPTIONAL_LOCKS=0 git -C "$SIBLING" "$@"; }
sib_snapshot() { printf '%s %s\n' "$(git_ro rev-parse HEAD)" "$(git_ro status --porcelain | shasum | cut -d' ' -f1)"; }

# fresh logs dir (the trial folder lives in the gitignored run folder)
rm -rf "${LOGS:?}"
mkdir -p "$LOGS"
rm -f "${RESULT:?}"

SIB_BEFORE="$(sib_snapshot)" || { echo "cannot read sibling $SIBLING" >&2; exit 2; }

# ---- state ---------------------------------------------------------------------------------
COST_plan=0; COST_implement=0; COST_review=0
EXIT_plan=-1; EXIT_implement=-1; EXIT_review=-1
DEN_plan=0; DEN_implement=0; DEN_review=0
ERR_plan=""; ERR_implement=""; ERR_review=""
PHASES_RUN=()
NOTES=()
START_SHA=""
CHANGED=0
GATE_EXIT=-1
REVIEW_VERDICT=""
SIB_UNCHANGED=false
ABORT_REASON=""

write_result() {  # write_result <true|false>
  PHASES_RUN_STR="${PHASES_RUN[*]:-}" NOTES_STR="$(printf '%s\n' "${NOTES[@]:-}")" \
  P_COST_plan="$COST_plan" P_COST_implement="$COST_implement" P_COST_review="$COST_review" \
  P_EXIT_plan="$EXIT_plan" P_EXIT_implement="$EXIT_implement" P_EXIT_review="$EXIT_review" \
  P_DEN_plan="$DEN_plan" P_DEN_implement="$DEN_implement" P_DEN_review="$DEN_review" \
  OK="$1" DRY="$DRY" REPO="$REPO_NAME" START_SHA="$START_SHA" CHANGED="$CHANGED" GATE_EXIT="$GATE_EXIT" \
  REVIEW_VERDICT="$REVIEW_VERDICT" SIB_UNCHANGED="$SIB_UNCHANGED" ABORT_REASON="$ABORT_REASON" \
  TICKET_FILE="$TICKET_FILE" RESULT="$RESULT" python3 -I - <<'PY'
import json, os
e = os.environ
phases = ["plan", "implement", "review"]
costs = {p: float(e["P_COST_" + p]) for p in phases}
title = open(e["TICKET_FILE"], encoding="utf-8").readline().lstrip("# ").strip()
out = {
    "approach": "plugins-ci",
    "project_type": "web-app",
    "repo": e["REPO"],
    "ticket": title,
    "phases_run": e["PHASES_RUN_STR"].split(),
    "changed_files": int(e["CHANGED"]),
    "cost_usd": round(sum(costs.values()), 4),
    "ok": e["OK"] == "true",
    "phase_costs": costs,
    "phase_exit": {p: int(e["P_EXIT_" + p]) for p in phases},
    "permission_denials": {p: int(e["P_DEN_" + p]) for p in phases},
    "sibling_unchanged": e["SIB_UNCHANGED"] == "true",
    "gate_exit": int(e["GATE_EXIT"]),
    "review_verdict": e["REVIEW_VERDICT"],
    "start_sha": e["START_SHA"],
    "dry_run": e["DRY"] == "1",
    "abort_reason": e["ABORT_REASON"],
    "notes": [n for n in e["NOTES_STR"].split("\n") if n],
}
with open(e["RESULT"], "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)
print(json.dumps(out, indent=2))
PY
}

finish() {  # finish <true|false>   exit 0 only when ok is true (dry run: exit 0 if plumbing worked)
  local ok="$1" sib_after
  sib_after="$(sib_snapshot)"
  if [ "$SIB_BEFORE" = "$sib_after" ]; then
    SIB_UNCHANGED=true
  else
    SIB_UNCHANGED=false; NOTES+=("sibling HEAD/status changed during trial"); ok=false
  fi
  write_result "$ok"
  [ "$ok" = true ] && exit 0
  [ "$DRY" = "1" ] && [ -z "$ABORT_REASON" ] && [ "$SIB_UNCHANGED" = true ] && exit 0
  exit 1
}

# ---- 1-2. fresh clone ----------------------------------------------------------------------
rm -rf "${CLONE:?}"
if ! git clone --quiet --no-hardlinks "$SIBLING" "$CLONE" 2>"$LOGS/clone.stderr"; then
  ABORT_REASON="git clone failed"; finish false
fi
START_SHA="$(git -C "$CLONE" rev-parse HEAD)"

# ---- 3. safety check: `claude -p` runs a repo's hooks and .mcp.json with no trust prompt -----
UNSAFE=""
[ -e "$CLONE/.mcp.json" ] && UNSAFE="$UNSAFE .mcp.json"
for f in "$CLONE"/.claude/settings*.json; do [ -e "$f" ] && UNSAFE="$UNSAFE ${f#"$CLONE"/}"; done
[ -e "$CLONE/.claude/hooks" ] && UNSAFE="$UNSAFE .claude/hooks"
if [ -n "$UNSAFE" ]; then
  ABORT_REASON="clone contains files claude -p would run without a trust prompt:$UNSAFE"
  finish false
fi
NOTES+=("safety check passed: no .mcp.json, .claude/settings*.json or .claude/hooks in the clone")

# ---- helpers for the headless phases -------------------------------------------------------
GIT_RO_TOOLS="Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git rev-parse:*),Bash(git ls-files:*),Bash(git show:*),Bash(ls:*),Bash(cat:*)"
PLAN_TOOL_RULE="Bash(python3 $PLAN_TOOL:*)"
AGENT_TOOLS="Read,Grep,Glob,Task,Agent,Skill"

run_phase() {  # run_phase <name> <budget> <allowedTools> <prompt>; returns 0 when the phase passed
  local name="$1" budget="$2" tools="$3" prompt="$4" rc cost iserr den
  if [ "$DRY" = "1" ]; then NOTES+=("dry run: skipped claude phase $name"); return 0; fi
  ( cd "$CLONE" && PYTHONDONTWRITEBYTECODE=1 claude -p "$prompt" \
      --plugin-dir "$PLUGIN" --setting-sources project,local --model sonnet \
      --strict-mcp-config --output-format json --no-session-persistence \
      --max-budget-usd "$budget" --permission-mode dontAsk \
      --allowedTools "$tools" </dev/null >"$LOGS/$name.json" 2>"$LOGS/$name.stderr" )
  rc=$?
  read -r cost iserr den < <(python3 -I - "$LOGS/$name.json" <<'PY'
import json, sys
try:
    r = json.load(open(sys.argv[1]))
    if isinstance(r, list):  # array output: take the final result object
        r = next(x for x in reversed(r) if x.get("type") == "result")
    print(r.get("total_cost_usd", 0) or 0, "true" if r.get("is_error") else "false", len(r.get("permission_denials") or []))
except Exception:
    print(0, "true", 0)
PY
)
  printf -v "COST_$name" '%s' "$cost"; printf -v "EXIT_$name" '%s' "$rc"
  printf -v "DEN_$name" '%s' "$den"; printf -v "ERR_$name" '%s' "$iserr"
  if [ "$rc" -eq 0 ] && [ "$iserr" = "false" ]; then PHASES_RUN+=("$name"); return 0; fi
  NOTES+=("phase $name failed (exit $rc, is_error=$iserr); see logs/$name.json")
  return 1
}

TICKET_TEXT="$(cat "$TICKET_FILE")"

# ---- 4a. plan ------------------------------------------------------------------------------
PLAN_PROMPT="/dev-kit:plan $TICKET_TEXT

size=S DIR=$RUN_DIR
Headless run: nobody can answer questions, so use the defaults and do not ask. Stop after step 5 (present); do not run the approve step."
run_phase plan "$BUDGET_PLAN" "$AGENT_TOOLS,Write(.dev-kit/**),Edit(.dev-kit/**),$GIT_RO_TOOLS,$PLAN_TOOL_RULE" "$PLAN_PROMPT"
PLAN_RC=$?

# Scripted stand-in for the human approval gate (in real use the developer approves the plan).
if [ "$DRY" != "1" ] && [ "$PLAN_RC" -eq 0 ]; then
  if python3 "$PLAN_TOOL" check "$CLONE/$RUN_DIR/plan.md" >"$LOGS/plan-check.json" 2>&1; then
    python3 "$PLAN_TOOL" approve "$CLONE/$RUN_DIR/plan.md" >"$LOGS/plan-approve.json" 2>&1
    NOTES+=("plan.md passed plan_tool check; approval gate simulated by trial.sh (plan_tool approve)")
  else
    NOTES+=("plan.md missing or failed plan_tool check; see logs/plan-check.json"); PLAN_RC=1
  fi
fi

# ---- 4b. implement -------------------------------------------------------------------------
IMPL_RC=1
if [ "$DRY" = "1" ] || [ "$PLAN_RC" -eq 0 ]; then
  IMPL_PROMPT="/dev-kit:implement $SLUG
Headless run: nobody can answer questions, so use the defaults. The plan is already approved. Do not commit or push."
  IMPL_TOOLS="$AGENT_TOOLS,Write(backend/**),Edit(backend/**),Write(.dev-kit/**),Edit(.dev-kit/**),$GIT_RO_TOOLS,Bash(git switch:*),Bash(git checkout -b:*),Bash(mkdir:*),Bash(python3 -m unittest:*),Bash(python3 -m pytest:*),$PLAN_TOOL_RULE"
  run_phase implement "$BUDGET_IMPLEMENT" "$IMPL_TOOLS" "$IMPL_PROMPT"; IMPL_RC=$?
else
  NOTES+=("implement skipped: plan phase did not pass")
fi

# ---- 4c. review ----------------------------------------------------------------------------
REV_RC=1
if [ "$DRY" = "1" ] || [ "$IMPL_RC" -eq 0 ]; then
  REV_PROMPT="/dev-kit:review $SLUG effort=medium
Headless run: nobody can answer questions, so use the defaults. Do not edit source files; only write under $RUN_DIR."
  REV_TOOLS="$AGENT_TOOLS,Write(.dev-kit/**),Edit(.dev-kit/**),$GIT_RO_TOOLS,Bash(python3 -m unittest:*),Bash(python3 -m pytest:*),$PLAN_TOOL_RULE"
  run_phase review "$BUDGET_REVIEW" "$REV_TOOLS" "$REV_PROMPT"; REV_RC=$?
else
  NOTES+=("review skipped: implement phase did not pass")
fi

# ---- 5. measure ----------------------------------------------------------------------------
{ git -C "$CLONE" diff --name-only "$START_SHA"; git -C "$CLONE" ls-files --others --exclude-standard; } \
  | sort -u | grep -vE '^(\.dev-kit/|.*__pycache__/)' | grep -v '^$' > "$LOGS/changed-files.txt"
CHANGED="$(wc -l < "$LOGS/changed-files.txt" | tr -d ' ')"

if [ "$DRY" != "1" ]; then
  # independent gate: the ticket's own test command, run by this script, not by the agents
  ( cd "$CLONE" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s backend/tests -t backend -p test_retry_hint.py -v >"$LOGS/gate.txt" 2>&1 )
  GATE_EXIT=$?
  if [ -f "$CLONE/$RUN_DIR/review.md" ]; then
    REVIEW_VERDICT="$(grep -m1 -oE 'approve|changes-required|blocked' "$CLONE/$RUN_DIR/review.md")"
  fi
  cp -R "$CLONE/.dev-kit" "$LOGS/dev-kit-run" 2>/dev/null
fi

# ---- 6-7. verdict --------------------------------------------------------------------------
if [ "$DRY" = "1" ]; then
  NOTES+=("dry run: plumbing only, ok is false by design")
  finish false
fi

OK=true
{ [ "$PLAN_RC" -eq 0 ] && [ "$IMPL_RC" -eq 0 ] && [ "$REV_RC" -eq 0 ]; } || { OK=false; NOTES+=("a phase failed"); }
[ "$CHANGED" -ge 1 ] || { OK=false; NOTES+=("no changed files"); }
python3 -I -c "import sys;sys.exit(0 if sum(map(float,sys.argv[1:]))<=5 else 1)" "$COST_plan" "$COST_implement" "$COST_review" \
  || { OK=false; NOTES+=("cost over USD 5"); }
[ "$GATE_EXIT" -eq 0 ] || { OK=false; NOTES+=("independent gate failed (see logs/gate.txt)"); }
[ -f "$CLONE/$RUN_DIR/review.md" ] || { OK=false; NOTES+=("review.md missing"); }
finish "$OK"
