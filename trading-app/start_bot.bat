@echo off
REM Arranque del bot IFVG al iniciar sesion. Tarea: IFVG_Bot_Startup.
REM Delega en watchdog_bot.ps1 -Force, que ademas de arrancar:
REM   - mata solo lo que ESCUCHA en :8000 (el netstat/findstr de antes cogia
REM     tambien conexiones salientes y mataba procesos que no tocaban)
REM   - espera a que el puerto quede libre (evita el "10048 address in use")
REM   - fuerza UTF-8 (el crash del 17-jul-2026 fue un emoji en cp1252)
REM   - confirma que responde antes de dar por bueno el arranque

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\Pc2025\Desktop\ANTIGRAVITY\trading-app\watchdog_bot.ps1" -Force
exit /b %ERRORLEVEL%
