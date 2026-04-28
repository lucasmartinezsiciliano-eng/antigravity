#!/bin/bash
# ── Post-session review — runs after NY AM close (11:15 ET) ──────────────────
# Generates analytics report and invokes trader-analyst agent.
# Schedule via cron: 15 11 * * 1-5 bash /app/run_session_review.sh
# (11:15 ET = 15:15 UTC = adjust to your VPS timezone)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORT="$SCRIPT_DIR/analytics_report.json"
AGENT_WORKSPACE="/root/.openclaw/workspace-trader-analyst"

echo "[$(date)] Starting post-session review..."

# 1. Generate analytics report
python3 "$SCRIPT_DIR/analytics.py" --json > "$REPORT"
echo "[$(date)] Analytics report written to $REPORT"

# 2. Print human-readable report
python3 "$SCRIPT_DIR/analytics.py"

# 3. Invoke trader-analyst agent if OpenClaw is available
if command -v openclaw &>/dev/null; then
    echo "[$(date)] Invoking trader-analyst agent..."
    REPORT_CONTENT=$(cat "$REPORT")
    openclaw run trader-analyst "Post-session review. Analytics data: $REPORT_CONTENT" \
        > "$AGENT_WORKSPACE/recommendations.md" 2>&1
    echo "[$(date)] Recommendations saved to $AGENT_WORKSPACE/recommendations.md"
    cat "$AGENT_WORKSPACE/recommendations.md"
else
    echo "[$(date)] OpenClaw not available — skipping agent analysis (analytics.py report is the output)"
fi

echo "[$(date)] Session review complete."
