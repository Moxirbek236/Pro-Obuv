@echo off
REM ═══════════════════════════════════════════════════════════════════════
REM FULL SERVER MANAGEMENT SCRIPT FOR WINDOWS
REM ═══════════════════════════════════════════════════════════════════════
REM Purpose: Start/restart both Backend and Telegram Bot servers
REM Usage: start_all_servers.bat
REM ═══════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo    SAFETY.UZ - FULL SERVER STARTUP
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Change to project root directory
cd /d "%~dp0"

echo [STEP 1/5] Stopping all existing processes...
echo ═══════════════════════════════════════════════════════════════════════

REM Kill all Python processes
echo Stopping all Python processes...
taskkill /F /IM python.exe >nul 2>&1

REM Wait for processes to stop
timeout /t 3 /nobreak >nul

echo ✅ All processes stopped
echo.

echo [STEP 2/5] Checking project structure...
echo ═══════════════════════════════════════════════════════════════════════

REM Check if backend directory exists
if not exist "backend\app.py" (
    echo ❌ ERROR: backend\app.py not found!
    pause
    exit /b 1
)
echo ✅ Backend found

REM Check if bot directory exists
if not exist "bot\telegram_bot.py" (
    echo ❌ ERROR: bot\telegram_bot.py not found!
    pause
    exit /b 1
)
echo ✅ Bot found
echo.

echo [STEP 3/5] Starting Backend Server...
echo ═══════════════════════════════════════════════════════════════════════

REM Start backend in new window
start "Safety.uz Backend Server" cmd /k "cd /d backend && python app.py"

REM Wait for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo ✅ Backend started in separate window
echo.

echo [STEP 4/5] Starting Telegram Bot...
echo ═══════════════════════════════════════════════════════════════════════

REM Start bot in new window
start "Safety.uz Telegram Bot" cmd /k "cd /d bot && python telegram_bot.py"

REM Wait for bot to initialize
echo Waiting for bot to initialize...
timeout /t 5 /nobreak >nul

echo ✅ Bot started in separate window
echo.

echo [STEP 5/5] Server Status
echo ═══════════════════════════════════════════════════════════════════════
echo.
echo ✅ ALL SERVERS STARTED SUCCESSFULLY!
echo.
echo 📊 Backend Server:
echo    - URL: http://localhost:5000/
echo    - Window: "Safety.uz Backend Server"
echo.
echo 📡 Telegram Bot:
echo    - Health: http://localhost:10001/health
echo    - Window: "Safety.uz Telegram Bot"
echo.
echo 💡 To stop servers:
echo    - Close the respective windows, or
echo    - Run: taskkill /F /IM python.exe
echo.
echo ═══════════════════════════════════════════════════════════════════════
echo.

pause
