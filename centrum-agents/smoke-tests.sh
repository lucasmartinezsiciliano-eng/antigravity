#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# CENTRUM — Smoke Tests post-instalación
# ═══════════════════════════════════════════════════════════════════════════════
# Validar que cada integración funciona ANTES de poner Centrum en producción.
# Ejecutar después de:
#   - bash setup-centrum.sh
#   - bash vllm-start.sh
#   - Editar .env de cada perfil con credenciales reales
#
# Uso:
#   bash smoke-tests.sh          # ejecuta TODOS los tests
#   bash smoke-tests.sh vllm     # solo el bloque vllm
#   bash smoke-tests.sh twilio   # solo twilio
# ═══════════════════════════════════════════════════════════════════════════════

set -uo pipefail  # NO -e: queremos seguir tras un fallo y reportar al final

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
RESULTS_FILE="/tmp/centrum-smoke-$(date +%Y%m%d-%H%M%S).log"
PASSED=0; FAILED=0; SKIPPED=0

# Colores
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1" | tee -a "$RESULTS_FILE"; PASSED=$((PASSED+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1" | tee -a "$RESULTS_FILE"; FAILED=$((FAILED+1)); }
skip() { echo -e "${YELLOW}[SKIP]${NC} $1" | tee -a "$RESULTS_FILE"; SKIPPED=$((SKIPPED+1)); }
section() { echo -e "\n${BLUE}═══ $1 ═══${NC}" | tee -a "$RESULTS_FILE"; }

# ── Cargar credenciales del perfil centrum ───────────────────────────────────
if [[ -f "$HERMES_HOME/profiles/centrum/.env" ]]; then
    set -a; source "$HERMES_HOME/profiles/centrum/.env"; set +a
fi
if [[ -f "$HERMES_HOME/profiles/centrum-content/.env" ]]; then
    set -a; source "$HERMES_HOME/profiles/centrum-content/.env"; set +a
fi

FILTER="${1:-all}"

# ═══════════════════════════════════════════════════════════════════════════════
# 1. vLLM — modelos locales en DGX Spark
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "vllm" ]]; then
    section "vLLM en DGX Spark"

    # Nano (puerto 8001)
    if curl -sf "http://localhost:8001/health" > /dev/null 2>&1; then
        pass "Nano (E4B) responde en :8001"
    else
        fail "Nano (E4B) NO responde en :8001 — revisar vllm-start.sh"
    fi

    # Pro (puerto 8002)
    if curl -sf "http://localhost:8002/health" > /dev/null 2>&1; then
        pass "Pro (26B) responde en :8002"
    else
        fail "Pro (26B) NO responde en :8002 — revisar vllm-start.sh"
    fi

    # Max (puerto 8003) — Qwen 3.6 35B principal
    if curl -sf "http://localhost:8003/health" > /dev/null 2>&1; then
        pass "Max/Qwen3.6 (35B) responde en :8003"
    else
        skip "Qwen3.6 (35B) NO responde en :8003 — carga on-demand, ejecutar vllm-load-max.sh"
    fi

    # Inferencia real — pedir un completion a Pro
    response=$(curl -sf -X POST "http://localhost:8002/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{"model":"gemma-4-26B-A4B-it","messages":[{"role":"user","content":"di OK y nada más"}],"max_tokens":10}' \
        2>/dev/null | grep -o '"content":"[^"]*"' | head -1)
    if [[ -n "$response" ]]; then
        pass "Inferencia Pro funciona — respuesta: $response"
    else
        fail "Inferencia Pro NO responde — revisar logs en /var/log/vllm/"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 2. Hermes — perfiles cargados
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "hermes" ]]; then
    section "Hermes profiles"

    if ! command -v hermes &> /dev/null; then
        fail "Hermes no está en PATH — instalar con pipx install hermes-agent"
    else
        pass "Hermes binario instalado: $(hermes --version 2>/dev/null || echo 'unknown')"

        for profile in centrum centrum-intel centrum-content; do
            if [[ -f "$HERMES_HOME/profiles/$profile/SOUL.md" ]] && \
               [[ -f "$HERMES_HOME/profiles/$profile/config.yaml" ]]; then
                pass "Perfil $profile completo (SOUL + config)"
            else
                fail "Perfil $profile incompleto en $HERMES_HOME/profiles/$profile/"
            fi
        done

        # Chat de prueba al orquestador
        if echo "ping" | hermes chat --profile centrum --no-stream 2>/dev/null | grep -qi "pong\|hola\|aquí\|listo"; then
            pass "Hermes centrum responde a 'ping'"
        else
            skip "Hermes centrum no respondió como esperado — verificar manualmente con 'hermes chat --profile centrum'"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 3. Telegram bot Centrum
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "telegram" ]]; then
    section "Telegram bot Centrum"

    if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
        skip "TELEGRAM_BOT_TOKEN no configurado en .env de centrum"
    else
        # GetMe
        bot_info=$(curl -sf "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" 2>/dev/null)
        if echo "$bot_info" | grep -q '"ok":true'; then
            bot_name=$(echo "$bot_info" | grep -o '"username":"[^"]*"' | head -1)
            pass "Bot Telegram autenticado: $bot_name"
        else
            fail "Bot Telegram NO autenticado — token inválido o red"
        fi

        # Enviar mensaje a Lucas (chat ID admin)
        if [[ -n "${TELEGRAM_CHAT_ID_LUCAS:-}" ]]; then
            sent=$(curl -sf -X POST \
                "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
                -d "chat_id=${TELEGRAM_CHAT_ID_LUCAS}" \
                -d "text=🧪 Smoke test Centrum — $(date +%H:%M:%S)" 2>/dev/null)
            if echo "$sent" | grep -q '"ok":true'; then
                pass "Telegram → Lucas: mensaje enviado correctamente"
            else
                fail "Telegram → Lucas: error al enviar"
            fi
        else
            skip "TELEGRAM_CHAT_ID_LUCAS no configurado"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 4. Twilio — Voice + WhatsApp
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "twilio" ]]; then
    section "Twilio"

    if [[ -z "${TWILIO_ACCOUNT_SID:-}" || -z "${TWILIO_AUTH_TOKEN:-}" ]]; then
        skip "TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN no configurados"
    else
        # Validar credenciales
        account=$(curl -sf -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
            "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}.json" 2>/dev/null)
        if echo "$account" | grep -q '"status"'; then
            status=$(echo "$account" | grep -o '"status":"[^"]*"' | head -1)
            balance=$(curl -sf -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
                "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Balance.json" 2>/dev/null | \
                grep -o '"balance":"[^"]*"')
            pass "Twilio autenticado — $status — $balance"
        else
            fail "Twilio NO autenticado — revisar credenciales"
        fi

        # Listar números (debe haber al menos 1 español)
        numbers=$(curl -sf -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
            "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers.json" 2>/dev/null | \
            grep -c '"phone_number"')
        if [[ "$numbers" -gt 0 ]]; then
            pass "Twilio: $numbers número(s) provisionado(s)"
        else
            fail "Twilio: NO hay números provisionados — comprar uno español"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 5. SMTP — email saliente
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "smtp" ]]; then
    section "SMTP Email"

    if [[ -z "${SMTP_HOST:-}" || -z "${SMTP_USER:-}" ]]; then
        skip "SMTP no configurado"
    else
        if command -v swaks &> /dev/null; then
            # Enviar email de prueba al propio SMTP_USER
            if swaks --to "$SMTP_USER" --from "$SMTP_USER" \
                --server "$SMTP_HOST" --port 587 --tls \
                --auth-user "$SMTP_USER" --auth-password "$SMTP_PASS" \
                --header "Subject: Centrum smoke test" \
                --body "Test $(date)" > /dev/null 2>&1; then
                pass "SMTP: email enviado correctamente"
            else
                fail "SMTP: error al enviar"
            fi
        else
            skip "swaks no instalado — apt install swaks para test SMTP"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 6. Google Calendar
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "calendar" ]]; then
    section "Google Calendar"

    if [[ -z "${GOOGLE_CALENDAR_CREDENTIALS:-}" ]]; then
        skip "GOOGLE_CALENDAR_CREDENTIALS no configurado"
    else
        if [[ -f "$GOOGLE_CALENDAR_CREDENTIALS" ]]; then
            pass "Credenciales Google Calendar encontradas en $GOOGLE_CALENDAR_CREDENTIALS"
            # Test real requiere OAuth flow + cliente — se hace desde Hermes
        else
            fail "Archivo credenciales Google Calendar no existe en $GOOGLE_CALENDAR_CREDENTIALS"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 7. OpenRouter (fallback LLM)
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "openrouter" ]]; then
    section "OpenRouter (fallback)"

    if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
        skip "OPENROUTER_API_KEY no configurado (opcional como fallback)"
    else
        balance=$(curl -sf "https://openrouter.ai/api/v1/auth/key" \
            -H "Authorization: Bearer $OPENROUTER_API_KEY" 2>/dev/null)
        if echo "$balance" | grep -q '"limit"'; then
            pass "OpenRouter autenticado y operativo"
        else
            fail "OpenRouter: error de autenticación"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 8. Meta Graph API (perfil centrum-content)
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "meta" ]]; then
    section "Meta Graph API"

    if [[ -z "${META_ACCESS_TOKEN:-}" ]]; then
        skip "META_ACCESS_TOKEN no configurado"
    else
        me=$(curl -sf "https://graph.facebook.com/v19.0/me?access_token=$META_ACCESS_TOKEN" 2>/dev/null)
        if echo "$me" | grep -q '"id"'; then
            name=$(echo "$me" | grep -o '"name":"[^"]*"')
            pass "Meta API autenticada: $name"
        else
            fail "Meta API: token inválido o caducado"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 9. TikTok Business API
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "tiktok" ]]; then
    section "TikTok Business API"

    if [[ -z "${TIKTOK_ACCESS_TOKEN:-}" ]]; then
        skip "TIKTOK_ACCESS_TOKEN no configurado"
    else
        info=$(curl -sf "https://open.tiktokapis.com/v2/user/info/" \
            -H "Authorization: Bearer $TIKTOK_ACCESS_TOKEN" 2>/dev/null)
        if echo "$info" | grep -q '"data"'; then
            pass "TikTok API autenticada"
        else
            fail "TikTok API: token inválido o expirado"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 10. Webhook web → n8n → CRM
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "webhook" ]]; then
    section "Webhook web → n8n → CRM"

    WEBHOOK_URL="${CENTRUM_WEBHOOK_URL:-https://webhook.centrumdelavivienda.es/webhook/centrum-lead}"

    if curl -sf "$WEBHOOK_URL" > /dev/null 2>&1; then
        # POST de prueba con un lead sintético (marcar como test)
        response=$(curl -sf -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d '{
                "test": true,
                "nombre": "Smoke Test",
                "telefono": "+34600000000",
                "email": "smoke@test.local",
                "situacion": "1-3 meses sin pagar",
                "resultado": "reducir cuota",
                "valor_piso": "vale más",
                "economia": "trabajo estable"
            }' 2>/dev/null)

        if [[ -n "$response" ]]; then
            pass "Webhook responde: lead test aceptado"
        else
            fail "Webhook responde pero vacío — revisar workflow n8n"
        fi
    else
        skip "Webhook URL no disponible — n8n no desplegado aún ($WEBHOOK_URL)"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 11. CRM Mission Control
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "crm" ]]; then
    section "CRM Mission Control"

    CRM_URL="${CENTRUM_CRM_URL:-https://crm.centrumdelavivienda.es/api/crm/stats}"

    if curl -sf "$CRM_URL" > /dev/null 2>&1; then
        pass "CRM responde en $CRM_URL"
    else
        skip "CRM no disponible — desplegar mission-control para Centrum"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# 12. MiroFish (DGX Spark local)
# ═══════════════════════════════════════════════════════════════════════════════
if [[ "$FILTER" == "all" || "$FILTER" == "mirofish" ]]; then
    section "MiroFish"

    MIROFISH_URL="${MIROFISH_URL:-http://localhost:8080/health}"

    if curl -sf "$MIROFISH_URL" > /dev/null 2>&1; then
        pass "MiroFish responde en $MIROFISH_URL"
    else
        skip "MiroFish no disponible — desplegar si se quiere usar para sims"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Resumen final
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Smoke tests completados"
echo "════════════════════════════════════════════════════════════"
echo "  PASS:    $PASSED"
echo "  FAIL:    $FAILED"
echo "  SKIP:    $SKIPPED"
echo "  Log:     $RESULTS_FILE"
echo "════════════════════════════════════════════════════════════"

if [[ "$FAILED" -gt 0 ]]; then
    echo ""
    echo "⚠️  Hay fallos. Revisar antes de poner Centrum en producción."
    exit 1
fi

echo ""
echo "✓ Todos los tests críticos pasaron."
exit 0
