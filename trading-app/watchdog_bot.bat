@echo off
REM Watchdog: cada 5 minutos comprueba si el bot sigue vivo.
REM Si no responde en el puerto 8000, lo relanza.
REM Este script corre en bucle como tarea programada (cada 5 min).

set BOT_DIR=C:\Users\Pc2025\Desktop\ANTIGRAVITY\trading-app
set PYTHON=C:\Python314\python.exe
set BOT_SCRIPT=beta_local.py
set PORT=8000
set LOG=%BOT_DIR%\bot_output.log

REM Comprobar si el puerto 8000 está activo
curl -s --max-time 5 http://localhost:%PORT%/api/config >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] Bot no responde — relanzando... >> %LOG%

    REM Matar proceso viejo si existe
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT% "') do (
        taskkill /PID %%a /F >nul 2>&1
    )

    timeout /t 2 /nobreak >nul

    REM Relanzar
    cd /d %BOT_DIR%
    start "" /B /MIN %PYTHON% %BOT_SCRIPT% >> %LOG% 2>&1
    echo [%date% %time%] Bot relanzado. >> %LOG%
) else (
    echo [%date% %time%] Bot OK (puerto %PORT% activo). >> %LOG%
)
