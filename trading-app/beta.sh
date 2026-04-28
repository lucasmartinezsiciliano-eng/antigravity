#!/bin/bash
# ── Beta testing entrypoint ───────────────────────────────────────────────────
# Usage:
#   bash beta.sh start     → arranca stack local (paper trading)
#   bash beta.sh stop      → para el stack
#   bash beta.sh signal    → envía una señal de test (IFVG long NQ)
#   bash beta.sh session   → envía 2 señales (simula sesión completa)
#   bash beta.sh review    → genera informe de analytics
#   bash beta.sh logs      → muestra trades.jsonl en tiempo real
#   bash beta.sh status    → health check

set -e
CMD="${1:-help}"

COMPOSE="docker compose -f docker-compose.local.yml"

case "$CMD" in

  start)
    echo "=== Starting local beta stack ==="
    if [ ! -f .env ]; then
        cp .env.example .env
        KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "test-key-replace-me")
        sed -i "s/replace-with-random-hex/$KEY/" .env
        echo ">>> .env created with API key: $KEY"
        echo ">>> Fill in IBKR_USER, IBKR_PASS before trading. Paper mode is active."
    fi
    $COMPOSE up -d --build
    echo ""
    echo "Stack running:"
    echo "  Webhook:    http://localhost:8000/webhook"
    echo "  Health:     http://localhost:8000/status"
    echo "  IB Gateway VNC: localhost:5900 (password: changeme)"
    echo ""
    echo "Next: bash beta.sh signal"
    ;;

  stop)
    $COMPOSE down
    echo "Stack stopped."
    ;;

  signal)
    SYMBOL="${2:-NQ1!}"
    ACTION="${3:-BUY}"
    echo "=== Sending test signal: $ACTION $SYMBOL ==="
    python3 test_signals.py --scenario long --symbol "$SYMBOL" --action "$ACTION"
    ;;

  session)
    echo "=== Simulating full NY AM session (2 signals) ==="
    python3 test_signals.py --scenario session --delay 3
    ;;

  stocks)
    echo "=== Testing stock signals (AAPL + MSFT) ==="
    python3 test_signals.py --scenario stocks --delay 2
    ;;

  review)
    echo "=== Running post-session analytics ==="
    python3 analytics.py
    ;;

  review-json)
    python3 analytics.py --json
    ;;

  apply)
    echo "=== Applying recommended .env changes ==="
    python3 analytics.py --apply
    echo ">>> Restart executor to apply: $COMPOSE restart executor"
    ;;

  logs)
    echo "=== Tailing trades.jsonl (Ctrl+C to stop) ==="
    tail -f trades.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        ev = d.get('event','')
        if ev == 'order_placed':
            print(f\"  ✅ {d.get('action')} {d.get('symbol')} x{d.get('qty')} @ {d.get('entry')} | SL {d.get('sl')} TP {d.get('tp')}\")
        elif ev == 'skip':
            print(f\"  ⏭  SKIP: {d.get('reason')}\")
        elif ev == 'error':
            print(f\"  ❌ ERROR: {d.get('msg')}\")
        else:
            print(f\"  · {ev}: {line.strip()[:120]}\")
    except:
        print(line.strip()[:120])
"
    ;;

  status)
    echo "=== Health check ==="
    python3 -c "
import requests
try:
    r = requests.get('http://localhost:8000/status', timeout=3)
    d = r.json()
    print(f'  API:   {r.status_code} {d}')
except Exception as e:
    print(f'  API:   ERROR — {e}')
"
    echo ""
    $COMPOSE ps
    ;;

  setup-agent)
    echo "=== Setting up trader-analyst agent on OpenClaw ==="
    UBUNTU_IP="${UBUNTU_IP:-100.119.47.93}"
    echo "Copying agents to $UBUNTU_IP..."
    scp -r agents/ "root@$UBUNTU_IP:/tmp/trading-agents"
    ssh "root@$UBUNTU_IP" "bash /tmp/trading-agents/setup-trading-agents.sh"
    ;;

  help|*)
    echo "Usage: bash beta.sh [command]"
    echo ""
    echo "  start       → Start local paper trading stack"
    echo "  stop        → Stop stack"
    echo "  signal      → Send one test signal"
    echo "  session     → Simulate full session (2 signals)"
    echo "  stocks      → Test stock signals (AAPL/MSFT)"
    echo "  review      → Run analytics report"
    echo "  apply       → Apply .env recommendations"
    echo "  logs        → Tail trades.jsonl"
    echo "  status      → Health check"
    echo "  setup-agent → Install trader-analyst on OpenClaw Ubuntu"
    ;;

esac
