# watchdog-oracle.ps1 — Watchdog local para Oracle Cloud
# Instalar en Windows Task Scheduler para que corra cada 15 min:
#
#   schtasks /create /tn "Oracle Watchdog" /tr "powershell -File C:\path\to\watchdog-oracle.ps1" /sc minute /mo 15 /ru SYSTEM
#
# O abrir Task Scheduler > Create Task > Trigger: cada 15 min > Action: powershell.exe -File <ruta>

# --- CONFIG ---
$TELEGRAM_BOT_TOKEN = "7968364664:AAGKHcZ3GCki2y0sQGpjDgepN-Awm2hIW0o"
$TELEGRAM_CHAT_ID   = "5631114912"   # Chat Lucas

$SERVICES = @(
    @{ Name = "CRM Mission Control"; Url = "https://crm.lukimporta.es/health" },
    @{ Name = "n8n";                 Url = "https://n8n.lukimporta.es/healthz" },
    @{ Name = "OpenClaw";            Url = "https://openclaw.lukimporta.es/health" },
    @{ Name = "Portainer";           Url = "https://portainer.lukimporta.es" }
)

$STATE_FILE = "$env:TEMP\oracle_watchdog_state.json"
$TIMEOUT_SEC = 10

# --- FUNC ---
function Send-TelegramAlert($msg) {
    $body = @{ chat_id = $TELEGRAM_CHAT_ID; text = $msg; parse_mode = "HTML" } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" `
            -Method Post -ContentType "application/json" -Body $body | Out-Null
    } catch {
        Write-Host "Telegram error: $_"
    }
}

function Get-ServiceStatus($url) {
    try {
        $r = Invoke-WebRequest -Uri $url -TimeoutSec $TIMEOUT_SEC -UseBasicParsing -ErrorAction Stop
        return $r.StatusCode -lt 500
    } catch {
        return $false
    }
}

# --- LOAD STATE ---
$state = @{}
if (Test-Path $STATE_FILE) {
    $state = Get-Content $STATE_FILE | ConvertFrom-Json -AsHashtable
}

# --- CHECK ---
$now = Get-Date -Format "yyyy-MM-dd HH:mm"
$anyDown = $false
$alerts = @()

foreach ($svc in $SERVICES) {
    $ok = Get-ServiceStatus $svc.Url
    $key = $svc.Name -replace " ", "_"

    if (-not $ok) {
        $anyDown = $true
        # Solo alerta si no estaba ya down (evita spam)
        if ($state[$key] -ne "DOWN") {
            $alerts += "CAIDO: $($svc.Name)"
        }
        $state[$key] = "DOWN"
    } else {
        # Recuperación: alertar si estaba down
        if ($state[$key] -eq "DOWN") {
            $alerts += "RECUPERADO: $($svc.Name)"
        }
        $state[$key] = "UP"
    }
}

# --- SEND ALERTS ---
if ($alerts.Count -gt 0) {
    $bold_open  = [char]0x003C + "b" + [char]0x003E
    $bold_close = [char]0x003C + "/b" + [char]0x003E
    $ital_open  = [char]0x003C + "i" + [char]0x003E
    $ital_close = [char]0x003C + "/i" + [char]0x003E
    $msg = "${bold_open}Oracle Cloud - $now${bold_close}`n`n" + ($alerts -join "`n")
    if ($anyDown) {
        $msg += "`n`n${ital_open}Consola Oracle: cloud.oracle.com -> eu-madrid-1 -> Compute -> Instances -> Start${ital_close}"
    }
    Send-TelegramAlert $msg
}

# --- SAVE STATE ---
$state | ConvertTo-Json | Set-Content $STATE_FILE

Write-Host "[$now] Check OK - Alerts: $($alerts.Count)"
