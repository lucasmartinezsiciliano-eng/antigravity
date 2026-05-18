#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# VISAI Load Test — Comandos rápidos
#
# Uso: bash run.sh <modo> [host]
#
# Modos disponibles:
#   smoke       5 usuarios, 30 seg — verifica que Railway responde
#   read        50 usuarios leyendo — test de lectura (seguro en prod)
#   flow        20 usuarios haciendo análisis — requiere DEV_SKIP_PAYMENT=True
#   stress      100 usuarios mixtos — test de carga real
#   headless    Test automático sin UI (para CI)
#   clean       Abre psql para limpiar datos de test
#
# Ejemplos:
#   bash run.sh smoke https://visai-backend.up.railway.app
#   bash run.sh read  https://visai-backend.up.railway.app
# ─────────────────────────────────────────────────────────────────────────────

set -e

MODE="${1:-smoke}"
HOST="${2:-http://localhost:8000}"
DIR="$(cd "$(dirname "$0")" && pwd)"
LOCUST="locust -f $DIR/locustfile.py --host $HOST"

echo "═══════════════════════════════════════════════════"
echo "  VISAI Load Test"
echo "  Modo : $MODE"
echo "  Host : $HOST"
echo "═══════════════════════════════════════════════════"

case "$MODE" in

  smoke)
    # Verificación rápida: 5 usuarios, 30 seg, sin UI
    echo "[smoke] 5 usuarios × 30 seg — verifica que Railway responde"
    $LOCUST \
      --users 5 \
      --spawn-rate 1 \
      --run-time 30s \
      --headless \
      --only-summary \
      --html "$DIR/reports/smoke_$(date +%Y%m%d_%H%M).html"
    ;;

  read)
    # Carga de lectura: seguro en prod, no crea registros
    echo "[read] 50 usuarios leyendo — abre http://localhost:8089"
    $LOCUST \
      --users 50 \
      --spawn-rate 5 \
      --class-picker
    ;;

  flow)
    # Flujo completo de análisis (sin fotos — no gasta LLM)
    # El backend DEBE tener DEV_SKIP_PAYMENT=True
    echo "[flow] 20 usuarios — flujo initiate→consent (sin LLM)"
    $LOCUST \
      --users 20 \
      --spawn-rate 2 \
      --class-picker
    ;;

  flow-with-photos)
    # Flujo completo CON fotos — gasta créditos del LLM
    echo "[flow-with-photos] ⚠️  Llama al LLM real"
    INCLUDE_PHOTO_UPLOAD=true $LOCUST \
      --users 5 \
      --spawn-rate 1 \
      --class-picker
    ;;

  stress)
    # Test de estrés: 100 usuarios mixtos
    echo "[stress] 100 usuarios × UI — abre http://localhost:8089"
    $LOCUST \
      --users 100 \
      --spawn-rate 10
    ;;

  headless)
    # Sin UI — útil para CI o correr desde terminal
    # Genera HTML report
    mkdir -p "$DIR/reports"
    echo "[headless] 30 usuarios × 2 min — generando report"
    $LOCUST \
      --users 30 \
      --spawn-rate 3 \
      --run-time 2m \
      --headless \
      --html "$DIR/reports/report_$(date +%Y%m%d_%H%M).html" \
      --csv "$DIR/reports/csv_$(date +%Y%m%d_%H%M)"
    echo ""
    echo "Reports guardados en $DIR/reports/"
    ;;

  *)
    echo "Modo desconocido: $MODE"
    echo "Modos: smoke | read | flow | flow-with-photos | stress | headless"
    exit 1
    ;;

esac
