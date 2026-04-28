#!/bin/bash
# ── Setup trading agents en OpenClaw (Ubuntu PC 100.119.47.93) ────────────────
# Run on the Ubuntu PC, or via ssh from Windows:
#   ssh root@100.119.47.93 "bash /tmp/setup-trading-agents.sh"

set -e

AGENTS_DIR="/root/.openclaw/agents"
WORKSPACE_DIR="/root/.openclaw"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Setting up trading agents ==="

setup_agent() {
    local NAME="$1"
    local MODEL="$2"
    local BASE_URL="$3"
    local IDENTITY_SRC="$SCRIPT_DIR/$NAME/IDENTITY.md"

    echo "  → $NAME ($MODEL)"

    # Check if workspace already exists (feedback rule: never re-add if exists)
    if [ -d "$WORKSPACE_DIR/workspace-$NAME" ]; then
        echo "    Workspace exists — updating IDENTITY.md only"
        cp "$IDENTITY_SRC" "$WORKSPACE_DIR/workspace-$NAME/IDENTITY.md"
        return
    fi

    # New agent: create workspace and agent config
    mkdir -p "$WORKSPACE_DIR/workspace-$NAME"
    cp "$IDENTITY_SRC" "$WORKSPACE_DIR/workspace-$NAME/IDENTITY.md"

    # Agent registration (uses iris config as template)
    openclaw agents add "$NAME" \
        --model "$MODEL" \
        --base-url "$BASE_URL" \
        --workspace "$WORKSPACE_DIR/workspace-$NAME" \
        --system-prompt-file "$IDENTITY_SRC" \
    2>/dev/null || echo "    Note: openclaw agents add failed — workspace created, register manually"
}

# trader-analyst: uses Claude Sonnet (via OpenClaw gateway or direct API)
setup_agent "trader-analyst" "claude-sonnet-4-6" "https://api.anthropic.com/v1"

echo ""
echo "=== Done ==="
echo "Test: openclaw run trader-analyst 'Analyze this session: {\"total_trades\": 2, \"win_rate\": 0.5}'"
