#!/bin/bash
# oracle-anti-idle.sh — Mantiene Oracle Free Tier activo
# Instalar en el servidor Oracle una vez esté accesible:
#
#   chmod +x oracle-anti-idle.sh
#   sudo cp oracle-anti-idle.sh /usr/local/bin/oracle-anti-idle.sh
#   sudo cp oracle-anti-idle.service /etc/systemd/system/
#   sudo cp oracle-anti-idle.timer   /etc/systemd/system/
#   sudo systemctl daemon-reload
#   sudo systemctl enable --now oracle-anti-idle.timer

LOG="/var/log/oracle-anti-idle.log"

echo "[$(date -Iseconds)] Anti-idle ping" >> "$LOG"

# 1. CPU burst de 15 segundos (~5-10% usage) — suficiente para Oracle
timeout 15 bash -c 'while true; do :; done' &
CPU_PID=$!
sleep 15
kill "$CPU_PID" 2>/dev/null

# 2. Pings de red a servicios propios
curl -sf --max-time 5 http://localhost:9999/health -o /dev/null && echo "[$(date -Iseconds)] CRM OK" >> "$LOG"
curl -sf --max-time 5 http://localhost:5678/healthz -o /dev/null && echo "[$(date -Iseconds)] n8n OK" >> "$LOG"

# 3. Escribe en disco (evita suspensión de storage)
touch /tmp/.oracle-keepalive

echo "[$(date -Iseconds)] Done" >> "$LOG"

# Rotar log si > 1MB
if [ $(stat -c%s "$LOG" 2>/dev/null || echo 0) -gt 1048576 ]; then
    mv "$LOG" "${LOG}.old"
fi
