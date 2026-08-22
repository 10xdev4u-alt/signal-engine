#!/usr/bin/env bash
# Single verification gate for the whole project (see AGENTS.md).
set -euo pipefail
cd "$(dirname "$0")"

cmd="${1:-check}"

case "$cmd" in
check)
    ruff check signal_engine tests
    pytest -q
    ;;
*)
    exec python -m signal_engine "$@"
    ;;
esac
