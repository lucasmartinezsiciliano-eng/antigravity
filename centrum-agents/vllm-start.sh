#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# CENTRUM — Arranque vLLM en DGX Spark (3 instancias Gemma 4)
# ═══════════════════════════════════════════════════════════════════════════════
# Ejecutar una vez al arrancar el DGX Spark.
# Añadir al crontab: @reboot sleep 30 && bash /root/centrum-agents/vllm-start.sh
#
# MEMORIA ESTIMADA (los 3 juntos):
#   Nano  gemma-4-E4B-it      →  ~30 GB  (20 agentes: routing, notif, guardar datos)
#   Pro   gemma-4-26B-A4B-it  →  ~52 GB  (43 agentes: contenido, coord, seguimiento)
#   Max   gemma-4-31B-it      →  ~62 GB  (25 agentes: legal, análisis, estrategia)
#   ─────────────────────────────────────
#   TOTAL                        ~144 GB  → No caben los 3 juntos en 128 GB
#
# ESTRATEGIA: Nano + Pro siempre cargados (~82 GB). Max se carga on-demand
#   cuando el orquestador activa Bloque 3 (análisis) o Bloque 6 (soluciones).
#   El DGX Spark tiene NVMe rápido: swap de 31B en ~15-20s.
#
#   Para cargar Max: bash /root/centrum-agents/vllm-load-max.sh
#   Para liberar Max: kill $(cat /tmp/vllm-max.pid)
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

LOG_DIR="/var/log/vllm"
mkdir -p "$LOG_DIR"

echo "Starting Centrum vLLM stack (Nano + Pro always-on)..."

# ─────────────────────────────────────────────────────────────────────────────
# NANO — gemma-4-E4B-it → puerto 8001  (~30 GB)
# Routing, clasificación, notificaciones, guardar datos
# ─────────────────────────────────────────────────────────────────────────────
echo "[Nano] Launching gemma-4-E4B-it on port 8001..."
nohup python3 -m vllm.entrypoints.openai.api_server \
    --model "google/gemma-4-E4B-it" \
    --port 8001 \
    --host 0.0.0.0 \
    --dtype bfloat16 \
    --max-model-len 16384 \
    --gpu-memory-utilization 0.25 \
    --served-model-name "gemma-4-E4B-it" \
    > "$LOG_DIR/nano-e4b.log" 2>&1 &
echo "  PID: $!" && echo $! > /tmp/vllm-nano.pid

# ─────────────────────────────────────────────────────────────────────────────
# PRO — gemma-4-26B-A4B-it → puerto 8002  (~52 GB)
# Contenido, coordinación, seguimiento, resúmenes
# MoE: 26B params totales, 4B activos en inferencia → rápido a pesar del tamaño
# ─────────────────────────────────────────────────────────────────────────────
echo "[Pro] Launching gemma-4-26B-A4B-it on port 8002..."
nohup python3 -m vllm.entrypoints.openai.api_server \
    --model "google/gemma-4-26B-A4B-it" \
    --port 8002 \
    --host 0.0.0.0 \
    --dtype bfloat16 \
    --max-model-len 32768 \
    --gpu-memory-utilization 0.42 \
    --served-model-name "gemma-4-26B-A4B-it" \
    > "$LOG_DIR/pro-26b.log" 2>&1 &
echo "  PID: $!" && echo $! > /tmp/vllm-pro.pid

# ─────────────────────────────────────────────────────────────────────────────
# Esperar a que Nano + Pro respondan (max 180s)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "Waiting for Nano and Pro to come online..."
for port in 8001 8002; do
    timeout=180
    elapsed=0
    while ! curl -s "http://localhost:$port/health" > /dev/null 2>&1; do
        sleep 3
        elapsed=$((elapsed+3))
        if [[ $elapsed -ge $timeout ]]; then
            echo "  [TIMEOUT] Port $port — check $LOG_DIR"
            break
        fi
    done
    echo "  [OK] Port $port ready (${elapsed}s)"
done

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Centrum vLLM stack ready"
echo "  Nano  (E4B  ~30GB) → http://localhost:8001"
echo "  Pro   (26B  ~52GB) → http://localhost:8002"
echo "  Max   (31B  ~62GB) → carga on-demand con vllm-load-max.sh"
echo "═══════════════════════════════════════════════════"
