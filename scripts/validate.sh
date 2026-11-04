#!/usr/bin/env bash
# Validate the marketplace manifest and every plugin in it.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
claude plugin validate "$ROOT"
for plugin in "$ROOT"/plugins/*/; do
  claude plugin validate "$plugin"
done
