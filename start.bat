@echo off
title Skeleton Meme - Doomscroll Stopper
echo ======================================================
echo    Skeleton Meme - Doomscroll Stopper
echo ======================================================
echo.

if exist "%~dp0venv\Scripts\python.exe" (
    echo [OK] Iniciando con entorno virtual venv...
    "%~dp0venv\Scripts\python.exe" "%~dp0main.py" %*
) else (
    echo [!] No se encontro venv, intentando con python del sistema...
    python "%~dp0main.py" %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] La aplicacion se cerro con codigo de error: %ERRORLEVEL%
    pause
)
