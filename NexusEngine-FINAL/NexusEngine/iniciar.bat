@echo off
setlocal enabledelayedexpansion
title NexusEngine Omega v3.0
color 0A
cls

echo.
echo  NexusEngine Omega v3.0
echo  por Emanuel Felipe - github.com/onerddev
echo  ==========================================
echo.

cd /d "%~dp0"

if not exist "api\" (
    echo [ERRO] Pasta api nao encontrada.
    echo Execute este arquivo de dentro da pasta NexusEngine.
    pause
    exit /b 1
)

:: Encontra Python
set "PY="
python --version >nul 2>&1 && set "PY=python" && goto :pyok
py --version >nul 2>&1 && set "PY=py" && goto :pyok
python3 --version >nul 2>&1 && set "PY=python3" && goto :pyok

for %%V in (313 312 311 310 39 38) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
        set "PY=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        goto :pyok
    )
    if exist "C:\Python%%V\python.exe" (
        set "PY=C:\Python%%V\python.exe"
        goto :pyok
    )
)

echo [ERRO] Python nao encontrado.
echo Instale em python.org e marque "Add Python to PATH"
pause
exit /b 1

:pyok
echo [OK] Python: %PY%
echo.

:: Instala dependencias
echo [..] Verificando dependencias...
"%PY%" -c "import fastapi,uvicorn,numpy,psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo [..] Instalando pacotes...
    "%PY%" -m pip install fastapi "uvicorn[standard]" pydantic pydantic-settings python-dotenv numpy psutil --quiet
    echo [OK] Instalado!
) else (
    echo [OK] Dependencias prontas.
)
echo.

:: Libera porta 8000
for /f "tokens=5" %%P in ('netstat -aon 2^>nul ^| findstr ":8000 "') do (
    taskkill /F /PID %%P >nul 2>&1
)

:: Abre navegador apos 4 segundos em paralelo
start "" cmd /c "ping -n 5 127.0.0.1 >nul && start "" http://localhost:8000/dashboard"

echo [OK] Iniciando servidor...
echo.
echo  Dashboard : http://localhost:8000/dashboard
echo  Swagger   : http://localhost:8000/docs
echo  Parar     : Ctrl+C
echo.

"%PY%" -m uvicorn api.main:app --host 0.0.0.0 --port 8000

echo.
echo Servidor encerrado.
pause
