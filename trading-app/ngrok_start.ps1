# ── ngrok_start.ps1 ───────────────────────────────────────────────────────────
# Expone el webhook local a internet para recibir alertas de TradingView.
#
# USO:
#   1. Ejecutar desde PowerShell:
#        .\ngrok_start.ps1
#   2. Copiar la URL pública que aparece (ej: https://xxxx.ngrok-free.app)
#   3. En TradingView alert → Webhook URL: https://xxxx.ngrok-free.app/webhook
#
# IMPORTANTE: La URL cambia cada vez que reinicias ngrok (plan gratuito).
# Si quieres URL fija → ngrok.com → plan Basic ($10/mes) o usar el VPS.

Write-Host ""
Write-Host "=== NGROK — ANTIGRAVITY Webhook Tunnel ===" -ForegroundColor Cyan
Write-Host ""

# Verificar que el bot está corriendo
try {
    $status = Invoke-WebRequest -Uri "http://localhost:8000/status" -UseBasicParsing -TimeoutSec 3
    $data = $status.Content | ConvertFrom-Json
    Write-Host "  Bot:  ONLINE (v$($data.version))" -ForegroundColor Green
} catch {
    Write-Host "  Bot:  OFFLINE - Arrancar primero: python beta_local.py" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Presiona cualquier tecla para salir..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Token de ngrok (opcional, para dominio fijo)
# Para añadir tu token: ngrok config add-authtoken TU_TOKEN
# Regístrate gratis en https://ngrok.com y copia el token del dashboard

Write-Host ""
Write-Host "  Abriendo tunnel ngrok en puerto 8000..." -ForegroundColor Yellow
Write-Host "  Copia la URL 'Forwarding' y úsala en TradingView." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Dashboard ngrok: http://localhost:4040" -ForegroundColor Gray
Write-Host ""
Write-Host "  Ctrl+C para cerrar el tunnel." -ForegroundColor Gray
Write-Host ""

# Abrir dashboard ngrok en el navegador después de 3s
Start-Job {
    Start-Sleep 3
    Start-Process "http://localhost:4040"
} | Out-Null

# Iniciar ngrok
ngrok http 8000 --log=stdout
