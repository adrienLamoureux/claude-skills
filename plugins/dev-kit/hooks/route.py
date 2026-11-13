#!/usr/bin/env python3
"""Kit routing hook: one routing decision per coding task, without a slash command.

Each typed prompt gets at most one route; no route means "edit directly":

  route         owner           when the prompt reads as               behaviour (mode "gate")
  plan          dev-kit         a build that spans two or more areas   starts on its own: repo edits
                                                                       are held until a plan is
                                                                       approved or the user says
                                                                       "just edit it"
  investigate   dev-kit         a bug or unexplained behaviour         starts on its own: edits are
                                                                       held until dev-kit:investigate
                                                                       has run or the user says
                                                                       "just fix it"
  campaign      campaign-kit    an objective measured over rounds      proposed, never started: edits
                                                                       wait for the user's answer
                                                                       for the rest of the turn

One script, shipped as an identical copy in each kit; `--kit` says which routes a copy owns.
Events (see hooks/hooks.json):
  UserPromptSubmit   Classifies the prompt, records the route for the task, adds a short note
                     (additionalContext). Never blocks a prompt. Task notes and messages from
                     other sessions (prompts that start with "<") change nothing, so only the
                     user's own words can lift a hold.
  PreToolUse Edit|   Holds edits as in the table. dev-kit also tracks the areas this task has
    Write|...        edited: a direct edit that reaches a second area with no approved
                     .dev-kit/*/plan.md is held the same way (it catches follow-ups such as
                     "do the same for the others" that carry no keywords).
  PreToolUse Agent   dev-kit: holds, once per session, handing a multi-area build to a non-kit
                     subagent (a subagent cannot get the user's approval for a plan).

Never held: edits by dev-kit:* and campaign-kit:* agents, files under .dev-kit/ and
.campaign-kit/, files outside the repo. A held edit is denied with a reason that names the
skill to call; Claude reads it.

Mode, first match wins: env <KIT>_ROUTING (DEV_KIT_ROUTING, CAMPAIGN_KIT_ROUTING), env
KIT_ROUTING (all kits), the plugin option CLAUDE_PLUGIN_OPTION_ROUTING (userConfig "routing"),
then "gate". Values: off (nothing) | nudge (notes only, never blocks) | gate.

Standard library only. Any error exits 0 with no output, so the hook fails open.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

MODES = ("off", "nudge", "gate")
DEFAULT_MODE = "gate"
SPREAD_SCOPE = "task"  # area tracking restarts at each typed prompt ("task") or never ("session")
KIT_ROUTES = {"dev-kit": {"plan", "investigate"}, "campaign-kit": {"campaign"}}
EXEMPT_AGENT_PREFIXES = ("dev-kit:", "campaign-kit:")
READ_ONLY_AGENTS = {"explore", "plan", "web-fetch", "claude-code-guide", "statusline-setup"}
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
AGENT_TOOLS = {"Agent", "Task"}

# --- shared patterns -----------------------------------------------------------------------

BUILD_VERBS = re.compile(
    r"\b(implement|build(?! and (?:deploy|run|test|ship))|add|adding|create|write|make(?! sure)|"
    r"introduce|wire|integrate|support|"
    r"ship|refactor|migrate|port|rewrite|extend|set up|scaffold|develop|convert|replace|expose|"
    r"enable|let users|hook up|plumb)\b",
    re.I,
)
# Each group is one "area" a request can touch. Ambiguous words (view, model, service, page,
# table, route, settings, app) are left out on purpose: they cause one-area false positives.
AREA_LEXICON = {
    "backend": r"back-?end|server(?:-side)?|api|endpoints?|handlers?|controllers?|middleware|"
               r"express|django|flask|fastapi|rails|graphql|(?:get|post|put|patch|delete) /\S*",
    "frontend": r"front-?end|ui|react|vue|svelte|angular|components?|forms?(?! of)|screens?|"
                r"css|buttons?|modals?|client-side",
    "data": r"database|db|schema|migrations?|sql|postgres|mysql|sqlite|mongo(?:db)?|redis",
    "config": r"configurable|config(?:uration)? (?:file|option|value)s?|per[- ]environment|"
              r"env(?:ironment)? var(?:iable)?s?|feature flags?|\.env\b",
    "infra": r"ci|pipelines?|github actions?|workflows? file|docker(?:file)?|deploy(?:ment)?|"
             r"terraform|kubernetes|k8s|helm",
    "docs": r"docs|documentation|readme|changelog|guides?|onboarding doc",
    "cli": r"cli|command[- ]line|subcommands?|--[a-z][\w-]+ flag",
    "mobile": r"ios|android|swiftui|kotlin|mobile app",
}
AREA_RES = {name: re.compile(rf"(?<![\w-])(?:{pat})(?![\w-])", re.I)
            for name, pat in AREA_LEXICON.items()}
PATH_RE = re.compile(r"(?<![\w/.-])((?:[\w.-]+/)+[\w.-]*|[\w-]+\.[a-z]{1,5})(?![\w/])")
ENUM_RE = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+(\S.*)$", re.M)  # list items, text captured
ALL_OF_RE = re.compile(r"\b(all|each|every one) of (?:these|them|the (?:options|items|tickets|changes))\b"
                       r"|\ball the (?:options|changes|items)\b", re.I)
QUESTION_START = re.compile(
    r"^\s*(what|why|where|when|who|which|whose|explain|describe|tell me|show me|list|"
    r"how (?:do|does|did|can|could|should|would|is|are) (?:i|we|you|it|this|that|the)|"
    r"should (?:we|i)|would it|is there|are there|do we|does (?:it|this|the))\b",
    re.I,
)
BUG_WORDS = re.compile(r"\b(bugs?|error|errors|exception|crash(?:es|ed|ing)?|fails?|failed|failing|"
                       r"broken|breaks|regression|flaky|stack ?trace|traceback|doesn'?t work|"
                       r"not working|stopped working|\w+(?:Error|Exception))\b", re.I)
SYMPTOMS = re.compile(r"\b(wrong|(?:shows?|returns?|renders?|prints?|gets?|displays?)\b[^.?!\n]{0,40}"
                      r"\binstead of|unexpected(?:ly)?|never|always|stuck|hangs?|hanging|"
                      r"freez\w*|slow(?:er|s down)?|missing|empty|undefined|null|NaN|blank|twice|"
                      r"duplicated?|leak\w*|times? out|timeout|stops?|stopped|doesn'?t|does not|"
                      r"won'?t|isn'?t|can'?t|cannot|no longer|anymore|[45]\d\d)\b", re.I)
DIAG_ASK = re.compile(r"\b(why|what(?:'s| is) (?:wrong|going on|causing)|what causes|how come|"
                      r"figure out|find out|look into|investigate|debug|diagnose|root cause|"
                      r"track down)\b", re.I)
FIX_ASK = re.compile(r"\b(fix|repair|resolve|solve)\b", re.I)
COMMAND_OPENING = re.compile(
    r"^\W*(?:please\s+|can you\s+|could you\s+)?(run|show|list|tell|summari[sz]e|describe|document|"
    r"write|draft|review|commit|push|open|create|add|implement|build|make|update|rename|bump|"
    r"refactor|explain how)\b", re.I)
CAMPAIGN_GOAL = re.compile(
    r"\b(?:raise|increase|improve|get|bring|push|boost|lift)\b[^.?!\n]{0,40}\bcoverage\b"
    r"|\bcoverage\b[^.?!\n]{0,20}\b(?:to|above|over|at least)\s*\d"
    r"|\b(?:cut|reduce|lower|decrease|shrink|halve|bring down|get down|trim|get|keep)\b[^.?!\n]{0,40}"
    r"\b(?:latency|p\d{2}|response times?|load times?|build times?|bundle(?: size)?|memory(?: use)?|"
    r"costs?|spend|token (?:use|usage|cost)|error rate|flak(?:y|iness)|cold starts?|ci time|run ?time)\b"
    r"|\b(?:migrate|move|convert|port|switch)\b[^.?!\n]{0,30}\b(?:all|every|each|the remaining|the rest of the)\b"
    r"[^.?!\n]{0,40}\b(?:call sites?|usages?|callers|files|endpoints|components|modules|tests|services|packages|pages)\b"
    r"|\b(?:clear|burn down|work through|get through|close out)\b[^.?!\n]{0,20}"
    r"\b(?:backlog|issues|tickets|todos|lint (?:errors|warnings)|warnings)\b"
    r"|\b(?:fix|resolve|eliminate|remove|get rid of)\s+(?:all|every)\b[^.?!\n]{0,30}"
    r"\b(?:lint|type|typescript|tsc|mypy|eslint|flake8|ruff|deprecation|compiler)\b[^.?!\n]{0,10}\b(?:errors|warnings|issues)\b"
    r"|\bresearch\b[^.?!\n]{0,20}\b(?:and|then)\s+prototype\b", re.I)
CAMPAIGN_MEASURE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:%|ms\b|s\b|sec\b|seconds\b|kb\b|mb\b|x\b|percent\b)|\b(?:below|under|above|"
    r"at least|at most|by half|until|rounds?|iterat\w*|every|all|remaining|each|options|zero)\b", re.I)
HOW_TO = re.compile(r"^\s*(?:how|what|why|which|should|is|are|can i|could i)\b", re.I)
# The user already chose: edit directly (lifts any hold), or a kit command named.
DIRECT_OPT_OUT = re.compile(
    r"(\bno plan\b|\bwithout (?:a )?plan(?:ning)?\b|\bdon'?t plan\b|\bskip (?:the )?(?:plan(?:ning)?|kit|dev-?kit|investigation)\b|"
    r"\b(?:edit|change|do|fix|write) (?:it |this |them )?directly\b|\bjust (?:edit|change|fix|rename)\b|"
    r"\bno (?:dev-?kit|campaign|investigation)\b|\bdon'?t (?:use|run|start) (?:the )?(?:dev|campaign)-?kit\b)", re.I)
KIT_NAMED = re.compile(r"(/dev-kit:|\bdev-kit:(?:plan|implement|review|investigate)\b|"
                       r"\b(?:with|through|via|use|using|run) (?:the )?(?:dev|campaign)-?kit\b|/campaign|"
                       r"\bcampaign-kit:|/goal\b)", re.I)
PASTE_TAG = re.compile(r"^</?pasted_content[^>]*>\s*$", re.M)
PASTE_BLOCK = re.compile(r"<pasted_content[^>]*>.*?</pasted_content[^>]*>", re.S)
# The ask is a review or an analysis, not a build, when one of these opens the prompt.
NON_BUILD_OPENING = re.compile(
    r"^\W*(?:\w+\W+){0,6}?(review|audit|assess|evaluate|critique|verify|check|analy[sz]e|"
    r"summari[sz]e|compare|explain|investigate|look into|help me)\b", re.I)
REVIEW_OPENING = re.compile(r"^\W*(?:\w+\W+){0,6}?(review|audit|assess|evaluate|critique|"
                            r"summari[sz]e|compare|put .{0,30} in perspective)\b", re.I)
SYNTHETIC = ("This session is being continued from a previous conversation",)
SOFT_AREAS = {"docs", "cli", "config"}  # layers that usually live inside one named area


def _verb_zone(prompt: str) -> str:
    """The user's own words (pasted blocks removed), first and last 30 words: where the ask is."""
    own = PASTE_BLOCK.sub(" ", prompt or "").split()
    return " ".join(own[:30] + own[-30:]) if len(own) > 60 else " ".join(own)


ENVELOPE_WHYS = {"envelope (task note, session message)", "compaction summary"}


def _none(why: str, optout: bool = False) -> dict:
    return {"route": None, "fire": False, "areas": [], "signal": "", "why": why, "optout": optout}


def _hit(route: str, why: str, areas: list[str] | None = None, signal: str = "") -> dict:
    return {"route": route, "fire": True, "areas": areas or [], "signal": signal, "why": why,
            "optout": False}


# --- classifier ----------------------------------------------------------------------------

def classify_prompt(prompt: str, repo_areas: dict[str, str] | None = None,
                    root: Path | None = None) -> dict:
    """Pick at most one route: {"route": "plan"|"investigate"|"campaign"|None, ...}."""
    text = PASTE_TAG.sub("", prompt or "").strip()
    if not text:
        return _none("empty")
    if text.startswith("/"):
        return _none("slash command")
    if text.startswith("<"):
        return _none("envelope (task note, session message)")
    if text.startswith(SYNTHETIC):
        return _none("compaction summary")
    if DIRECT_OPT_OUT.search(text):
        return _none("user asked to edit directly", optout=True)
    if len(text.split()) < 6:
        return _none("too short")
    if KIT_NAMED.search(text):
        return _none("kit already named")
    zone = _verb_zone(prompt)

    # campaign: an objective with a measure (a number, "until", "all ...") and not a how-to question
    goal = CAMPAIGN_GOAL.search(zone)
    if goal and CAMPAIGN_MEASURE.search(zone) and not HOW_TO.search(text):
        return _hit("campaign", "objective measured over rounds", signal=goal.group(0)[:60])

    # investigate: a bug or unexplained behaviour, asked about or reported (not a build that
    # merely mentions errors, and not "run the tests")
    bug, symptom, diag = BUG_WORDS.search(zone), SYMPTOMS.search(zone), DIAG_ASK.search(zone)
    command = COMMAND_OPENING.search(text) or REVIEW_OPENING.search(text)
    if (bug and (diag or FIX_ASK.search(zone) or not command)) or (diag and symptom and not command) \
            or (diag and bug):
        words = sorted({m.group(0).lower() for rx in (BUG_WORDS, SYMPTOMS) for m in rx.finditer(zone)})
        return _hit("investigate", "bug or unexplained behaviour", signal=", ".join(words[:4]))

    # plan: a build request that spans two or more areas
    if NON_BUILD_OPENING.search(text):
        return _none("review or analysis ask")
    if not BUILD_VERBS.search(zone):
        return _none("no build verb in the ask")
    if QUESTION_START.search(text):
        return _none("question")

    areas: set[str] = {name for name, rx in AREA_RES.items() if rx.search(text)}
    path_areas: set[str] = set()
    files_named = 0
    for match in PATH_RE.finditer(text):
        token = match.group(1).strip("./")
        if token.startswith(("http", "www")) or re.fullmatch(r"(?:e\.g|i\.e|etc|vs)", token, re.I):
            continue
        parts = token.split("/")
        has_ext = bool(re.search(r"\.[A-Za-z]{1,5}$", parts[-1]))
        files_named += has_ext
        if len(parts) < 2:
            continue
        # Prose such as "UI/UX" or "API/backend" is not a path: in a repo the first segment
        # must exist on disk; outside one the token needs an extension, a trailing slash or
        # three segments.
        if root is not None:
            if not (root / parts[0]).exists():
                continue
        elif not (has_ext or match.group(1).endswith("/") or len(parts) >= 3):
            continue
        area = _area_of_parts(parts, dirs_only=True)
        if area:
            path_areas.add(area)
    if repo_areas:
        for label, area in repo_areas.items():
            # a bare mention ("the dev-kit README"), not a segment inside a path
            if re.search(rf"(?<![\w/.-]){re.escape(label)}(?![\w/-])", text, re.I):
                path_areas.add(area)
    # Two or more named places are that many areas. With one named place, layer words are
    # read as inside it ("add a --json flag to focus-kit and document it in its README",
    # "add a server check to src/server/auth.js"), unless two hard layers (backend, frontend,
    # data, infra, mobile) say the change spans more than that place.
    hard = areas - SOFT_AREAS
    if len(path_areas) >= 2:
        areas = (areas - {"docs"} if "docs" in path_areas else areas) | path_areas
    elif len(path_areas) == 1:
        areas = hard if len(hard) >= 2 else set(path_areas)

    enum_items = sum(1 for item in ENUM_RE.findall(text) if BUILD_VERBS.match(item))
    if len(areas) >= 2:
        return _hit("plan", "build verb + 2+ areas", sorted(areas))
    if files_named <= 1 and (enum_items >= 3 or ALL_OF_RE.search(text)):
        return _hit("plan", "build verb + list of changes", sorted(areas) or ["several items"])
    return _none("one area or none")


# --- repo areas ---------------------------------------------------------------------------

CONTAINER_DIRS = {"plugins", "packages", "apps", "services", "libs", "modules", "crates", "src"}
IGNORED_DIRS = {".git", ".dev-kit", ".campaign-kit", "node_modules", ".venv", "venv", "dist",
                "build", "__pycache__", "test", "tests", "__tests__", "spec", "specs"}
TEST_FILE = re.compile(r"(^test_.*\.py$|_test\.\w+$|\.test\.\w+$|\.spec\.\w+$)")


def _area_of_parts(parts: list[str], dirs_only: bool = False) -> str | None:
    parts = [p for p in parts if p not in ("", ".")]
    if not parts:
        return None
    if any(p in IGNORED_DIRS for p in parts[:-1]) or TEST_FILE.search(parts[-1]):
        return None
    if dirs_only and len(parts) == 1:
        return parts[0]
    if len(parts) == 1:
        return None  # root-level file (README.md, package.json): no area
    if parts[0] in CONTAINER_DIRS and len(parts) > 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def find_root(cwd: str) -> Path | None:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    start = Path(env or cwd or ".").resolve()
    for p in (start, *start.parents):
        if (p / ".git").exists():
            return p
    return start if env else None


def area_of_file(file_path: str, root: Path) -> str | None:
    try:
        rel = Path(file_path).resolve().relative_to(root)
    except (ValueError, OSError):
        return None  # outside the repo (scratchpad, /tmp, ~/.claude)
    return _area_of_parts(list(rel.parts))


def _identifier_like(name: str) -> bool:
    # "dev-kit", "resume_forge", "api2" yes; "docs", "ideas", "better" no: plain words in
    # prose would otherwise count as areas.
    return len(name) >= 5 and bool(re.search(r"[-_\d]", name)) and not name.startswith(".")


def list_repo_areas(root: Path) -> dict[str, str]:
    """Map a name a prompt might use (dir basename) to its area, e.g. 'dev-kit' -> 'plugins/dev-kit'."""
    out: dict[str, str] = {}
    try:
        for child in root.iterdir():
            if not child.is_dir() or child.name in IGNORED_DIRS or child.name.startswith("."):
                continue
            if child.name in CONTAINER_DIRS:
                for sub in child.iterdir():
                    if sub.is_dir() and _identifier_like(sub.name):
                        out[sub.name] = f"{child.name}/{sub.name}"
            elif _identifier_like(child.name):
                out[child.name] = child.name
    except OSError:
        pass
    return out


PLAN_ACTIVE_DAYS = 7
FINAL_VERDICT = re.compile(r"^## Verdict\s*\n+\W*(approve|blocked)\b", re.M | re.I)


def approved_plan_exists(root: Path, now: float | None = None) -> bool:
    """True while a dev-kit run is live: an approved plan.md whose run has no final review
    verdict (approve or blocked) and was touched (plan.md or resume.md) in the last 7 days.
    A finished or abandoned run in .dev-kit/ must not lift holds for later, unrelated tasks."""
    now = time.time() if now is None else now
    for plan in (root / ".dev-kit").glob("*/plan.md"):
        run = plan.parent
        try:
            if not re.search(r'"approved"\s*:\s*true', plan.read_text(encoding="utf-8", errors="ignore")):
                continue
            review = run / "review.md"
            if review.exists() and FINAL_VERDICT.search(review.read_text(encoding="utf-8", errors="ignore")):
                continue
            touched = max(p.stat().st_mtime for p in (plan, run / "resume.md") if p.exists())
            if now - touched <= PLAN_ACTIVE_DAYS * 86400:
                return True
        except OSError:
            continue
    return False


# --- state ----------------------------------------------------------------------------------

def new_state() -> dict:
    return {"areas": [], "noted": False, "optout": False, "denied_agent": False,
            "turn": {"route": None, "detail": "", "held": 0}}


def state_path(session_id: str, kit: str) -> Path:
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(tempfile.gettempdir(), "kit-routing")
    safe = re.sub(r"[^\w-]", "_", session_id or "nosession")[:80]
    return Path(base) / "routing" / f"{kit}-{safe}.json"


def load_state(session_id: str, kit: str) -> dict:
    state = new_state()
    try:
        state.update(json.loads(state_path(session_id, kit).read_text()))
    except (OSError, ValueError):
        pass
    return state


def save_state(session_id: str, kit: str, state: dict) -> None:
    path = state_path(session_id, kit)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state))
    except OSError:
        pass


# --- decisions (pure: the hooks and the transcript replay both call these) --------------------

def record_prompt(state: dict, result: dict, kit: str, spread_scope: str = SPREAD_SCOPE) -> dict:
    """Update the task state for one prompt. Envelopes (task notes, other sessions' messages,
    compaction summaries) change nothing, so only the user's own words lift a hold."""
    if result["why"] in ENVELOPE_WHYS:
        return state
    route = result["route"] if result["route"] in KIT_ROUTES.get(kit, set()) else None
    if result.get("optout"):
        state["optout"] = True
    elif route:
        state["optout"] = False  # a new routed task starts with its hold in place
    if spread_scope == "task" or route:
        state["areas"], state["noted"] = [], False
    detail = ", ".join(result["areas"]) or result["signal"]
    state["turn"] = {"route": route, "detail": detail, "held": 0}
    return state


def _repo_relative(file_path: str, root: Path) -> list[str] | None:
    try:
        return list(Path(file_path).resolve().relative_to(root).parts)
    except (ValueError, OSError):
        return None


def decide_edit(state: dict, file_path: str, root: Path, current_mode: str, kit: str,
                plan_ok, agent_type: str = "", in_subagent: bool = False) -> dict | None:
    """Return hookSpecificOutput fields for one Edit/Write, or None to let it through.
    `plan_ok` is a callable so the approved-plan check only reads disk when it matters."""
    if current_mode == "off" or agent_type.startswith(EXEMPT_AGENT_PREFIXES):
        return None
    parts = _repo_relative(file_path, root)
    if not parts or parts[0] in (".dev-kit", ".campaign-kit", ".git"):
        return None
    turn, gate = state["turn"], current_mode == "gate"
    who = ("A subagent cannot get the user's approval, so report back to the main session that "
           "this task needs {skill}." if in_subagent else "{action}")

    if kit == "campaign-kit":
        if gate and turn["route"] == "campaign" and not state["optout"]:
            turn["held"] += 1
            return _deny(
                f"[campaign-kit routing gate] This request reads as an objective measured over "
                f"rounds (\"{turn['detail']}\"). campaign-kit is proposed, never started on its own, "
                f"so edits wait for the user's answer this turn. "
                + who.format(skill="/campaign-kit:campaign",
                             action="Reply with one line proposing /campaign-kit:campaign and why, "
                                    "and let the user choose.")
                + f" {env_name(kit)}=off turns this off.")
        return None

    # dev-kit
    if gate and turn["route"] == "plan" and not state["optout"] and not plan_ok():
        turn["held"] += 1
        return _deny(
            f"[dev-kit routing gate] Repo edits are held for this task: it reads as a change "
            f"across several areas ({turn['detail']}) and no approved .dev-kit plan exists. "
            + who.format(skill="/dev-kit:plan",
                         action="Start the dev-kit:plan skill and say in one line why dev-kit "
                                "started.")
            + " The hold lifts when the plan is approved or the user says to edit directly "
              "(\"just edit it\"). Do not retry this edit." + f" {env_name(kit)}=nudge or off relaxes it.")
    if gate and turn["route"] == "investigate" and not turn.get("investigated") and not state["optout"]:
        turn["held"] += 1
        return _deny(
            f"[dev-kit routing gate] Edits are held for this task: it reads as a bug report "
            f"({turn['detail']}). "
            + who.format(skill="/dev-kit:investigate",
                         action="Start the dev-kit:investigate skill and say in one line why: it "
                                "reproduces the problem read-only and ranks likely causes.")
            + " The hold lifts once dev-kit:investigate has run, or when the user says to fix it "
              "directly (\"just fix it\"). Do not retry this edit."
            + f" {env_name(kit)}=nudge or off relaxes it.")

    area = _area_of_parts(parts)
    if not area or area in state["areas"]:
        return None
    if not state["areas"] or state["optout"] or plan_ok():
        state["areas"].append(area)
        return None
    areas = ", ".join(state["areas"] + [area])
    if gate:
        return _deny(
            f"[dev-kit routing gate] This edit would bring the task's direct edits to a second "
            f"area ({areas}) with no approved .dev-kit plan. "
            + who.format(skill="/dev-kit:plan",
                         action="Start the dev-kit:plan skill and say in one line why dev-kit "
                                "started, or ask the user whether to edit directly.")
            + " The hold lifts when a plan is approved or the user says to edit directly."
            + f" {env_name(kit)}=nudge or off relaxes it.")
    state["areas"].append(area)
    if not state["noted"]:
        state["noted"] = True
        return {"additionalContext": (
            f"[dev-kit routing] This task has now edited files in {len(state['areas'])} areas "
            f"({areas}) without an approved dev-kit plan. dev-kit:plan plans multi-area changes "
            f"for the user's approval. If you continue editing directly, say so in your reply.")}
    return None


def record_skill(state: dict, skill: str) -> dict:
    """A kit skill call can lift a hold: dev-kit:investigate lifts a bug task's hold."""
    if skill.strip().lstrip("/") in ("dev-kit:investigate",):
        state["turn"]["investigated"] = True
    return state


def _deny(reason: str) -> dict:
    return {"permissionDecision": "deny", "permissionDecisionReason": reason}


# --- handlers -------------------------------------------------------------------------------

def env_name(kit: str) -> str:
    return kit.upper().replace("-", "_") + "_ROUTING"


def mode(kit: str) -> str:
    for value in (os.environ.get(env_name(kit)), os.environ.get("KIT_ROUTING"),
                  os.environ.get("CLAUDE_PLUGIN_OPTION_ROUTING")):
        if value and value.strip().lower() in MODES:
            return value.strip().lower()
    return DEFAULT_MODE


def emit(event: str, **fields) -> None:
    out = {"hookSpecificOutput": {"hookEventName": event, **fields}}
    sys.stdout.write(json.dumps(out))


def note_for(result: dict, kit: str, current_mode: str) -> str:
    tail = (f"This note comes from a keyword heuristic in the {kit} plugin; "
            f"{env_name(kit)}=off turns it off.")
    gate = current_mode == "gate"
    if result["route"] == "plan":
        return (f"[dev-kit routing] The request above reads as a code change across several areas "
                f"({', '.join(result['areas'])}). dev-kit is set to start on its own for changes "
                f"like this: the dev-kit:plan skill maps the repo and writes plan.md for the user's "
                f"approval, and the reply says in one line why dev-kit started. "
                + ("Repo edits are held until a plan is approved or the user says to edit directly. "
                   if gate else "")
                + f"A change that stays in one file or one area is edited directly instead. {tail}")
    if result["route"] == "investigate":
        return (f"[dev-kit routing] The request above reads as a bug report or unexplained "
                f"behaviour ({result['signal']}). dev-kit:investigate reproduces it read-only, ranks "
                f"three likely causes with file references and proposes the smallest experiment "
                f"that tells them apart, before code changes. "
                + ("dev-kit is set to start it on its own: edits are held until it has run or the "
                   "user says to fix it directly, and the reply says in one line why it started. "
                   if gate else "")
                + f"A cause the user already named, or a fix they spelled out, is fixed directly. {tail}")
    return (f"[campaign-kit routing] The request above reads as an objective measured over "
            f"several rounds (\"{result['signal']}\"). campaign-kit is proposed, never started on "
            f"its own: the reply proposes /campaign-kit:campaign in one line with the reason, and "
            f"the user decides. "
            + ("Edits wait for the user's answer this turn. " if gate else "")
            + f"One well-defined change goes to dev-kit:plan instead, and a small one is done "
              f"directly. {tail}")


def on_prompt(data: dict, kit: str, current_mode: str) -> None:
    root = find_root(data.get("cwd", ""))
    result = classify_prompt(data.get("prompt", ""), list_repo_areas(root) if root else None, root)
    if os.environ.get("DEV_KIT_ROUTING_DEBUG"):
        sys.stderr.write(json.dumps(result) + "\n")
    session = data.get("session_id", "")
    save_state(session, kit, record_prompt(load_state(session, kit), result, kit))
    if result["route"] in KIT_ROUTES.get(kit, set()):
        emit("UserPromptSubmit", additionalContext=note_for(result, kit, current_mode))


def on_edit(data: dict, kit: str, current_mode: str) -> None:
    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    root = find_root(data.get("cwd", ""))
    if not file_path or not root:
        return
    session = data.get("session_id", "")
    state = load_state(session, kit)
    out = decide_edit(state, file_path, root, current_mode, kit,
                      plan_ok=lambda: approved_plan_exists(root),
                      agent_type=data.get("agent_type") or "", in_subagent=bool(data.get("agent_id")))
    save_state(session, kit, state)
    if out:
        emit("PreToolUse", **out)


def on_skill(data: dict, kit: str) -> None:
    session = data.get("session_id", "")
    state = load_state(session, kit)
    save_state(session, kit, record_skill(state, str((data.get("tool_input") or {}).get("skill", ""))))


def on_agent(data: dict, kit: str, current_mode: str) -> None:
    if kit != "dev-kit" or current_mode != "gate":
        return
    tool_input = data.get("tool_input") or {}
    subagent = (tool_input.get("subagent_type") or "general-purpose").strip()
    if subagent.startswith(EXEMPT_AGENT_PREFIXES) or subagent.lower() in READ_ONLY_AGENTS:
        return
    root = find_root(data.get("cwd", ""))
    if root and approved_plan_exists(root):
        return
    result = classify_prompt(tool_input.get("prompt", ""), list_repo_areas(root) if root else None, root)
    if result["route"] != "plan":
        return
    session = data.get("session_id", "")
    state = load_state(session, kit)
    if state["denied_agent"] or state["optout"]:
        return
    state["denied_agent"] = True
    save_state(session, kit, state)
    emit("PreToolUse", **_deny(
        f"[dev-kit routing gate] This hands a multi-area build ({', '.join(result['areas'])}) to "
        f"the {subagent} subagent with no approved .dev-kit plan. A subagent cannot get the user's "
        f"approval for a plan; dev-kit:plan in this session can. To delegate anyway, send the same "
        f"Agent call again: this check stops a session only once. "
        f"{env_name(kit)}=nudge or off relaxes it."))


def parse_kit(argv: list[str]) -> str:
    if "--kit" in argv:
        i = argv.index("--kit")
        if i + 1 < len(argv) and argv[i + 1] in KIT_ROUTES:
            return argv[i + 1]
    return "dev-kit"


def main(argv: list[str]) -> int:
    kit = parse_kit(argv)
    current_mode = mode(kit)
    if current_mode == "off":
        return 0
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    event = data.get("hook_event_name")
    tool = data.get("tool_name")
    try:
        if event == "UserPromptSubmit":
            on_prompt(data, kit, current_mode)
        elif event == "PreToolUse" and tool in EDIT_TOOLS:
            on_edit(data, kit, current_mode)
        elif event == "PreToolUse" and tool in AGENT_TOOLS:
            on_agent(data, kit, current_mode)
        elif event == "PreToolUse" and tool == "Skill":
            on_skill(data, kit)
    except Exception as exc:  # fail open: routing must never break a session
        if os.environ.get("DEV_KIT_ROUTING_DEBUG"):
            sys.stderr.write(f"route.py error: {exc!r}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
