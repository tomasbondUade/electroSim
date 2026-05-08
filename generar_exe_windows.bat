@echo off
setlocal

echo ============================================
echo   Unitree Motor Monitor - Instalador Windows
echo   Version corregida para Windows + Unitree SDK
echo ============================================
echo.

REM =========================================================
REM IMPORTANTE:
REM unitree_sdk2_python depende de cyclonedds==0.10.2.
REM En Windows conviene usar Python 3.10 x64 porque existe wheel
REM precompilado para cyclonedds 0.10.2.
REM =========================================================

REM Verificar Python Launcher
where py >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro el Python Launcher ^(py^).
    echo Instala Python 3.10 x64 y marca "Add python.exe to PATH".
    echo Tambien podes instalarlo con:
    echo   winget install Python.Python.3.10
    pause
    exit /b 1
)

REM Verificar Python 3.10
py -3.10 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro Python 3.10.
    echo.
    echo Este instalador necesita Python 3.10 x64 para evitar que cyclonedds
    echo intente compilar desde codigo fuente en Windows.
    echo.
    echo Instala Python 3.10 x64 desde python.org o con:
    echo   winget install Python.Python.3.10
    pause
    exit /b 1
)

REM Verificar que sea 64 bits
py -3.10 -c "import struct, sys; sys.exit(0 if struct.calcsize('P')*8 == 64 else 1)"
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.10 no es de 64 bits.
    echo Instala Python 3.10 x64.
    pause
    exit /b 1
)

echo [OK] Python 3.10 x64 encontrado
py -3.10 --version
echo.

REM Verificar Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git no esta instalado.
    echo Descargalo desde: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [OK] Git encontrado
git --version
echo.

REM Verificar main.py
if not exist main.py (
    echo [ERROR] No se encontro main.py en esta carpeta.
    echo Ejecuta este .bat desde la carpeta donde esta main.py.
    pause
    exit /b 1
)

REM Crear entorno virtual con Python 3.10
echo [1/6] Creando entorno virtual con Python 3.10...
if exist env (
    echo [INFO] Ya existe la carpeta env. Se reutiliza el entorno.
) else (
    py -3.10 -m venv env
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

call env\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b 1
)
echo [OK] Entorno virtual activado
echo.

REM Actualizar herramientas base
echo [2/6] Actualizando pip/setuptools/wheel...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al actualizar pip/setuptools/wheel.
    pause
    exit /b 1
)
echo [OK] Herramientas actualizadas
echo.

REM Instalar dependencias de la app
echo [3/6] Instalando dependencias de la app...
python -m pip install PyQt6 openpyxl pyinstaller numpy opencv-python
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al instalar PyQt6/openpyxl/pyinstaller/numpy/opencv-python.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas
echo.

REM Instalar CycloneDDS primero como wheel binario
echo [4/6] Instalando cyclonedds==0.10.2...
python -m pip install --only-binary=:all: cyclonedds==0.10.2
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al instalar cyclonedds==0.10.2.
    echo.
    echo Causa probable: no estas usando Python 3.10 x64 o pip no encontro wheel compatible.
    echo No sigas con Unitree SDK hasta resolver esto.
    pause
    exit /b 1
)
echo [OK] cyclonedds instalado
echo.

REM Clonar e instalar SDK sin reinstalar dependencias
echo [5/6] Instalando Unitree SDK...
if not exist unitree_sdk2_python (
    git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo clonar el SDK. Verifica tu conexion a internet.
        pause
        exit /b 1
    )
)

python -m pip install -e unitree_sdk2_python --no-deps
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al instalar Unitree SDK.
    pause
    exit /b 1
)
echo [OK] Unitree SDK instalado
echo.

REM Verificar imports
echo [6/6] Verificando instalacion...
python -c "import cyclonedds; print('[OK] cyclonedds OK')"
if %errorlevel% neq 0 (
    echo [ERROR] cyclonedds no se importa correctamente.
    pause
    exit /b 1
)

python -c "from unitree_sdk2py.core.channel import ChannelSubscriber; print('[OK] SDK OK')"
if %errorlevel% neq 0 (
    echo [ERROR] El SDK no se importa correctamente.
    pause
    exit /b 1
)

python -c "from PyQt6.QtWidgets import QApplication; print('[OK] PyQt6 OK')"
if %errorlevel% neq 0 (
    echo [ERROR] PyQt6 no se importa correctamente.
    pause
    exit /b 1
)
echo.

REM Generar .exe
echo [FINAL] Generando ejecutable .exe ...
echo Esto puede tardar unos minutos.
echo.

pyinstaller --onefile --windowed --name "UnitreeMotorMonitor" --collect-all unitree_sdk2py --collect-all cyclonedds main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo al generar el .exe.
    echo Revisa los errores de arriba.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   LISTO! El ejecutable se genero en:
echo.
echo   dist\UnitreeMotorMonitor.exe
echo ============================================
echo.
pause
exit /b 0
