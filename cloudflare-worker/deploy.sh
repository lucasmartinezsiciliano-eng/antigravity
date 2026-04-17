#!/usr/bin/env bash
# =============================================================
# deploy.sh — Despliega el Cloudflare Worker y actualiza main.js
# =============================================================
# Uso:
#   1. wrangler login   (solo la primera vez, abre el navegador)
#   2. bash deploy.sh
# =============================================================
set -e

WORKER_NAME="broker-lead-proxy"
MAIN_JS="../broker-web/js/main.js"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║     Broker Lead Proxy — Deploy Script            ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# 1. Desplegar Worker
echo "▶ Desplegando Worker..."
DEPLOY_OUTPUT=$(wrangler deploy 2>&1)
echo "$DEPLOY_OUTPUT"

# 2. Extraer URL del Worker del output
WORKER_URL=$(echo "$DEPLOY_OUTPUT" | grep -oE "https://${WORKER_NAME}\.[a-z0-9-]+\.workers\.dev" | head -1)

if [ -z "$WORKER_URL" ]; then
  echo ""
  echo "✗ No se pudo extraer la URL automáticamente."
  echo "  Introduce la URL del Worker manualmente (ej: https://broker-lead-proxy.account.workers.dev):"
  read -r WORKER_URL
fi

echo ""
echo "✓ Worker URL: ${WORKER_URL}/lead"
echo ""

# 3. Configurar secretos
echo "▶ Configurando N8N_URL..."
echo "  Pega la URL del webhook de n8n:"
wrangler secret put N8N_URL

echo ""
echo "▶ Configurando BROKER_SECRET..."
echo "  Genera un token aleatorio (mínimo 32 chars) o copia éste:"
# Genera uno aleatorio si openssl está disponible
if command -v openssl &>/dev/null; then
  SUGGESTED=$(openssl rand -hex 32)
  echo "  Token sugerido: ${SUGGESTED}"
fi
echo "  Introduce el token secreto:"
wrangler secret put BROKER_SECRET

# 4. Actualizar main.js con la URL del Worker
echo ""
echo "▶ Actualizando main.js..."
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "s|const N8N_WEBHOOK_URL = '.*'|const N8N_WEBHOOK_URL = '${WORKER_URL}/lead'|" "$MAIN_JS"
else
  sed -i "s|const N8N_WEBHOOK_URL = '.*'|const N8N_WEBHOOK_URL = '${WORKER_URL}/lead'|" "$MAIN_JS"
fi

echo "✓ main.js actualizado → ${WORKER_URL}/lead"

# 5. Instrucciones para n8n
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  IMPORTANTE: Configurar n8n                      ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  En el workflow 'broker-lead', ANTES del primer  ║"
echo "║  nodo útil, añade:                               ║"
echo "║                                                  ║"
echo "║  IF node:                                        ║"
echo "║    Header 'X-Broker-Token' exists AND            ║"
echo "║    Header 'X-Broker-Token' == BROKER_SECRET      ║"
echo "║                                                  ║"
echo "║  Si la condición falla → Stop Execution          ║"
echo "║  (así nadie puede enviar leads sin el token)     ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# 6. Git commit
echo "▶ Haciendo commit y push de main.js..."
cd ..
git add broker-web/js/main.js
git commit -m "security: route leads through Cloudflare Worker proxy"
git push

echo ""
echo "✓ Todo listo. La web ya usa el Worker seguro."
echo ""
echo "Verifica: ${WORKER_URL}/health"
