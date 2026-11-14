@echo off
setlocal enabledelayedexpansion

title CYBERSHIELD AI 2.0 - BACKEND LAUNCHER

echo ===============================================================================
echo                 CYBERSHIELD AI 2.0 -- ONE-CLICK LAUNCHER
echo      AI-Powered Web Threat Detection and Digital Trust Intelligence Backend
echo ===============================================================================
echo.

:: 1. Resolve Project Root
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

set "BACKEND_DIR=%PROJECT_ROOT%\backend"

if not exist "%BACKEND_DIR%" (
    echo [ERROR] Backend directory not found: "%BACKEND_DIR%"
    echo Please verify project folder integrity.
    echo.
    pause
    exit /b 1
)

:: 2. Resolve Python Environment
set "PYTHON_EXE="
set "VENV_ACTIVATE="

if exist "%BACKEND_DIR%\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%BACKEND_DIR%\venv\Scripts\python.exe"
    set "VENV_ACTIVATE=%BACKEND_DIR%\venv\Scripts\activate.bat"
    echo [INFO] Detected dedicated virtual environment: "%BACKEND_DIR%\venv"
    goto :PYTHON_FOUND
)

if exist "%PROJECT_ROOT%\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%\venv\Scripts\python.exe"
    set "VENV_ACTIVATE=%PROJECT_ROOT%\venv\Scripts\activate.bat"
    echo [INFO] Detected project virtual environment: "%PROJECT_ROOT%\venv"
    goto :PYTHON_FOUND
)

where python >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_EXE=python"
    echo [INFO] Using system Python from PATH.
    goto :PYTHON_FOUND
)

echo [ERROR] Python was not found in the virtual environment or system PATH.
echo Please ensure Python 3.11+ is installed and configured.
echo.
pause
exit /b 1

:PYTHON_FOUND
:: 3. Pre-flight Import Check
echo [INFO] Verifying CyberShield AI 2.0 application modules...
"%PYTHON_EXE%" -c "import sys; sys.path.insert(0, r'%PROJECT_ROOT%'); from backend.app.risk_app import app" >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Backend import verification failed!
    echo Ensure all dependencies in requirements.txt are installed.
    echo Try running:
    echo   "%PYTHON_EXE%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
    echo.
    pause
    exit /b 1
)
echo [OK] Application modules and dependencies verified successfully.
echo.

:: 4. Port 8000 Occupancy Check
"%PYTHON_EXE%" -c "import socket; s = socket.socket(); s.settimeout(0.5); r = s.connect_ex(('127.0.0.1', 8000)); s.close(); exit(0 if r == 0 else 1)" >nul 2>&1
if !errorlevel! equ 0 (
    echo [WARN] Port 8000 is already in use by another process.
    set /p RESTART_CONFIRM="Would you like to stop the existing process and restart? [Y/N]: "
    if /i "!RESTART_CONFIRM!"=="Y" (
        echo [INFO] Stopping conflicting process on port 8000...
        call "%PROJECT_ROOT%\STOP_CyberShield.bat" --quiet
        ping 127.0.0.1 -n 3 >nul
    ) else (
        echo [ABORT] Server launch cancelled by user.
        pause
        exit /b 0
    )
)

:: 5. Launch Server Process
echo [STARTING] Launching CyberShield AI 2.0 Backend on http://127.0.0.1:8000 ...
if defined VENV_ACTIVATE (
    start "CYBERSHIELD AI 2.0 - BACKEND SERVER [Port 8000]" cmd /k "title CYBERSHIELD AI 2.0 - BACKEND SERVER [Port 8000] && cd /d "%PROJECT_ROOT%" && call "%VENV_ACTIVATE%" && "%PYTHON_EXE%" "%BACKEND_DIR%\run_server.py""
) else (
    start "CYBERSHIELD AI 2.0 - BACKEND SERVER [Port 8000]" cmd /k "title CYBERSHIELD AI 2.0 - BACKEND SERVER [Port 8000] && cd /d "%PROJECT_ROOT%" && "%PYTHON_EXE%" "%BACKEND_DIR%\run_server.py""
)

:: 6. Health Check Wait Loop
echo [INFO] Waiting for server initialization...
set /a ATTEMPTS=0
set /a MAX_ATTEMPTS=15
set "SERVER_HEALTHY=0"

:HEALTH_LOOP
set /a ATTEMPTS+=1
ping 127.0.0.1 -n 2 >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $res = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/v1/health' -UseBasicParsing -TimeoutSec 2; if ($res.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if !errorlevel! equ 0 (
    set "SERVER_HEALTHY=1"
    goto :HEALTH_SUCCESS
)

if !ATTEMPTS! lss !MAX_ATTEMPTS! (
    echo [WAIT] Probing /api/v1/health - Attempt !ATTEMPTS! of !MAX_ATTEMPTS!...
    goto :HEALTH_LOOP
)

:HEALTH_TIMEOUT
echo.
echo [WARNING] Backend did not respond within 15 seconds.
echo Please inspect the dedicated server console window for error tracebacks.
echo.
goto :SUMMARY

:HEALTH_SUCCESS
echo.
echo [SUCCESS] CyberShield AI 2.0 Backend is active and healthy!
echo.

:SUMMARY
echo ===============================================================================
echo                     CYBERSHIELD AI 2.0 IS OPERATIONAL
echo ===============================================================================
echo   - Web Application UI : http://127.0.0.1:8000/
echo   - Interactive Docs   : http://127.0.0.1:8000/docs
echo   - ReDoc Reference    : http://127.0.0.1:8000/redoc
echo   - Health Endpoint    : http://127.0.0.1:8000/api/v1/health
echo   - Threat Analysis    : POST http://127.0.0.1:8000/api/v1/analyze/text
echo   - Unified Scan Route : POST http://127.0.0.1:8000/api/v1/scan-url
echo.
echo   Keep the dedicated server console window open while testing.
echo   To safely shut down the server, run: STOP_CyberShield.bat
echo ===============================================================================
echo.

set /p OPEN_BROWSER="Open CyberShield Web Application in your browser now? [Y/N] default Y: "
if "!OPEN_BROWSER!"=="" set "OPEN_BROWSER=Y"
if /i "!OPEN_BROWSER!"=="Y" (
    start http://127.0.0.1:8000/
)

echo.
echo Press any key to exit this launcher window [server will continue running in background].
pause >nul
exit /b 0
