# Watchdog del bot IFVG.
# Comprueba que el cockpit responde en :8000 y lo relanza si no.
# Lo usan las dos tareas programadas:
#   IFVG_Bot_Startup   -> con -Force (al iniciar sesion, arranca siempre)
#   IFVG_Bot_Watchdog  -> sin -Force (cada 5 min, solo si esta caido)
#
# Sustituye a watchdog_bot.bat, que fallaba con exit 255 en todas sus
# ejecuciones: el parentesis de "(puerto 8000 activo)" cerraba el bloque else.

param([switch]$Force)

$BotDir  = "C:\Users\Pc2025\Desktop\ANTIGRAVITY\trading-app"
$Python  = "C:\Python314\python.exe"
$Script  = "beta_local.py"
$Port    = 8000
$Health  = "http://localhost:$Port/api/config"
$Log     = Join-Path $BotDir "watchdog.log"

function Write-Log($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $Log -Value $line -Encoding utf8
}

# Rotacion simple: el log del bot crecia sin limite.
foreach ($f in @($Log, (Join-Path $BotDir "bot_output.log"))) {
    if ((Test-Path $f) -and ((Get-Item $f).Length -gt 5MB)) {
        Move-Item $f "$f.1" -Force
    }
}

function Test-BotAlive {
    try {
        Invoke-WebRequest -Uri $Health -TimeoutSec 5 -UseBasicParsing | Out-Null
        return $true
    } catch {
        return $false
    }
}

if ((Test-BotAlive) -and -not $Force) {
    Write-Log "OK - responde en :$Port"
    exit 0
}

if ($Force) { Write-Log "Arranque forzado (startup)." }
else        { Write-Log "NO responde en :$Port - relanzando." }

# Matar solo procesos que esten ESCUCHANDO en el puerto (no conexiones salientes).
$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($l in $listeners) {
    try {
        Stop-Process -Id $l.OwningProcess -Force -ErrorAction Stop
        Write-Log "Matado PID $($l.OwningProcess) que ocupaba :$Port"
    } catch {
        Write-Log "No pude matar PID $($l.OwningProcess): $($_.Exception.Message)"
    }
}

# Esperar a que el puerto quede libre de verdad antes de arrancar: si no,
# el proceso nuevo muere con "10048 address already in use".
$free = $false
foreach ($i in 1..15) {
    if (-not (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)) {
        $free = $true
        break
    }
    Start-Sleep -Seconds 1
}
if (-not $free) {
    Write-Log "ABORT - el puerto :$Port sigue ocupado tras 15s."
    exit 1
}

# UTF-8 para que un print con emoji no mate hilos (crash del 17-jul-2026).
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8       = "1"
# Sin esto Python bufferea al redirigir a fichero y el log queda vacio hasta
# que el proceso muere, justo cuando mas falta hace verlo.
$env:PYTHONUNBUFFERED  = "1"

Start-Process -FilePath $Python `
              -ArgumentList $Script `
              -WorkingDirectory $BotDir `
              -WindowStyle Hidden `
              -RedirectStandardOutput (Join-Path $BotDir "bot_output.log") `
              -RedirectStandardError  (Join-Path $BotDir "bot_error.log")

# Confirmar que ha arrancado de verdad, no solo que se lanzo el proceso.
foreach ($i in 1..30) {
    Start-Sleep -Seconds 2
    if (Test-BotAlive) {
        Write-Log "Arrancado y respondiendo tras $($i*2)s."
        exit 0
    }
}

Write-Log "FALLO - lanzado pero no responde tras 60s. Ver bot_error.log"
exit 1
