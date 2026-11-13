#!/usr/bin/env bash
# Validate the marketplace manifest and every plugin in it.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
claude plugin validate "$ROOT"
for plugin in "$ROOT"/plugins/*/; do
  claude plugin validate "$plugin"
done
# Kit routing hooks: unit tests, and dev-kit's and campaign-kit's route.py must stay identical.
python3 "$ROOT/plugins/dev-kit/hooks/test_route.py" > /dev/null
