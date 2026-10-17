@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Instalando Sistema de Reservas de Espacios
del .instalado_ok .instalado_error 2>nul

set "PY=C:\Users\sebas\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%PY%" set "PY=py"

echo [1/4] Creando entorno virtual .venv ...
if not exist ".venv\Scripts\python.exe" (
    "%PY%" -m venv .venv
    if errorlevel 1 goto error
)

echo.
echo [2/4] Instalando dependencias ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install --no-cache-dir "pywebview==5.4" "pythonnet==3.1.0"
if errorlevel 1 echo (pywebview no se pudo instalar: la app se abrira en el navegador)

echo.
echo [3/4] Preparando base de datos con datos de ejemplo ...
".venv\Scripts\python.exe" -m flask --app run seed

echo.
echo [4/4] Creando acceso directo en el Escritorio ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0crear_acceso_directo.ps1"
if errorlevel 1 goto error

echo.
echo ============================================================
echo  Listo. Abre "Reservas de Espacios" desde tu Escritorio.
echo ============================================================
echo instalado> .instalado_ok
pause
exit /b 0

:error
echo.
echo *** Ocurrio un error durante la instalacion. Revisa los mensajes de arriba. ***
echo error> .instalado_error
pause
exit /b 1
