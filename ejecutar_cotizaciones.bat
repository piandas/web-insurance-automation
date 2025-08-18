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
        echo [INFO] Asegurate de tener Python instalado correctamente
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado
) else (
    echo [INFO] Usando entorno virtual existente
)

:: Activar entorno virtual
echo [INFO] Activando entorno virtual...
call .venv\Scripts\activate.bat

:: Verificar si las dependencias están instaladas
echo [INFO] Verificando dependencias...
python -c "import playwright, pandas, dotenv, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Dependencias faltantes o dañadas, reinstalando...
    goto :install_deps
) else (
    echo [OK] Dependencias verificadas
    goto :run_app
)

:install_deps
:: Instalar dependencias una por una para evitar conflictos
echo [INFO] Instalando pip, setuptools y wheel...
python -m pip install --upgrade pip setuptools wheel

echo [INFO] Instalando python-dotenv...
pip install python-dotenv==1.0.1

echo [INFO] Instalando openpyxl...
pip install openpyxl==3.1.2

echo [INFO] Instalando numpy (REQUERIDO)...
echo [INFO] Intentando con ultima version...
pip install --only-binary=all numpy
if errorlevel 1 (
    echo [WARNING] Fallo version actual, probando version anterior...
    pip install --only-binary=all "numpy<2.0.0"
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar numpy
        echo [ERROR] El sistema NO puede funcionar sin numpy
        echo [INFO] Descarga e instala Microsoft Visual C++ Build Tools desde:
        echo [INFO] https://visualstudio.microsoft.com/visual-cpp-build-tools/
        pause
        exit /b 1
    )
)

echo [INFO] Instalando pandas (REQUERIDO)...
echo [INFO] Intentando con ultima version...
pip install --only-binary=all pandas
if errorlevel 1 (
    echo [WARNING] Fallo version actual, probando version anterior...
    pip install --only-binary=all "pandas<3.0.0"
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar pandas
        echo [ERROR] El sistema NO puede funcionar sin pandas
        echo [INFO] Descarga e instala Microsoft Visual C++ Build Tools desde:
        echo [INFO] https://visualstudio.microsoft.com/visual-cpp-build-tools/
        pause
        exit /b 1
    )
)

echo [OK] numpy y pandas instalados correctamente
echo [INFO] Instalando playwright...
pip install playwright==1.48.0

echo [INFO] Instalando navegadores...
playwright install chromium

echo [OK] Todas las dependencias instaladas correctamente

:run_app
echo.
echo [START] Iniciando interfaz grafica...
echo.

:: Ejecutar la GUI principal
python scripts\ejecutar_gui.py

:: Si hay problemas de codificación, intentar con versión ASCII
if errorlevel 1 (
    echo.
    echo [WARNING] Problema detectado, intentando modo compatibilidad...
    python scripts\ejecutar_gui_ascii.py
)

:: Si la GUI se cierra, el bat también se cierra automáticamente
echo.
echo [END] Aplicacion cerrada
echo.
timeout /t 2 /nobreak >nul
exit
