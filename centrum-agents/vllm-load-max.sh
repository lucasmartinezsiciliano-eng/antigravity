#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# CENTRUM — Carga/descarga MAX (gemma-4-31B-it) on-demand
# ═══════════════════════════════════════════════════════════════════════════════
# El orquestador llama a este script antes de activar agentes Max:
#   bash /root/centrum-agents/vllm-load-max.sh load
#   bash /root/centrum-agents/vllm-load-max.sh unload
#
# También se puede usar manualmente cuando llega un caso nuevo.
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

LOG_DIR="/var/log/vllm"
PID_FILE="/tmp/vllm-max.pid"
ACTION="${1:-load}"

case "$ACTION" in
  load)
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "[Max] Ya está cargado (PID $(cat $PID_FILE))"
        exit 0
    fi

    echo "[Max] Cargando gemma-4-31B-it en puerto 8003..."
    nohup python3 -m vllm.entrypoints.openai.api_server \
        --model "google/gemma-4-31B-it" \
        --port 8003 \
        --host 0.0.0.0 \
        --dtype bfloat16 \
        --max-model-len 32768 \
        --gpu-memory-utilization 0.50 \
        --served-model-name "gemma-4-31B-it" \
        > "$LOG_DIR/max-31b.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "[Max] PID: $(cat $PID_FILE) — esperando..."

    timeout=180; elapsed=0
    while ! curl -s "http://localhost:8003/health" > /dev/null 2>&1; do
        sleep 3; elapsed=$((elapsed+3))
        [[ $elapsed -ge $timeout ]] && echo "[Max] TIMEOUT" && exit 1
    done
    echo "[Max] Listo en ${elapsed}s → http://localhost:8003"
    ;;

  unload)
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null && echo "[Max] Descargado (PID $PID)" || echo "[Max] Ya estaba parado"
        rm -f "$PID_FILE"
    else
        echo "[Max] No estaba cargado"
    fi
    ;;

  *)
    echo "Uso: $0 [load|unload]"
    exit 1
    ;;
esac
