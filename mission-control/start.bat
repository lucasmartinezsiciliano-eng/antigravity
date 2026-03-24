@echo off
cd /d "%~dp0"
echo.
echo  ⚡ Antigravity Mission Control
echo  ================================

IF NOT EXIST node_modules (
  echo  📦 Instalando dependencias...
  npm install
)

echo  🚀 http://localhost:3333
echo  Ctrl+C para detener
echo.
node server.js
pause
