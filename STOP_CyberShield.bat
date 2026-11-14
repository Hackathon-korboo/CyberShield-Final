@echo off
setlocal enabledelayedexpansion

title CYBERSHIELD AI 2.0 - SAFE SHUTDOWN

set "QUIET_MODE=0"
if /i "%~1"=="--quiet" set "QUIET_MODE=1"

if "!QUIET_MODE!"=="0" (
    echo ===============================================================================
    echo               CYBERSHIELD AI 2.0 -- SAFE SHUTDOWN UTILITY
    echo ===============================================================================
    echo.
)

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

set "PID_FILE=%PROJECT_ROOT%\.cybershield.pid"
set "KILLED_ANY=0"

:: 1. Check PID file
if exist "%PID_FILE%" (
    set /p STORED_PID=<"%PID_FILE%"
    if defined STORED_PID (
        echo [INFO] Found recorded PID !STORED_PID! in .cybershield.pid
        for /f "tokens=1" %%p in ('tasklist /FI "PID eq !STORED_PID!" /NH 2^>nul') do (
            if /i "%%p"=="python.exe" (
                echo [STOPPING] Terminating CyberShield server process tree - PID !STORED_PID!...
                taskkill /PID !STORED_PID! /F /T >nul 2>&1
                set "KILLED_ANY=1"
            )
        )
    )
    del /f /q "%PID_FILE%" >nul 2>&1
)

:: 2. Check Port 8000 Listeners for safety
for /f "tokens=5" %%a in ('netstat -a -n -o 2^>nul ^| findstr :8000 ^| findstr LISTENING') do (
    set "PORT_PID=%%a"
    if defined PORT_PID (
        for /f "tokens=1" %%p in ('tasklist /FI "PID eq !PORT_PID!" /NH 2^>nul') do (
            if /i "%%p"=="python.exe" (
                echo [STOPPING] Terminating remaining Python listener on Port 8000 - PID !PORT_PID!...
                taskkill /PID !PORT_PID! /F /T >nul 2>&1
                set "KILLED_ANY=1"
            )
        )
    )
)

if "!KILLED_ANY!"=="1" (
    echo [SUCCESS] CyberShield AI 2.0 Backend has been successfully stopped.
    echo Port 8000 is now free.
) else (
    echo [INFO] No active CyberShield server processes were found running on Port 8000.
)

if exist "%PID_FILE%" del /f /q "%PID_FILE%" >nul 2>&1

if "!QUIET_MODE!"=="0" (
    echo.
    echo ===============================================================================
    echo [DONE] Shutdown complete. Unrelated background processes were unaffected.
    echo ===============================================================================
    echo.
    pause
)

exit /b 0
