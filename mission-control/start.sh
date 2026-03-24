#!/bin/bash
# Antigravity Mission Control — Startup script
# Corre esto desde WSL2 o PowerShell con node

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "⚡ Antigravity Mission Control"
echo "================================"

# Instalar dependencias si faltan
if [ ! -d "node_modules" ]; then
  echo "📦 Instalando dependencias..."
  npm install
fi

echo "🚀 Arrancando servidor en http://localhost:3333"
echo "   Ctrl+C para detener"
echo ""

node server.js
