#!/usr/bin/env bash
# start.sh — launch MCP server and/or UI.
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/centrum-studio}"
MODE="${1:-both}"

if [ -f "${INSTALL_DIR}/.venv/bin/activate" ]; then
  source "${INSTALL_DIR}/.venv/bin/activate"
fi

case "$MODE" in
  mcp)
    exec python -m centrum_studio.server
    ;;
  ui)
    exec python -m centrum_studio.ui.app
    ;;
  both)
    python -m centrum_studio.ui.app &
    UI_PID=$!
    trap "kill $UI_PID 2>/dev/null || true" EXIT
    exec python -m centrum_studio.server
    ;;
  *)
    echo "Usage: $0 {mcp|ui|both}"
    exit 2
    ;;
esac
