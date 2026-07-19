#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[ -x .venv/bin/python ] || { echo "ERROR: missing .venv; run scripts/bootstrap_local.sh" >&2; exit 1; }
.venv/bin/ruff check src tests
.venv/bin/mypy src
.venv/bin/pytest
.venv/bin/goverdocs validate --root . --receipt
.venv/bin/goverdocs health --root .
echo "GOVERDOCS_VERIFY=PASS"
