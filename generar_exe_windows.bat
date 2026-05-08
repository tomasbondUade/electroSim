@echo off
echo ============================================
echo   Unitree Motor Monitor - Instalador Windows
echo   Instala todo y genera el .exe
echo ============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado.
    echo.
    echo 1. Descargalo de: https://www.python.org/downloads/
    echo 2. IMPORTANTE: Al instalar, tilda "Add python.exe to PATH"
    echo 3. Despues de instalar Python, ejecuta este archivo de nuevo.
    echo.
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
    echo 1. Descargalo de: https://git-scm.com/download/win
    echo 2. Instala con las opciones por defecto.
    echo 3. Despues de instalar Git, ejecuta este archivo de nuevo.
    echo.
    pause
    exit /b 1
)
echo [OK] Git encontrado
echo.

REM Crear entorno virtual
echo [1/6] Creando entorno virtual...
if not exist env (
    python -m venv env
)
call env\Scripts\activate.bat
echo [OK] Entorno virtual activado
echo.

REM Instalar dependencias
echo [2/6] Instalando PyQt6, openpyxl...
pip install PyQt6 openpyxl --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al instalar PyQt6/openpyxl
    pause
    exit /b 1
)
echo [OK] PyQt6 y openpyxl instalados
echo.

REM Instalar PyInstaller
echo [3/6] Instalando PyInstaller...
pip install pyinstaller --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al instalar PyInstaller
    pause
    exit /b 1
)
echo [OK] PyInstaller instalado
echo.

REM Clonar e instalar SDK
echo [4/6] Instalando Unitree SDK...
if not exist unitree_sdk2_python (
    git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo clonar el SDK. Verifica tu conexion a internet.
        pause
        exit /b 1
    )
)
pip install -e unitree_sdk2_python --quiet
echo [OK] Unitree SDK instalado
echo.

REM Verificar que todo importa bien
echo [5/6] Verificando instalacion...
python -c "from unitree_sdk2py.core.channel import ChannelSubscriber; print('[OK] SDK OK')"
if %errorlevel% neq 0 (
    echo [ERROR] El SDK no se importa correctamente
    pause
    exit /b 1
)
python -c "from PyQt6.QtWidgets import QApplication; print('[OK] PyQt6 OK')"
if %errorlevel% neq 0 (
    echo [ERROR] PyQt6 no se importa correctamente
    pause
    exit /b 1
)
echo.

REM Generar .exe
echo [6/6] Generando ejecutable .exe ...
echo Esto puede tardar unos minutos, espera...
echo.
pyinstaller --onefile --windowed --name "UnitreeMotorMonitor" --collect-all unitree_sdk2py --collect-all cyclonedds main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo al generar el .exe
    echo Revisa los errores de arriba.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   LISTO! El ejecutable se genero en:
echo.
echo   dist\UnitreeMotorMonitor.exe
echo.
echo   Copia ese archivo a cualquier PC Windows
echo   y ejecutalo con doble click.
echo ============================================
echo.
pause
