@echo off
setlocal
echo ============================================
echo   Unitree Motor Monitor - Generar .exe
echo ============================================
echo.

REM Verificar que existe env310 (Python 3.10 + cyclonedds 0.10.2)
if not exist env310\Scripts\activate.bat (
    echo [ERROR] No se encontro el entorno virtual env310.
    echo Ejecuta primero:
    echo   py -3.10 -m venv env310
    echo   env310\Scripts\pip install PyQt6 pyqtgraph openpyxl pyinstaller
    echo   env310\Scripts\pip install --only-binary=:all: cyclonedds==0.10.2
    echo   env310\Scripts\pip install unitree_sdk2_python --no-deps
    pause
    exit /b 1
)

call env310\Scripts\activate.bat
echo [OK] Entorno env310 activado (Python 3.10 + cyclonedds 0.10.2)
echo.

REM -------------------------------------------------------
REM  Reinstalar unitree_sdk2py de forma NO editable
REM  (el modo -e no es compatible con PyInstaller)
REM -------------------------------------------------------
echo [0/2] Reinstalando unitree_sdk2py (modo no-editable para PyInstaller)...
pip uninstall unitree_sdk2py -y >nul 2>&1
pip install "%~dp0unitree_sdk2_python" --no-deps --quiet
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo instalar unitree_sdk2py.
    pause
    exit /b 1
)
echo [OK] unitree_sdk2py instalado correctamente.
echo.

REM Limpiar build anterior
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist
if exist UnitreeMotorMonitor.spec del UnitreeMotorMonitor.spec

REM Generar .exe
echo [1/2] Generando ejecutable (puede tardar unos minutos)...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "UnitreeMotorMonitor" ^
    --collect-all pyqtgraph ^
    --collect-all cyclonedds ^
    --collect-all unitree_sdk2py ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.QtOpenGL ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo al generar el .exe. Revisa los errores de arriba.
    pause
    exit /b 1
)

echo.
echo [2/2] Verificando...
if exist dist\UnitreeMotorMonitor.exe (
    echo ============================================
    echo   LISTO! Ejecutable generado en:
    echo.
    echo   dist\UnitreeMotorMonitor.exe
    echo.
    echo   IMPORTANTE: cada PC que use el .exe con robot
    echo   real necesita configurar IP estatica en Ethernet:
    echo     IP:      192.168.123.100
    echo     Mascara: 255.255.255.0
    echo   (usa conectar_robot.bat - configura todo solo)
    echo ============================================
) else (
    echo [ERROR] No se encontro el .exe en dist\
)
echo.
pause
exit /b 0
