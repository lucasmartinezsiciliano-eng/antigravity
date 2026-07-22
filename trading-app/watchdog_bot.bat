@echo off
REM Lanzador del watchdog. La logica real esta en watchdog_bot.ps1.
REM El contenido anterior de este .bat fallaba con exit 255 en TODAS sus
REM ejecuciones: el parentesis de "(puerto 8000 activo)" cerraba el bloque
REM else antes de tiempo. Por eso el bot no se relanzo tras el crash del 17-jul.
REM Tarea: IFVG_Bot_Watchdog (cada 5 min). Solo relanza si el bot no responde.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Pc2025\Desktop\ANTIGRAVITY\trading-app\watchdog_bot.ps1"
exit /b %ERRORLEVEL%
