#!/usr/bin/env python3
"""Offline tests for the kit router, plugins/{dev-kit,campaign-kit}/hooks/route.py (no model calls).

    python3 plugins/dev-kit/hooks/test_route.py           # unit tests + corpus score
    python3 plugins/dev-kit/hooks/test_route.py --all     # also print every corpus row

The corpus is labelled by hand with the route each prompt should take: PLAN (a multi-area
build), INV (a bug or unexplained behaviour), CAMP (an objective measured over rounds) or
QUIET (anything else: one-file edits, one-area changes, how-to questions, envelopes).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRIPT = HERE / "route.py"
CAMPAIGN_COPY = REPO / "plugins" / "campaign-kit" / "hooks" / "route.py"

spec = importlib.util.spec_from_file_location("route", SCRIPT)
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)

PLAN, INV, CAMP, QUIET = "plan", "investigate", "campaign", None
CORPUS: list[tuple[str | None, str]] = [
    # --- multi-area builds -> plan ---
    (PLAN, "Implement per-user rate limiting on POST /login in our Express backend, show a \"too many attempts\" message with a countdown in the React login form, and make the limit configurable per environment."),
    (PLAN, "Add a dark mode toggle to the settings screen and persist the choice in the users table via a new API endpoint."),
    (PLAN, "Build CSV export: a backend endpoint that streams the report and a button in the UI that downloads it."),
    (PLAN, "Can you add soft delete to the orders model with a database migration, and hide deleted orders in the admin frontend?"),
    (PLAN, "Add a --json flag to scripts/check_plugins.py and document it in docs/ai-sdlc/onboard-a-repo.md."),
    (PLAN, "Add a resume.md step to the dev-kit plan skill and the campaign-kit review skill."),
    (PLAN, "Create a GitHub Actions workflow file that runs the test suite, and add a CLI subcommand to run the same checks locally."),
    (PLAN, "Migrate session storage from cookies to Redis on the server and update the React client to refresh tokens."),
    (PLAN, "Implement these:\n1. a /health endpoint\n2. a status badge component\n3. an env var for the polling interval"),
    (PLAN, "Build all the options one after another."),
    (PLAN, "Write the iOS screen for notifications and the backend API that sends the push payload."),
    (PLAN, "Support uploading avatars: S3 presigned URLs from the API, an upload component in the frontend, and an avatar_url column in the database schema."),
    (PLAN, "Refactor the auth middleware into its own module and update every frontend form that posts to it."),
    (PLAN, "Introduce a feature flag for the new checkout, read it on the server and in the React app."),
    (PLAN, "Add a Dockerfile for the API and update the README with how to deploy it."),
    (PLAN, "Please implement the search feature across plugins/docs-kit/skills and scripts/check_plugins.py."),
    (PLAN, "Extend the CLI with an export command and add a docs page explaining the output format."),
    (PLAN, "Add GraphQL subscriptions on the backend and a live-updating list component on the frontend."),
    (PLAN, "Implement retry with backoff when the API returns a network error, in both the backend client and the React UI."),
    # --- bugs and unexplained behaviour -> investigate ---
    (INV, "Why does the login form crash when the API returns a 429?"),
    (INV, "The checkout page throws an error after the latest deploy, can you look into it?"),
    (INV, "Login always fails with \"Login failed (attempts: 1)\" even when I type alice and secret. Fix it."),
    (INV, "test_orders.py is flaky on CI, it fails about one run in five."),
    (INV, "Why doesn't the dev-kit plan skill write plan.md when the scout finishes?"),
    (INV, "After upgrading React the dashboard renders twice and the chart is blank. What's going on?"),
    (INV, "Getting a TypeError: cannot read properties of undefined (reading 'id') in OrderList.jsx since yesterday."),
    (INV, "The export endpoint times out for large reports, figure out why."),
    (INV, "Fix the failing test in tests/test_plan_tool.py."),
    # --- objectives over rounds -> campaign ---
    (CAMP, "Raise test coverage of server/ and client/ to 80%."),
    (CAMP, "Cut the p95 latency of POST /login below 50 ms."),
    (CAMP, "Migrate all the remaining callers of the old fetchJson helper to the new api client."),
    (CAMP, "Clear the lint warnings backlog across the repo until eslint reports zero."),
    (CAMP, "Fix all TypeScript type errors in the monorepo."),
    (CAMP, "Reduce our Claude token cost per review run by half."),
    (CAMP, "Research and prototype three options for offline sync, then recommend one."),
    (CAMP, "Get the bundle size under 200 kb, round by round."),
    # --- quiet: one file, one area, how-to questions, runs, envelopes ---
    (QUIET, "In src/config.js, rename the constant TIMEOUT to REQUEST_TIMEOUT_MS and update its two uses in the same file."),
    (QUIET, "Fix the typo in docs/ai-sdlc/onboard-a-repo.md: 'recieve' should be 'receive'."),
    (QUIET, "Add a docstring to parse_manifest in plugins/dev-kit/skills/plan/scripts/plan_tool.py."),
    (QUIET, "Add a unit test for the date formatter in src/utils/date.js."),
    (QUIET, "What does the dev-kit plan skill do?"),
    (QUIET, "How do I add a new endpoint to the Express backend and call it from React?"),
    (QUIET, "git log shows a weird merge, what happened on main yesterday?"),
    (QUIET, "/dev-kit:plan add rate limiting to the backend and frontend"),
    (QUIET, "<task-notification>Agent finished: added endpoint and frontend form</task-notification>"),
    (QUIET, "Add a padding of 8px to the submit button in LoginForm.tsx."),
    (QUIET, "Make the error message in the React login form friendlier."),
    (QUIET, "Write a short summary of this repo's README."),
    (QUIET, "Add rate limiting to the backend and frontend without a plan, just edit it directly."),
    (QUIET, "Bump the version in plugins/dev-kit/.claude-plugin/plugin.json to 1.5.0."),
    (QUIET, "Add an index on users.email in the database migration file."),
    (QUIET, "Run the tests and tell me what fails."),
    (QUIET, "Implement the retry loop in scripts/validate.sh so it tries claude plugin validate twice."),
    (QUIET, "Add a section to the dev-kit README about the routing hook."),
    (QUIET, "ok, approve the plan"),
    (QUIET, "Should we add caching to the API and the frontend, or is that overkill?"),
    (QUIET, "Add a --json flag to the focus-kit inbox command and document it in the focus-kit README."),
    (QUIET, "build and deploy all these CDK changes (UI + API too)"),
    (QUIET, "Make an overall review. Especially, look at respecting KISS/DRY/SOLID across the backend and frontend."),
    (QUIET, "Add a server-side check for empty passwords to src/server/auth.js."),
    (QUIET, "How do I raise test coverage to 80% with jest?"),
    (QUIET, "Reduce the bundle size by replacing moment with date-fns in utils/date.js."),
    (QUIET, "Add error handling to the fetch call in LoginForm.jsx."),
    (QUIET, "Write a test that reproduces the crash in parse_date."),
    (QUIET, "Why does this repo use bun instead of npm?"),
    (QUIET, "Add Angular for front-end skills, and DynamoDB for back-end/data"),  # resume text: a known FP
]


def score(repo_areas: dict | None = None, root: Path | None = None) -> dict:
    rows, by_label = [], {}
    for label, prompt in CORPUS:
        r = route.classify_prompt(prompt, repo_areas, root)
        got = r["route"]
        cell = by_label.setdefault(label or "quiet", {"ok": 0, "n": 0, "wrong": {}})
        cell["n"] += 1
        if got == label:
            cell["ok"] += 1
        else:
            cell["wrong"][got or "quiet"] = cell["wrong"].get(got or "quiet", 0) + 1
        rows.append(("ok " if got == label else "BAD", label or "quiet", got or "quiet", r["why"],
                     ",".join(r["areas"]) or r["signal"], prompt[:70].replace("\n", " ")))
    return {"by_label": by_label, "rows": rows}


ROUTING_VARS = ("DEV_KIT_ROUTING", "CAMPAIGN_KIT_ROUTING", "KIT_ROUTING", "CLAUDE_PLUGIN_OPTION_ROUTING")
BASE_ENV = {k: v for k, v in os.environ.items() if k not in ROUTING_VARS}
PLAN_PROMPT = CORPUS[0][1]
BUG_PROMPT = "Login always fails with \"Login failed (attempts: 1)\" even when I type alice and secret. Fix it."
GOAL_PROMPT = "Raise test coverage of server/ and client/ to 80%."


def run_hook(payload: dict, env: dict | None = None, kit: str = "dev-kit",
             script: Path = SCRIPT) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(script), "--kit", kit], input=json.dumps(payload),
                          text=True, capture_output=True, env={**BASE_ENV, **(env or {})}, timeout=10)
    return proc.returncode, proc.stdout


class GateTests(unittest.TestCase):
    """Default mode (gate) unless a test says otherwise."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        for d in ("plugins/dev-kit/skills", "plugins/docs-kit", "docs", "scripts", "tests", "server", "client"):
            (self.root / d).mkdir(parents=True)
        self.env = {"CLAUDE_PLUGIN_DATA": str(self.root / "_data"), "CLAUDE_PROJECT_DIR": str(self.root)}
        self.session = "s-" + os.urandom(4).hex()

    def tearDown(self):
        self.tmp.cleanup()

    def _out(self, payload: dict, mode: str | None, kit: str) -> dict:
        env = dict(self.env)
        if mode:
            env["KIT_ROUTING"] = mode
        code, out = run_hook(payload, env, kit=kit)
        self.assertEqual(code, 0)
        return json.loads(out)["hookSpecificOutput"] if out.strip() else {}

    def prompt(self, text: str, mode: str | None = None, kit: str = "dev-kit") -> dict:
        return self._out({"hook_event_name": "UserPromptSubmit", "session_id": self.session,
                          "cwd": str(self.root), "prompt": text}, mode, kit)

    def edit(self, rel: str, mode: str | None = None, kit: str = "dev-kit", **extra) -> dict:
        return self._out({"hook_event_name": "PreToolUse", "tool_name": "Edit", "session_id": self.session,
                          "cwd": str(self.root), "tool_input": {"file_path": str(self.root / rel)}, **extra},
                         mode, kit)

    def held(self, out: dict) -> bool:
        return out.get("permissionDecision") == "deny"

    def test_default_mode_is_gate(self):
        self.assertEqual(subprocess.run([sys.executable, "-c", f"import importlib.util as u;s=u.spec_from_file_location('r',{str(SCRIPT)!r});m=u.module_from_spec(s);s.loader.exec_module(m);print(m.mode('dev-kit'))"],
                                        capture_output=True, text=True, env=BASE_ENV).stdout.strip(), "gate")

    def test_one_area_task_is_never_held(self):
        self.prompt("In scripts/a.py, rename the constant TIMEOUT to REQUEST_TIMEOUT_MS.")
        for rel in ("scripts/a.py", "scripts/b.py", "tests/test_a.py", "README.md"):
            self.assertEqual(self.edit(rel), {}, rel)
        self.assertEqual(self.edit("/tmp/elsewhere.txt"), {})

    def test_spread_is_held_until_the_user_says_edit_directly(self):
        self.prompt("Rename the attempts field to failedAttempts everywhere it is used.")
        self.assertEqual(self.edit("server/a.js"), {})
        self.assertTrue(self.held(self.edit("client/b.jsx")))
        self.assertTrue(self.held(self.edit("client/b.jsx")))  # a retry is held too
        self.prompt("That's small, just edit it directly.")
        self.assertEqual(self.edit("client/b.jsx"), {})

    def test_area_tracking_restarts_with_each_task(self):
        self.prompt("Fix the off-by-one in scripts/a.py please, it skips the last item.")
        self.edit("scripts/a.py")
        self.prompt("Now update the wording of the intro paragraph in docs/a.md.")
        self.assertEqual(self.edit("docs/a.md"), {})

    def test_nudge_notes_once_and_never_holds(self):
        self.prompt("Rename the attempts field to failedAttempts everywhere it is used.", mode="nudge")
        self.edit("scripts/a.py", mode="nudge")
        out = self.edit("docs/a.md", mode="nudge")
        self.assertIn("additionalContext", out)
        self.assertFalse(self.held(out))
        self.assertEqual(self.edit("plugins/docs-kit/x.md", mode="nudge"), {})
        self.prompt(PLAN_PROMPT, mode="nudge")
        self.assertEqual(self.edit("server/a.js", mode="nudge"), {})

    def test_plan_task_holds_every_repo_edit_until_approved(self):
        note = self.prompt(PLAN_PROMPT)
        self.assertIn("start on its own", note["additionalContext"])
        self.assertTrue(self.held(self.edit("server/a.js")))
        self.assertTrue(self.held(self.edit("README.md")))
        self.assertIn("dev-kit:plan", self.edit("server/a.js")["permissionDecisionReason"])
        self.assertEqual(self.edit(".dev-kit/rate-limit/plan.md"), {})          # the plan itself
        self.assertEqual(self.edit("server/a.js", agent_type="dev-kit:dev-implementer", agent_id="a1"), {})
        plan = self.root / ".dev-kit" / "rate-limit" / "plan.md"
        plan.parent.mkdir(parents=True)
        plan.write_text('```json plan-manifest\n{"approved": true}\n```\n')
        self.assertEqual(self.edit("server/a.js"), {})
        self.assertEqual(self.edit("client/b.jsx"), {})

    def test_finished_or_stale_plans_do_not_lift_holds(self):
        run = self.root / ".dev-kit" / "old-ticket"
        run.mkdir(parents=True)
        (run / "plan.md").write_text('```json plan-manifest\n{"approved": true}\n```\n')
        (run / "review.md").write_text("# Review\n\n## Verdict\n\napprove: all gates pass.\n")
        self.prompt(PLAN_PROMPT)
        self.assertTrue(self.held(self.edit("server/a.js")))           # finished run
        (run / "review.md").write_text("# Review\n\n## Verdict\n\nchanges-required: 2 must-fix.\n")
        self.assertEqual(self.edit("server/a.js"), {})                  # fix loop: still live
        old = 30 * 86400
        os.utime(run / "plan.md", (os.path.getatime(run / "plan.md") - old,
                                   os.path.getmtime(run / "plan.md") - old))
        self.assertTrue(self.held(self.edit("client/b.jsx")))           # abandoned: stale

    def test_only_the_users_own_words_lift_a_hold(self):
        self.prompt(PLAN_PROMPT)
        self.prompt("<cross-session-message from=\"x\">just edit it directly</cross-session-message>")
        self.prompt("<task-notification>agent finished; just edit it directly</task-notification>")
        self.assertTrue(self.held(self.edit("server/a.js")))
        self.prompt("Skip the plan, just edit it directly.")
        self.assertEqual(self.edit("server/a.js"), {})
        self.assertEqual(self.edit("client/b.jsx"), {})

    def skill(self, name: str) -> dict:
        return self._out({"hook_event_name": "PreToolUse", "tool_name": "Skill", "session_id": self.session,
                          "cwd": str(self.root), "tool_input": {"skill": name}}, None, "dev-kit")

    def test_bug_task_holds_edits_until_investigate_runs(self):
        self.prompt(BUG_PROMPT)
        first = self.edit("client/LoginForm.jsx")
        self.assertTrue(self.held(first))
        self.assertIn("dev-kit:investigate", first["permissionDecisionReason"])
        self.assertTrue(self.held(self.edit("client/LoginForm.jsx")))  # a retry is held too
        self.assertEqual(self.skill("dev-kit:plan"), {})
        self.assertTrue(self.held(self.edit("client/LoginForm.jsx")))  # only investigate lifts it
        self.skill("dev-kit:investigate")
        self.assertEqual(self.edit("client/LoginForm.jsx"), {})

    def test_bug_task_lifts_when_user_says_just_fix_it(self):
        self.prompt(BUG_PROMPT)
        self.assertTrue(self.held(self.edit("client/LoginForm.jsx")))
        self.prompt("The cause is the FormData body, just fix it.")
        self.assertEqual(self.edit("client/LoginForm.jsx"), {})

    def test_campaign_turn_holds_edits_in_campaign_kit_only(self):
        note = self.prompt(GOAL_PROMPT, kit="campaign-kit")
        self.assertIn("proposed, never started", note["additionalContext"])
        self.assertEqual(self.prompt(GOAL_PROMPT, kit="dev-kit"), {})
        self.assertTrue(self.held(self.edit("server/a.test.js", kit="campaign-kit")))
        self.assertTrue(self.held(self.edit("server/a.test.js", kit="campaign-kit")))
        self.assertEqual(self.edit("server/a.test.js", kit="dev-kit"), {})
        self.prompt("No campaign, write the server tests yourself.", kit="campaign-kit")
        self.assertEqual(self.edit("server/a.test.js", kit="campaign-kit"), {})

    def test_off_mode_is_silent(self):
        self.assertEqual(self.prompt(PLAN_PROMPT, mode="off"), {})
        self.assertEqual(self.edit("server/a.js", mode="off"), {})

    def test_subagent_reason_says_report_back(self):
        self.prompt(PLAN_PROMPT)
        out = self.edit("server/a.js", agent_id="x", agent_type="general-purpose")
        self.assertIn("report back", out["permissionDecisionReason"])


class PromptAndAgentTests(unittest.TestCase):
    def prompt(self, text: str, kit: str = "dev-kit", env: dict | None = None) -> str:
        with tempfile.TemporaryDirectory() as d:
            code, out = run_hook({"hook_event_name": "UserPromptSubmit", "cwd": "/nonexistent",
                                  "session_id": "p", "prompt": text},
                                 {"CLAUDE_PROJECT_DIR": "", "CLAUDE_PLUGIN_DATA": d, **(env or {})}, kit=kit)
        self.assertEqual(code, 0)
        return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out.strip() else ""

    def test_each_kit_announces_only_its_routes(self):
        self.assertIn("dev-kit:plan", self.prompt(PLAN_PROMPT))
        self.assertIn("dev-kit:investigate", self.prompt(BUG_PROMPT))
        self.assertEqual(self.prompt(GOAL_PROMPT), "")
        self.assertIn("campaign-kit:campaign", self.prompt(GOAL_PROMPT, kit="campaign-kit"))
        self.assertEqual(self.prompt(PLAN_PROMPT, kit="campaign-kit"), "")
        self.assertEqual(self.prompt(BUG_PROMPT, kit="campaign-kit"), "")

    def test_notes_are_short_and_switchable(self):
        for text, kit in ((PLAN_PROMPT, "dev-kit"), (GOAL_PROMPT, "campaign-kit")):
            note = self.prompt(text, kit=kit)
            self.assertLess(len(note), 900)
            self.assertIn(route.env_name(kit) + "=off", note)
        self.assertEqual(self.prompt(PLAN_PROMPT, env={"DEV_KIT_ROUTING": "off"}), "")
        self.assertEqual(self.prompt(GOAL_PROMPT, kit="campaign-kit", env={"KIT_ROUTING": "off"}), "")

    def test_prompt_hook_quiet_on_one_file_edit(self):
        self.assertEqual(self.prompt(CORPUS[37][1]), "")

    def test_agent_gate_once_in_gate_mode(self):
        with tempfile.TemporaryDirectory() as d:
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Agent", "session_id": "ag",
                       "cwd": d, "tool_input": {"subagent_type": "general-purpose", "prompt": PLAN_PROMPT}}
            env = {"CLAUDE_PLUGIN_DATA": d, "CLAUDE_PROJECT_DIR": d}
            self.assertEqual(run_hook(payload, {**env, "DEV_KIT_ROUTING": "nudge"})[1].strip(), "")
            out = json.loads(run_hook(payload, env)[1])
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertEqual(run_hook(payload, env)[1].strip(), "")
            payload["tool_input"]["subagent_type"] = "dev-kit:dev-scout"
            payload["session_id"] = "ag2"
            self.assertEqual(run_hook(payload, env)[1].strip(), "")

    def test_garbage_input_fails_open(self):
        proc = subprocess.run([sys.executable, str(SCRIPT)], input="not json", text=True,
                              capture_output=True, timeout=10, env=BASE_ENV)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))

    @unittest.skipUnless(CAMPAIGN_COPY.exists(), "campaign-kit is not beside dev-kit (installed copy)")
    def test_kit_copies_are_identical(self):
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        self.assertEqual(digest(SCRIPT), digest(CAMPAIGN_COPY),
                         "plugins/campaign-kit/hooks/route.py must be a copy of dev-kit's")


def print_corpus(label: str, repo_areas: dict | None, root: Path | None = None) -> None:
    s = score(repo_areas, root)
    cells = "  ".join(f"{k} {v['ok']}/{v['n']}" + (f" (wrong: {v['wrong']})" if v["wrong"] else "")
                      for k, v in s["by_label"].items())
    print(f"\n== corpus ({label}, n={len(CORPUS)}): {cells}")
    for row in s["rows"]:
        if row[0] == "BAD" or "--all" in sys.argv:
            print("  " + " | ".join(str(c) for c in row))


if __name__ == "__main__":
    this_repo = route.list_repo_areas(REPO)
    print_corpus("no repo", None)
    print_corpus("inside this repo", this_repo, REPO)
    sys.argv = [sys.argv[0]]
    unittest.main(verbosity=1)
