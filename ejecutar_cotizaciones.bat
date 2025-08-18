@echo off
chcp 65001 >nul
title Sistema de Automatizacion de Cotizaciones
echo.
echo ===============================================
echo   Sistema de Automatizacion de Cotizaciones
echo ===============================================
echo.

:: Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo.
    echo [INFO] Por favor instala Python desde: https://python.org
    echo        Asegurate de marcar "Add Python to PATH" durante la instalacion
    echo.
    pause
    exit /b 1
)

echo [OK] Python detectado correctamente
echo.

:: Cambiar al directorio del script
cd /d "%~dp0"

:: Verificar si existe el entorno virtual
if not exist ".venv" (
    echo [SETUP] Creando entorno virtual por primera vez...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Error creando entorno virtual
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado
)

:: Activar entorno virtual
echo [INFO] Activando entorno virtual...
call .venv\Scripts\activate.bat

:: Verificar e instalar dependencias
echo [INFO] Verificando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Error instalando dependencias
    pause
    exit /b 1
)

echo [OK] Dependencias instaladas correctamente
echo.
echo [START] Iniciando interfaz grafica...
echo.

:: Ejecutar la GUI principal
python ejecutar_gui.py

:: Si hay problemas de codificación, intentar con versión ASCII
if errorlevel 1 (
    echo.
    echo [WARNING] Problema detectado, intentando modo compatibilidad...
    python ejecutar_gui_ascii.py
)

:: Si la GUI se cierra, el bat también se cierra automáticamente
echo.
echo [END] Aplicacion cerrada
echo.
timeout /t 2 /nobreak >nul
exit
