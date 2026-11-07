#!/usr/bin/env python3
"""Black-box acceptance suite: runs test cases kept outside this repository, like a CI job you
cannot edit. One line per failing case, then "acceptance total <passed>/<run>".

  python3 tools/accept.py
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUITE = Path("__ACCEPTANCE_DIR__")


def main():
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(SUITE))
    suite = unittest.TestLoader().loadTestsFromName("holdout.test_holdout")
    result = unittest.TestResult()
    suite.run(result)
    bad = sorted(((t.id().split(".")[-1], err) for t, err in result.failures + result.errors))
    for name, err in bad:
        lines = [line for line in err.strip().splitlines() if line.strip()]
        first = next((line for line in reversed(lines) if not line.startswith(" ")
                      and ("Error" in line or "Exception" in line)), lines[-1])
        note = next((line.strip() for line in lines if line.startswith(" : ")), "")
        print(f"FAIL {name}: {first.strip()[:160]} {note[:120]}".rstrip())
    print(f"acceptance total {result.testsRun - len(bad)}/{result.testsRun}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
