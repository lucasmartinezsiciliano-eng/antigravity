@echo off
REM Bot IFVG — Auto-start script
REM Kills any existing instance, waits, then relaunches.
REM Placed in Task Scheduler: At logon + every 5 minutes (restart on crash).

cd /d "C:\Users\Pc2025\Desktop\ANTIGRAVITY\trading-app"

REM Kill any stale python instances holding port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do (
    taskkill /PID %%a /F >nul 2>&1
)

timeout /t 3 /nobreak >nul

REM Start bot in background (hidden window)
start "" /B /MIN C:\Python314\python.exe beta_local.py >> bot_output.log 2>&1
