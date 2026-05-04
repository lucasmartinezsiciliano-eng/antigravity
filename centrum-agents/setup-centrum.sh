#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# CENTRUM DE LA VIVIENDA — Script de despliegue en Nvidia DGX Spark
# ═══════════════════════════════════════════════════════════════════════════════
# Ejecutar en el DGX Spark como root:
#   scp -r centrum-agents/ dgxspark:/tmp/
#   ssh root@dgxspark "bash /tmp/centrum-agents/setup-centrum.sh"
#
# Prerequisitos:
#   - OpenClaw instalado y agente "iris" ya funcionando (directorio plantilla)
#   - vLLM corriendo en los 4 puertos (ver vllm-start.sh abajo)
#   - IDENTITY.md files copiados junto al script (en /tmp/centrum-agents/)
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

OPENCLAW_AGENTS="/root/.openclaw/agents"
OPENCLAW_WORKSPACE="/root/.openclaw"
TEMPLATE_AGENT="iris"                        # Agente base para copiar config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/centrum-setup.log"

# ── Colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC}  $1" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"; }
fail() { echo -e "${RED}[FAIL]${NC} $1" | tee -a "$LOG_FILE"; exit 1; }

# ── Validaciones previas ─────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════" | tee "$LOG_FILE"
echo "  CENTRUM — Deploy 89 agentes en DGX Spark"         | tee -a "$LOG_FILE"
echo "  $(date)"                                           | tee -a "$LOG_FILE"
echo "═══════════════════════════════════════════════════" | tee -a "$LOG_FILE"

[[ -d "$OPENCLAW_AGENTS/$TEMPLATE_AGENT" ]] || fail "Agente plantilla '$TEMPLATE_AGENT' no encontrado en $OPENCLAW_AGENTS"
[[ -f "$OPENCLAW_AGENTS/$TEMPLATE_AGENT/agent/config.json" ]] || fail "config.json no encontrado en plantilla iris"

# Verificar que los 4 puertos vLLM están activos
for port in 8001 8002 8003 8004; do
    curl -s "http://localhost:$port/health" > /dev/null 2>&1 \
        && ok "vLLM puerto $port: activo" \
        || warn "vLLM puerto $port: NO responde — verificar antes de usar agentes T$(( (port-8000) ))"
done

# ── Mapa tier → vLLM (puerto + model id) ────────────────────────────────────
# Nano: gemma-4-E4B-it      → puerto 8001  (~30 GB, siempre cargado)
# Pro:  gemma-4-26B-A4B-it  → puerto 8002  (~52 GB, siempre cargado)
# Max:  gemma-4-31B-it      → puerto 8003  (~62 GB, on-demand con vllm-load-max.sh)

declare -A AGENT_TIER=(
    # ── ORQUESTADOR ──────────────────────────────────────────────────────────
    [centrum-orchestrator]="Max"

    # ── BLOQUE 0: Inteligencia de Mercado ────────────────────────────────────
    [avatar-researcher]="Pro"
    [competitor-spy]="Pro"
    [law-tracker]="Max"
    [market-watcher]="Pro"
    [news-scanner]="Pro"
    [trend-exploiter]="Nano"

    # ── BLOQUE 1: Captación y Contenido ─────────────────────────────────────
    [ads-manager]="Pro"
    [avatar-creator]="Pro"
    [comment-scraper]="Pro"
    [content-director]="Pro"
    [content-repurposer]="Pro"
    [content-scheduler]="Nano"
    [freepik-specialist]="Pro"
    [google-ad-writer]="Pro"
    [google-keyword-researcher]="Nano"
    [google-negative-manager]="Nano"
    [meta-audience-builder]="Nano"
    [meta-copywriter]="Max"
    [meta-headline-tester]="Pro"
    [social-auto-responder]="Pro"
    [tiktok-cta-writer]="Pro"
    [tiktok-hook-specialist]="Max"
    [tiktok-scriptwriter]="T4"
    [video-editor]="T2"

    # ── BLOQUE 2: Lead y Conversión ──────────────────────────────────────────
    [auto-responder]="Pro"
    [conversion-director]="Pro"
    [conversion-optimizer]="Pro"
    [form-analyzer]="Pro"
    [lead-classifier]="Nano"
    [lead-notifier]="Nano"
    [lead-router]="Nano"
    [lead-scorer]="Pro"

    # ── BLOQUE 3: Intake y Cualificación ─────────────────────────────────────
    [call-prep]="Max"
    [call-transcriber]="Pro"
    [ficha-builder]="Pro"
    [ficha-saver]="Nano"
    [intake-director]="Pro"
    [missing-data-detector]="Nano"
    [question-suggester]="Max"
    [solution-previewer]="Max"

    # ── BLOQUE 4: Documentación ───────────────────────────────────────────────
    [doc-checklist-generator]="Max"
    [doc-director]="Pro"
    [doc-organizer]="Nano"
    [doc-reminder]="Nano"
    [doc-requester]="Pro"
    [doc-validator]="Pro"
    [rgpd-guardian]="Pro"

    # ── BLOQUE 5: Análisis del Caso ───────────────────────────────────────────
    [analysis-director]="Pro"
    [bank-behavior-analyst]="Max"
    [case-summarizer]="Max"
    [clause-detector]="Max"
    [debt-analyzer]="Max"
    [expedient-builder]="Pro"
    [legal-risk-assessor]="Max"
    [property-valuator]="Pro"

    # ── BLOQUE 6: Estrategia y Soluciones ────────────────────────────────────
    [case-improver]="Max"
    [family-mortgage-evaluator]="Max"
    [legal-defense-evaluator]="Max"
    [negotiation-evaluator]="Max"
    [recommendation-agent]="Max"
    [report-writer]="Max"
    [sale-evaluator]="Max"
    [solution-matcher]="Max"
    [solutions-director]="Pro"
    [time-gain-evaluator]="Pro"

    # ── BLOQUE 7: Comunicación ────────────────────────────────────────────────
    [comms-director]="Pro"
    [email-sender]="Nano"
    [email-writer]="Max"
    [legal-language-checker]="Max"
    [quality-checker]="Pro"
    [tone-checker]="Pro"
    [whatsapp-sender]="Nano"
    [whatsapp-writer]="Max"

    # ── BLOQUE 8: Seguimiento ─────────────────────────────────────────────────
    [alert-generator]="Nano"
    [case-closer]="Pro"
    [client-updater]="Pro"
    [feedback-collector]="Pro"
    [followup-director]="Pro"
    [milestone-detector]="Pro"
    [timeline-tracker]="Nano"

    # ── BLOQUE 9: Analytics y Reporting ──────────────────────────────────────
    [channel-performance]="Nano"
    [conversion-tracker]="Nano"
    [feedback-analyzer]="Pro"
    [ops-director]="Pro"
    [pipeline-dashboard]="Nano"
    [revenue-tracker]="Nano"
    [weekly-reporter]="Pro"
)

# ── Mapa tier → config vLLM ──────────────────────────────────────────────────
declare -A TIER_PORT=([Nano]="8001" [Pro]="8002" [Max]="8003")
declare -A TIER_MODEL=(
    [Nano]="google/gemma-4-E4B-it"
    [Pro]="google/gemma-4-26B-A4B-it"
    [Max]="google/gemma-4-31B-it"
)

# ── Mapa agente → ruta relativa IDENTITY.md (en $SCRIPT_DIR) ────────────────
declare -A AGENT_IDENTITY=(
    [centrum-orchestrator]="orquestador/centrum-orchestrator/IDENTITY.md"
    [avatar-researcher]="bloque-0/avatar-researcher/IDENTITY.md"
    [competitor-spy]="bloque-0/competitor-spy/IDENTITY.md"
    [law-tracker]="bloque-0/law-tracker/IDENTITY.md"
    [market-watcher]="bloque-0/market-watcher/IDENTITY.md"
    [news-scanner]="bloque-0/news-scanner/IDENTITY.md"
    [trend-exploiter]="bloque-0/trend-exploiter/IDENTITY.md"
    [ads-manager]="bloque-1/ads-manager/IDENTITY.md"
    [avatar-creator]="bloque-1/avatar-creator/IDENTITY.md"
    [comment-scraper]="bloque-1/comment-scraper/IDENTITY.md"
    [content-director]="bloque-1/content-director/IDENTITY.md"
    [content-repurposer]="bloque-1/content-repurposer/IDENTITY.md"
    [content-scheduler]="bloque-1/content-scheduler/IDENTITY.md"
    [freepik-specialist]="bloque-1/freepik-specialist/IDENTITY.md"
    [google-ad-writer]="bloque-1/google-ad-writer/IDENTITY.md"
    [google-keyword-researcher]="bloque-1/google-keyword-researcher/IDENTITY.md"
    [google-negative-manager]="bloque-1/google-negative-manager/IDENTITY.md"
    [meta-audience-builder]="bloque-1/meta-audience-builder/IDENTITY.md"
    [meta-copywriter]="bloque-1/meta-copywriter/IDENTITY.md"
    [meta-headline-tester]="bloque-1/meta-headline-tester/IDENTITY.md"
    [social-auto-responder]="bloque-1/social-auto-responder/IDENTITY.md"
    [tiktok-cta-writer]="bloque-1/tiktok-cta-writer/IDENTITY.md"
    [tiktok-hook-specialist]="bloque-1/tiktok-hook-specialist/IDENTITY.md"
    [tiktok-scriptwriter]="bloque-1/tiktok-scriptwriter/IDENTITY.md"
    [video-editor]="bloque-1/video-editor/IDENTITY.md"
    [auto-responder]="bloque-2/auto-responder/IDENTITY.md"
    [conversion-director]="bloque-2/conversion-director/IDENTITY.md"
    [conversion-optimizer]="bloque-2/conversion-optimizer/IDENTITY.md"
    [form-analyzer]="bloque-2/form-analyzer/IDENTITY.md"
    [lead-classifier]="bloque-2/lead-classifier/IDENTITY.md"
    [lead-notifier]="bloque-2/lead-notifier/IDENTITY.md"
    [lead-router]="bloque-2/lead-router/IDENTITY.md"
    [lead-scorer]="bloque-2/lead-scorer/IDENTITY.md"
    [call-prep]="bloque-3/call-prep/IDENTITY.md"
    [call-transcriber]="bloque-3/call-transcriber/IDENTITY.md"
    [ficha-builder]="bloque-3/ficha-builder/IDENTITY.md"
    [ficha-saver]="bloque-3/ficha-saver/IDENTITY.md"
    [intake-director]="bloque-3/intake-director/IDENTITY.md"
    [missing-data-detector]="bloque-3/missing-data-detector/IDENTITY.md"
    [question-suggester]="bloque-3/question-suggester/IDENTITY.md"
    [solution-previewer]="bloque-3/solution-previewer/IDENTITY.md"
    [doc-checklist-generator]="bloque-4/doc-checklist-generator/IDENTITY.md"
    [doc-director]="bloque-4/doc-director/IDENTITY.md"
    [doc-organizer]="bloque-4/doc-organizer/IDENTITY.md"
    [doc-reminder]="bloque-4/doc-reminder/IDENTITY.md"
    [doc-requester]="bloque-4/doc-requester/IDENTITY.md"
    [doc-validator]="bloque-4/doc-validator/IDENTITY.md"
    [rgpd-guardian]="bloque-4/rgpd-guardian/IDENTITY.md"
    [analysis-director]="bloque-5/analysis-director/IDENTITY.md"
    [bank-behavior-analyst]="bloque-5/bank-behavior-analyst/IDENTITY.md"
    [case-summarizer]="bloque-5/case-summarizer/IDENTITY.md"
    [clause-detector]="bloque-5/clause-detector/IDENTITY.md"
    [debt-analyzer]="bloque-5/debt-analyzer/IDENTITY.md"
    [expedient-builder]="bloque-5/expedient-builder/IDENTITY.md"
    [legal-risk-assessor]="bloque-5/legal-risk-assessor/IDENTITY.md"
    [property-valuator]="bloque-5/property-valuator/IDENTITY.md"
    [case-improver]="bloque-6/case-improver/IDENTITY.md"
    [family-mortgage-evaluator]="bloque-6/family-mortgage-evaluator/IDENTITY.md"
    [legal-defense-evaluator]="bloque-6/legal-defense-evaluator/IDENTITY.md"
    [negotiation-evaluator]="bloque-6/negotiation-evaluator/IDENTITY.md"
    [recommendation-agent]="bloque-6/recommendation-agent/IDENTITY.md"
    [report-writer]="bloque-6/report-writer/IDENTITY.md"
    [sale-evaluator]="bloque-6/sale-evaluator/IDENTITY.md"
    [solution-matcher]="bloque-6/solution-matcher/IDENTITY.md"
    [solutions-director]="bloque-6/solutions-director/IDENTITY.md"
    [time-gain-evaluator]="bloque-6/time-gain-evaluator/IDENTITY.md"
    [comms-director]="bloque-7/comms-director/IDENTITY.md"
    [email-sender]="bloque-7/email-sender/IDENTITY.md"
    [email-writer]="bloque-7/email-writer/IDENTITY.md"
    [legal-language-checker]="bloque-7/legal-language-checker/IDENTITY.md"
    [quality-checker]="bloque-7/quality-checker/IDENTITY.md"
    [tone-checker]="bloque-7/tone-checker/IDENTITY.md"
    [whatsapp-sender]="bloque-7/whatsapp-sender/IDENTITY.md"
    [whatsapp-writer]="bloque-7/whatsapp-writer/IDENTITY.md"
    [alert-generator]="bloque-8/alert-generator/IDENTITY.md"
    [case-closer]="bloque-8/case-closer/IDENTITY.md"
    [client-updater]="bloque-8/client-updater/IDENTITY.md"
    [feedback-collector]="bloque-8/feedback-collector/IDENTITY.md"
    [followup-director]="bloque-8/followup-director/IDENTITY.md"
    [milestone-detector]="bloque-8/milestone-detector/IDENTITY.md"
    [timeline-tracker]="bloque-8/timeline-tracker/IDENTITY.md"
    [channel-performance]="bloque-9/channel-performance/IDENTITY.md"
    [conversion-tracker]="bloque-9/conversion-tracker/IDENTITY.md"
    [feedback-analyzer]="bloque-9/feedback-analyzer/IDENTITY.md"
    [ops-director]="bloque-9/ops-director/IDENTITY.md"
    [pipeline-dashboard]="bloque-9/pipeline-dashboard/IDENTITY.md"
    [revenue-tracker]="bloque-9/revenue-tracker/IDENTITY.md"
    [weekly-reporter]="bloque-9/weekly-reporter/IDENTITY.md"
)

# ── Instalar agentes ──────────────────────────────────────────────────────────
CREATED=0; SKIPPED=0; ERRORS=0

for agent in "${!AGENT_TIER[@]}"; do
    tier="${AGENT_TIER[$agent]}"
    port="${TIER_PORT[$tier]}"
    model="${TIER_MODEL[$tier]}"
    agent_dir="$OPENCLAW_AGENTS/$agent"
    workspace_dir="$OPENCLAW_WORKSPACE/workspace-$agent"
    identity_src="$SCRIPT_DIR/${AGENT_IDENTITY[$agent]}"

    # Saltar si ya existe (safe — no sobreescribir agentes activos)
    if [[ -d "$agent_dir" ]]; then
        warn "Ya existe: $agent — saltando"
        ((SKIPPED++))
        continue
    fi

    # Crear estructura de directorios
    mkdir -p "$agent_dir/agent" "$agent_dir/sessions" "$workspace_dir"

    # Copiar config JSON desde plantilla iris
    cp "$OPENCLAW_AGENTS/$TEMPLATE_AGENT/agent/config.json" "$agent_dir/agent/config.json"

    # Actualizar base_url y model en el config JSON (usa python3 para edición segura)
    python3 - <<PYEOF
import json, sys

config_path = "$agent_dir/agent/config.json"
with open(config_path, "r") as f:
    cfg = json.load(f)

# Ajustar endpoint vLLM para este tier
cfg["model"] = "$model"
cfg["base_url"] = "http://localhost:$port/v1"
cfg["api_key"] = "local"          # vLLM no requiere key real
cfg["name"] = "$agent"

# Si tiene system_prompt, limpiarlo (viene de iris)
if "system_prompt" in cfg:
    cfg["system_prompt"] = ""

with open(config_path, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
PYEOF

    # Copiar IDENTITY.md al workspace
    if [[ -f "$identity_src" ]]; then
        cp "$identity_src" "$workspace_dir/IDENTITY.md"
        ok "[$tier] $agent"
    else
        warn "[$tier] $agent — IDENTITY.md no encontrado: $identity_src"
        ((ERRORS++))
        continue
    fi

    ((CREATED++))
done

# ── Resumen ───────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "  Creados:  $CREATED agentes"                        | tee -a "$LOG_FILE"
echo "  Saltados: $SKIPPED (ya existían)"                  | tee -a "$LOG_FILE"
echo "  Errores:  $ERRORS"                                 | tee -a "$LOG_FILE"
echo "═══════════════════════════════════════════════════" | tee -a "$LOG_FILE"

if [[ $ERRORS -gt 0 ]]; then
    warn "Hay errores. Revisar $LOG_FILE antes de continuar."
    exit 1
fi

# ── Reiniciar gateway OpenClaw ────────────────────────────────────────────────
echo ""
echo "Reiniciando openclaw gateway..."
if command -v openclaw &> /dev/null; then
    openclaw gateway restart && ok "Gateway reiniciado" || fail "Error al reiniciar gateway"
else
    warn "Comando 'openclaw' no encontrado en PATH. Reiniciar manualmente: openclaw gateway restart"
fi

echo ""
ok "Despliegue completado. Log en $LOG_FILE"
