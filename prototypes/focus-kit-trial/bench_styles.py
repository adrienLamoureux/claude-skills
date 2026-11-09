#!/usr/bin/env python3
"""Compare output styles on the reader-first rules (standard library only).

  python3 prototypes/focus-kit-trial/bench_styles.py [--runs N] [--model sonnet] [--styles A,B,C]

Costs about USD 0.06 per reply on Sonnet (9 replies with the defaults).

Runs each prompt in PROMPTS once per style (and per run) through `claude -p` with no tools,
loading plugins/focus-kit so its Reader-first style is available, then scores every reply:

  words        reply length in words (lower is better, for these conversational prompts)
  first_line   line 1 gives the answer, not a preamble ("I'll", "Let me", "Sure", "Great")
  next_move    the last line says what the user must do ("Your move:" or "Nothing needed")
  glosses      parenthesised glosses of at most eight words, e.g. "idempotent (safe to run twice)"

Writes results.json and a Markdown table next to this file and prints the table.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PLUGIN = ROOT / "plugins" / "focus-kit"

PROMPTS = {
    "decide": "Our CI test job takes 14 minutes. Two options: cache node_modules, or split the "
              "test suite into 4 parallel shards. Which should I do first?",
    "terms": "What is an idempotency key, and does a Stripe webhook handler that writes orders "
             "to Postgres need one?",
    "debug": "npm ci failed in CI with 'ECONNRESET' while fetching from the registry. The same "
             "commit passed an hour ago. What should I do?",
}
PREAMBLE = re.compile(r"^\s*(i'll|i will|let me|sure|great|okay|ok,|certainly|good question)",
                      re.I)
NEXT_MOVE = re.compile(r"(your move|nothing needed)", re.I)
GLOSS = re.compile(r"\b[\w-]+ \((?:[^()\n]{3,60})\)")


def run(prompt: str, style: str, model: str) -> dict:
    settings = json.dumps({"outputStyle": style})
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "json",
           "--plugin-dir", str(PLUGIN), "--settings", settings,
           "--permission-mode", "dontAsk", "--max-budget-usd", "0.30"]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE, timeout=300)
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"error": (out.stderr or out.stdout)[-400:]}
    return {"text": data.get("result") or "", "cost": data.get("total_cost_usd") or 0.0}


def score(text: str) -> dict:
    lines = [line for line in text.strip().splitlines() if line.strip()]
    glosses = [g for g in GLOSS.findall(text) if len(g.split("(", 1)[1].split()) <= 8]
    return {
        "words": len(text.split()),
        "first_line": bool(lines) and not PREAMBLE.match(lines[0]),
        "next_move": bool(lines) and bool(NEXT_MOVE.search(lines[-1])),
        "glosses": len(glosses),
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--model", default="sonnet")
    # A plugin's style is named <plugin>:<style name>; a bare "Reader-first" is not found.
    ap.add_argument("--styles", default="default,Concise,focus-kit:Reader-first")
    args = ap.parse_args(argv)
    styles = args.styles.split(",")
    results, cost = [], 0.0
    for style in styles:
        for name, prompt in PROMPTS.items():
            for i in range(args.runs):
                r = run(prompt, style, args.model)
                if "error" in r:
                    print(f"{style}/{name}: {r['error']}", file=sys.stderr)
                    continue
                cost += r["cost"]
                results.append({"style": style, "prompt": name, "run": i, **score(r["text"]),
                                "cost": r["cost"], "text": r["text"]})
    (HERE / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    rows = ["| style | replies | mean words | answer in line 1 | ends with next move | glosses |",
            "|---|---|---|---|---|---|"]
    for style in styles:
        rs = [r for r in results if r["style"] == style]
        if not rs:
            continue
        n = len(rs)
        rows.append(f"| {style} | {n} | {sum(r['words'] for r in rs) / n:.0f} | "
                    f"{sum(r['first_line'] for r in rs)}/{n} | "
                    f"{sum(r['next_move'] for r in rs)}/{n} | {sum(r['glosses'] for r in rs)} |")
    rows.append(f"\nModel {args.model}, {args.runs} run(s) per prompt, total USD {cost:.2f}.")
    table = "\n".join(rows)
    (HERE / "RESULTS.md").write_text("# Output style benchmark\n\n" + table + "\n")
    print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
