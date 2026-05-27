#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# CENTRUM — Carga/descarga MAX (Qwen 3.6 35B-A3B FP8) on-demand
# ═══════════════════════════════════════════════════════════════════════════════
# Reemplaza Gemma 4 31B dense (2026-05-27):
#   Gemma 4 31B BF16 → 7 tok/s en DGX Spark GB10 (memory-bandwidth bound, dense)
#   Qwen 3.6 35B-A3B FP8 → 28-30 tok/s single, 156 tok/s @c=32 (MoE, parser maduro)
#   TAU2 tool use: 81.2 vs 76.9 | Agentic-coding: 70.6 vs 41.6
#   Memoria: ~20-35 GB FP8 vs ~62 GB BF16 → cabe con holgura
#
# El orquestador llama a este script antes de activar agentes Max:
#   bash /root/centrum-agents/vllm-load-max.sh load
#   bash /root/centrum-agents/vllm-load-max.sh unload
#
# NOTA — SIEMPRE-ON FUTURO: con Pro migrado a NVFP4 (~16.5 GB en lugar de ~52 GB),
# los tres modelos cabrían siempre cargados (~23 + ~17 + ~35 = ~75 GB de 128 GB).
# Pendiente de validar NVFP4 + --moe-backend marlin en Pro antes de ese cambio.
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

LOG_DIR="/var/log/vllm"
PID_FILE="/tmp/vllm-max.pid"
ACTION="${1:-load}"

# VERIFICAR antes del primer deploy:
# - Confirmar model ID exacto en huggingface.co/Qwen (puede variar en snapshots)
# - Hacer: huggingface-cli download Qwen/Qwen3.6-35B-A3B-Instruct-FP8 --local-dir /models/qwen3.6-35b
MODEL_ID="Qwen/Qwen3.6-35B-A3B-Instruct-FP8"
SERVED_NAME="qwen3.6-35b-a3b"

case "$ACTION" in
  load)
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "[Max] Ya está cargado (PID $(cat $PID_FILE))"
        exit 0
    fi

    echo "[Max] Cargando ${MODEL_ID} en puerto 8003..."
    nohup python3 -m vllm.entrypoints.openai.api_server \
        --model "${MODEL_ID}" \
        --port 8003 \
        --host 0.0.0.0 \
        --dtype auto \
        --quantization fp8 \
        --max-model-len 65536 \
        --gpu-memory-utilization 0.28 \
        --enable-auto-tool-choice \
        --tool-call-parser hermes \
        --served-model-name "${SERVED_NAME}" \
        > "$LOG_DIR/max-qwen3.6.log" 2>&1 &
    # tool-call-parser hermes: Qwen 3 usa formato XML Hermes nativamente.
    # Parser maduro en vLLM, sin los bugs activos del parser gemma4 (#39392 etc.)
    # dtype auto: detecta FP8 del modelo precomprimido automáticamente
    # gpu-memory-utilization 0.28 = ~36 GB (modelo ~20-35 GB + KV cache restante)
    echo $! > "$PID_FILE"
    echo "[Max] PID: $(cat $PID_FILE) — esperando..."

    timeout=180; elapsed=0
    while ! curl -s "http://localhost:8003/health" > /dev/null 2>&1; do
        sleep 3; elapsed=$((elapsed+3))
        [[ $elapsed -ge $timeout ]] && echo "[Max] TIMEOUT — ver $LOG_DIR/max-qwen3.6.log" && exit 1
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
