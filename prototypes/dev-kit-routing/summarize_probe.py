#!/usr/bin/env python3
"""Summarise a headless probe run (claude -p --output-format stream-json --verbose
--include-hook-events) into one JSON line: did the routing hook add context, which tools ran
in order, did dev-kit:plan fire, turns, cost.

    python3 prototypes/dev-kit-routing/summarize_probe.py <run.jsonl> [label]
"""
import json
import sys


def main() -> int:
    path = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else path
    tools, hook_ctx, hook_deny, plugins, result = [], [], [], [], {}
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        kind, sub = ev.get("type"), ev.get("subtype")
        if kind == "system" and sub == "init":
            plugins = [p.get("name") for p in ev.get("plugins", [])]
        blob = json.dumps(ev)
        if kind == "system" and "hook" in (sub or ""):
            if "[dev-kit routing]" in blob or "[campaign-kit routing]" in blob:
                hook_ctx.append(ev.get("hook_event") or ev.get("hook_event_name") or sub)
            if "[dev-kit routing gate]" in blob:
                hook_deny.append(ev.get("hook_event") or ev.get("hook_event_name") or sub)
        if kind == "assistant":
            for block in (ev.get("message") or {}).get("content", []):
                if block.get("type") == "tool_use":
                    inp = block.get("input") or {}
                    detail = inp.get("skill") or inp.get("file_path") or inp.get("pattern") or ""
                    tools.append(f"{block['name']}:{detail}" if detail else block["name"])
        if kind == "user" and "[dev-kit routing gate]" in blob:
            hook_deny.append("tool_result")
        if kind == "result":
            result = ev
    skills = [t for t in tools if t.startswith("Skill:")]
    edits = [t for t in tools if t.split(":")[0] in ("Edit", "Write", "MultiEdit")]
    print(json.dumps({
        "probe": label,
        "plugins": plugins,
        "hook_context_events": hook_ctx,
        "gate_denials": hook_deny,
        "plan_skill_fired": any("dev-kit:plan" in s for s in skills),
        "kit_skills_fired": sorted({s.split(":", 1)[1] for s in skills
                                    if s.split(":", 1)[1].startswith(("dev-kit:", "campaign-kit:"))}),
        "skills": skills,
        "edits": edits,
        "tool_sequence": tools,
        "num_turns": result.get("num_turns"),
        "cost_usd": result.get("total_cost_usd"),
        "stop": result.get("subtype"),
        "result_excerpt": (result.get("result") or "")[:400],
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
