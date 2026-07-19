#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done
[ -n "$PYTHON" ] || { echo "ERROR: Python 3.11+ not found." >&2; exit 1; }
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/goverdocs rebuild-index --root .
.venv/bin/pytest
.venv/bin/goverdocs health --root . --receipt
echo "GOVERDOCS_BOOTSTRAP=COMPLETE"
echo "ROOT=$ROOT"
echo "PYTHON=$(.venv/bin/python --version)"
