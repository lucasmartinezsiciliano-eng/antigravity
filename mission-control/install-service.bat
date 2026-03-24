@echo off
echo.
echo  Instalando Mission Control como servicio de Windows...
echo.

schtasks /create /tn "Antigravity Mission Control" /tr "\"C:\Program Files\nodejs\node.exe\" \"C:\Users\Pc2025\Desktop\ANTIGRAVITY\mission-control\server.js\"" /sc ONSTART /ru SYSTEM /rl HIGHEST /f

if %ERRORLEVEL% EQU 0 (
  echo.
  echo  [OK] Servicio instalado correctamente.
  echo  Arrancara automaticamente cada vez que enciendas el PC.
  echo.
  echo  Arrancando ahora...
  schtasks /run /tn "Antigravity Mission Control"
  echo.
  echo  Abre http://localhost:3333 en el navegador
) else (
  echo.
  echo  [ERROR] Fallo al instalar. Prueba a ejecutar como Administrador.
)
echo.
pause
