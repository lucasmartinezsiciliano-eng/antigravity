@echo off
title VISAI Backend

echo ============================================
echo  VISAI Backend (localhost:8000)
echo ============================================
echo.
echo  Para desarrollo local: la web en localhost:3000
echo  apunta a este backend automaticamente.
echo.
echo  Para enseñar a alguien (tunnel):
echo    1. Abre otra terminal y ejecuta:
echo       ssh -o StrictHostKeyChecking=no -R 80:localhost:8000 nokey@localhost.run
echo    2. Copia la URL que aparece (*.lhr.life)
echo    3. Cambia NEXT_PUBLIC_API_URL en web\.env.local
echo    4. Reinicia la web con: npm run dev
echo.
echo ============================================

cd /d "%~dp0backend"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
