#!/usr/bin/env python3
"""Count passing tests per file.

  python3 tools/score.py spec            per-file lines, then "spec total <passed>/<run>"
  python3 tools/score.py spec tests
  python3 tools/score.py --json spec     the same as JSON

A module that cannot be imported counts as one failing test and is named on an ERROR line.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def score(folder):
    sys.path.insert(0, str(ROOT))
    suite = unittest.TestLoader().discover(str(ROOT / folder), pattern="test*.py",
                                           top_level_dir=str(ROOT))
    files, errors = {}, []

    def walk(node):
        for item in node:
            if isinstance(item, unittest.TestSuite):
                walk(item)
                continue
            result = unittest.TestResult()
            item.run(result)
            module = type(item).__module__
            if module == "unittest.loader":  # an import failure
                module = item.id().split(".")[-1]
                errors.append(module)
            name = module.replace(".", "/") + ".py"
            passed, run = files.get(name, (0, 0))
            files[name] = (passed + int(result.wasSuccessful()), run + 1)

    walk(suite)
    passed = sum(p for p, _ in files.values())
    run = sum(r for _, r in files.values())
    return {"folder": folder, "files": {k: list(v) for k, v in sorted(files.items())},
            "passed": passed, "run": run, "import_errors": errors}


def main(argv):
    as_json = "--json" in argv
    folders = [a for a in argv if a != "--json"] or ["spec"]
    results = [score(f) for f in folders]
    if as_json:
        print(json.dumps(results, indent=2))
        return 0
    for r in results:
        for name, (passed, run) in r["files"].items():
            print(f"{name} {passed}/{run}")
        for module in r["import_errors"]:
            print(f"ERROR cannot import {module}")
        print(f"{r['folder']} total {r['passed']}/{r['run']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
