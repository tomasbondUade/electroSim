@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Unitree Go2 — Configurar y conectar

:: ============================================================
:: Auto-elevacion: si no tiene admin, se relanza como admin
:: ============================================================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando permisos de administrador...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)

:: ============================================================
:: Buscar el ejecutable de la app
:: ============================================================
set "APP="
if exist "%~dp0dist\UnitreeMotorMonitor.exe" set "APP=%~dp0dist\UnitreeMotorMonitor.exe"
if exist "%~dp0UnitreeMotorMonitor.exe"      set "APP=%~dp0UnitreeMotorMonitor.exe"

cls
echo.
echo  ============================================
echo    Unitree Motor Monitor — Configuracion
echo  ============================================
echo.

:: ============================================================
:: Detectar adaptador Ethernet conectado por cable
:: ============================================================
echo  Buscando adaptador Ethernet...
echo.

set "ADAPTER="
for /f "tokens=*" %%i in ('powershell -NoProfile -Command ^
    "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.PhysicalMediaType -notmatch 'Native 802.11|Bluetooth' } | Select-Object -First 1 -ExpandProperty Name"') do (
    set "ADAPTER=%%i"
)

if "!ADAPTER!"=="" (
    echo  [ERROR] No se encontro ningun adaptador Ethernet conectado.
    echo.
    echo  Verificá que el cable este bien conectado al robot
    echo  y a la PC, luego volvé a ejecutar este archivo.
    echo.
    pause
    exit /b 1
)

echo  Adaptador encontrado: !ADAPTER!
echo.

:: ============================================================
:: Verificar si la IP ya esta configurada correctamente
:: ============================================================
set "YA_CONFIGURADO=0"
for /f "tokens=*" %%i in ('powershell -NoProfile -Command ^
    "Get-NetIPAddress -InterfaceAlias '!ADAPTER!' -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty IPAddress"') do (
    if "%%i"=="192.168.123.100" set "YA_CONFIGURADO=1"
)

if "!YA_CONFIGURADO!"=="1" (
    echo  [OK] La IP ya esta configurada correctamente.
    echo.
    goto :ping_robot
)

:: ============================================================
:: Configurar IP estatica
:: ============================================================
echo  Configurando IP estatica 192.168.123.100...

REM Eliminar IPs previas del adaptador
powershell -NoProfile -Command ^
    "Get-NetIPAddress -InterfaceAlias '!ADAPTER!' -AddressFamily IPv4 -ErrorAction SilentlyContinue | Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue" >nul 2>&1

REM Eliminar gateway previo
powershell -NoProfile -Command ^
    "Remove-NetRoute -InterfaceAlias '!ADAPTER!' -DestinationPrefix '0.0.0.0/0' -Confirm:$false -ErrorAction SilentlyContinue" >nul 2>&1

REM Asignar IP estatica
powershell -NoProfile -Command ^
    "New-NetIPAddress -InterfaceAlias '!ADAPTER!' -IPAddress 192.168.123.100 -PrefixLength 24 -ErrorAction Stop" >nul 2>&1

if %errorlevel% neq 0 (
    echo  [ERROR] No se pudo configurar la IP.
    echo  Intenta ejecutar este archivo como Administrador.
    echo.
    pause
    exit /b 1
)

echo  [OK] IP configurada: 192.168.123.100 / 255.255.255.0
echo.

:: ============================================================
:: Verificar conexion con el robot
:: ============================================================
:ping_robot
echo  Verificando conexion con el robot (192.168.123.161)...

ping -n 3 -w 1000 192.168.123.161 >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [AVISO] No se pudo alcanzar el robot.
    echo.
    echo  Posibles causas:
    echo    - El robot no esta encendido
    echo    - El cable Ethernet no esta bien conectado
    echo    - El robot tarda unos segundos en arrancar
    echo.
    echo  Podes abrir la app igual y usar Modo Demo,
    echo  o esperar que el robot encienda y volver a intentar.
    echo.
    choice /C SD /M "  [S] Abrir la app de todas formas   [D] Salir"
    if errorlevel 2 exit /b 0
    goto :abrir_app
)

echo  [OK] Robot encontrado y respondiendo.
echo.

:: ============================================================
:: Abrir la app
:: ============================================================
:abrir_app
if "!APP!"=="" (
    echo  [ERROR] No se encontro UnitreeMotorMonitor.exe
    echo  Asegurate de que el .exe este en la misma carpeta
    echo  que este archivo o en la carpeta "dist\".
    echo.
    pause
    exit /b 1
)

echo  Abriendo Unitree Motor Monitor...
echo.
echo  ============================================
echo   Listo! Selecciona Go2 y hace click en
echo   Conectar para ver los datos del robot.
echo  ============================================
echo.

start "" "!APP!"
timeout /t 3 >nul
exit /b 0
