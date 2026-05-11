@echo off
setlocal
echo ============================================
echo   Unitree Motor Monitor - Generar .exe
echo ============================================
echo.

REM Verificar que existe el entorno virtual
if not exist env\Scripts\activate.bat (
    echo [ERROR] No se encontro el entorno virtual.
    echo Ejecuta primero: python -m venv env
    echo Luego: env\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

call env\Scripts\activate.bat
echo [OK] Entorno virtual activado
echo.

REM Asegurar que pyqtgraph este instalado
echo [1/3] Verificando dependencias...
python -m pip install --quiet pyqtgraph pyinstaller
echo [OK] Dependencias OK
echo.

REM Limpiar build anterior
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist
if exist UnitreeMotorMonitor.spec del UnitreeMotorMonitor.spec

REM Generar .exe
echo [2/3] Generando ejecutable (puede tardar unos minutos)...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "UnitreeMotorMonitor" ^
    --collect-all pyqtgraph ^
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
echo [3/3] Verificando...
if exist dist\UnitreeMotorMonitor.exe (
    echo ============================================
    echo   LISTO! Ejecutable generado en:
    echo.
    echo   dist\UnitreeMotorMonitor.exe
    echo ============================================
) else (
    echo [ERROR] No se encontro el .exe en dist\
)
echo.
pause
exit /b 0
