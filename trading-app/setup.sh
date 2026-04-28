#!/bin/bash
# ── Trading App — VPS Setup ───────────────────────────────────────────────────
# Run once on a fresh Ubuntu 22.04 VPS.
# Usage: bash setup.sh yourdomain.com

set -e
DOMAIN=${1:-""}

echo "=== 1. Docker ==="
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    apt-get install -y docker-compose-plugin
fi

echo "=== 2. SSL (Certbot) ==="
if [ -n "$DOMAIN" ]; then
    apt-get install -y certbot
    certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos -m admin@"$DOMAIN"
    # Patch nginx.conf with the real domain
    sed -i "s/YOUR_DOMAIN_HERE/$DOMAIN/g" nginx.conf
else
    echo "No domain provided — skipping SSL. Set DOMAIN and re-run."
fi

echo "=== 3. .env ==="
if [ ! -f .env ]; then
    cp .env.example .env
    API_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/replace-with-random-hex/$API_KEY/" .env
    echo ""
    echo ">>> .env created. Fill in IBKR_USER, IBKR_PASS, TELEGRAM_* before starting."
    echo ">>> WEBHOOK_API_KEY auto-generated: $API_KEY"
    echo ">>> Use this key as the X-Api-Key header in TradingView webhook settings."
fi

echo "=== 4. Docker Compose up ==="
docker compose up -d --build

echo ""
echo "=== Done ==="
echo "Test: curl https://$DOMAIN/status"
echo "Webhook URL for TradingView: https://$DOMAIN/webhook"
