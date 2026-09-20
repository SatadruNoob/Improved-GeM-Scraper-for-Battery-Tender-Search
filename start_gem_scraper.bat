@echo off
title GeM Portal Scraper - Production Launcher
setlocal enabledelayedexpansion

REM =====================================================
REM CONFIG
REM =====================================================
set "PROJECT_PATH=C:\Users\biswa\Downloads\GeM Portal Scraper-20260920T074128Z-1-001\GeM Portal Scraper"
set "VENV_PYTHON=%PROJECT_PATH%\.venv\Scripts\python.exe"
set "PORT=8501"
set "MAX_WAIT=60"

echo.
echo ===============================================
echo   GeM Portal Scraper Production Launcher
echo ===============================================
echo.

REM =====================================================
REM STEP 1 — Kill anything using port 8501
REM =====================================================
echo Checking for processes using port %PORT%...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
    echo Killing process with PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM Extra cleanup for orphan streamlit/python
taskkill /F /IM streamlit.exe >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Streamlit*" >nul 2>&1

echo Port cleanup complete.
echo.

REM =====================================================
REM STEP 2 — Validate paths
REM =====================================================
if not exist "%PROJECT_PATH%" (
    echo ERROR: Project directory not found.
    pause
    exit /b
)

if not exist "%VENV_PYTHON%" (
    echo ERROR: Virtual environment Python not found.
    pause
    exit /b
)

cd /d "%PROJECT_PATH%"

REM =====================================================
REM STEP 3 — Activate venv
REM =====================================================
echo Using virtual environment Python:
echo %VENV_PYTHON%
echo.

REM =====================================================
REM STEP 4 — Start Python launcher
REM =====================================================
echo Starting Streamlit launcher...
start "GeM Scraper Server" cmd /k ""%VENV_PYTHON%" launcher.py"

echo Waiting for server to become available...

REM =====================================================
REM STEP 5 — Wait until port is LIVE
REM =====================================================
set /a counter=0

:CHECK_PORT
set /a counter+=1

netstat -ano | findstr :%PORT% | findstr LISTENING >nul

if %errorlevel%==0 (
    echo Server is LIVE!
    goto OPEN_BROWSER
)

if %counter% GEQ %MAX_WAIT% (
    echo ERROR: Server failed to start within %MAX_WAIT% seconds.
    pause
    exit /b
)

timeout /t 1 >nul
goto CHECK_PORT

REM =====================================================
REM STEP 6 — Open browser
REM =====================================================
:OPEN_BROWSER
echo Opening browser...
start http://localhost:%PORT%

echo.
echo ===== SUCCESS =====
echo Application started successfully.
echo.
exit
