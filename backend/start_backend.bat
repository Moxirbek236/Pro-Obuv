@echo off
REM ═══════════════════════════════════════════════════════════════════════
REM Backend Server Management Script for Windows
REM ═══════════════════════════════════════════════════════════════════════
REM Purpose: Start/restart Flask backend with proper process management
REM Usage: start_backend.bat
REM ═══════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo    BACKEND SERVER - WINDOWS
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Change to backend directory
cd /d "%~dp0"

echo [1/4] Checking environment...
echo Current directory: %CD%

REM Check if app.py exists
if not exist "app.py" (
    echo.
    echo ❌ ERROR: app.py not found!
    echo Please run this script from the backend directory.
    pause
    exit /b 1
)

echo ✅ Backend file found

REM Stop existing Python processes running app.py
echo.
echo [2/4] Stopping existing backend processes...
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *app.py*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "COMMANDLINE eq *app.py*" >nul 2>&1

REM Wait for processes to stop
timeout /t 2 /nobreak >nul

REM More aggressive cleanup - kill all python processes (use with caution)
echo Cleaning up all Python processes...
taskkill /F /IM python.exe >nul 2>&1

REM Wait again
timeout /t 2 /nobreak >nul

echo ✅ Cleanup complete

REM Check if .env file exists
echo.
echo [3/4] Checking configuration...
if exist ".env" (
    echo ✅ .env file found
) else (
    echo ❌ WARNING: .env file not found!
    echo Backend may not work without proper configuration.
)

REM Start the backend
echo.
echo [4/4] Starting Flask backend...
echo ═══════════════════════════════════════════════════════════════════════
echo.
echo 📡 Backend is starting...
echo 📊 Server will be available at:
echo    - http://localhost:5000/
echo    - http://0.0.0.0:5000/
echo.
echo 💡 Press Ctrl+C to stop the backend
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Start backend with output to console and log file
python app.py 2>&1 | tee backend.log

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Backend stopped successfully
) else (
    echo.
    echo ❌ Backend crashed with error code %ERRORLEVEL%
    echo 📋 Check backend.log for details
    pause
)
