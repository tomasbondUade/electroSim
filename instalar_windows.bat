@echo off
echo ============================================
echo   Unitree Motor Monitor - Instalador
echo ============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado.
    echo.
    echo Descargalo de: https://www.python.org/downloads/
    echo IMPORTANTE: Al instalar, tilda "Add python.exe to PATH"
    echo.
    echo Despues de instalar Python, ejecuta este archivo de nuevo.
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version
echo.

REM Verificar Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git no esta instalado.
    echo.
    echo Descargalo de: https://git-scm.com/download/win
    echo Instala con las opciones por defecto.
    echo.
    echo Despues de instalar Git, ejecuta este archivo de nuevo.
    pause
    exit /b 1
)

echo [OK] Git encontrado
echo.

REM Crear entorno virtual
echo [1/4] Creando entorno virtual...
if not exist env (
    python -m venv env
)

REM Activar entorno
call env\Scripts\activate.bat

REM Instalar dependencias
echo [2/4] Instalando dependencias (PyQt6, openpyxl)...
pip install PyQt6 openpyxl --quiet

REM Clonar SDK si no existe
echo [3/4] Instalando Unitree SDK...
if not exist unitree_sdk2_python (
    git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
)
pip install -e unitree_sdk2_python --quiet

echo [4/4] Instalacion completa!
echo.
echo ============================================
echo   Para ejecutar la app, usa: ejecutar.bat
echo ============================================
pause
