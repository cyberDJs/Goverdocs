#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
./scripts/verify.sh
printf '\nPress Enter to close...'
read -r _
