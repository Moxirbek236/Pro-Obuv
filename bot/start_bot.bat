@echo off
REM ═══════════════════════════════════════════════════════════════════════
REM Telegram Bot Server Management Script for Windows
REM ═══════════════════════════════════════════════════════════════════════
REM Purpose: Start/restart Telegram bot with proper process management
REM Usage: start_bot.bat
REM ═══════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════════════
echo    TELEGRAM BOT SERVER - WINDOWS
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Change to bot directory
cd /d "%~dp0"

echo [1/4] Checking environment...
echo Current directory: %CD%

REM Check if telegram_bot.py exists
if not exist "telegram_bot.py" (
    echo.
    echo ❌ ERROR: telegram_bot.py not found!
    echo Please run this script from the bot directory.
    pause
    exit /b 1
)

echo ✅ Bot file found

REM Stop existing Python processes running telegram_bot.py
echo.
echo [2/4] Stopping existing bot processes...
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *telegram_bot*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq python.exe" /FI "COMMANDLINE eq *telegram_bot.py*" >nul 2>&1

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
    if exist "..\backend\.env" (
        echo ⚠️  Using .env from backend directory
    ) else (
        echo ❌ WARNING: .env file not found!
        echo Bot may not work without proper configuration.
    )
)

REM Start the bot
echo.
echo [4/4] Starting Telegram bot...
echo ═══════════════════════════════════════════════════════════════════════
echo.
echo 📡 Bot is starting...
echo 📊 Health endpoints will be available at:
echo    - http://localhost:10001/
echo    - http://localhost:10001/health
echo    - http://localhost:10001/ping
echo.
echo 💡 Press Ctrl+C to stop the bot
echo ═══════════════════════════════════════════════════════════════════════
echo.

REM Start bot with output to console and log file
python telegram_bot.py 2>&1 | tee bot.log

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Bot stopped successfully
) else (
    echo.
    echo ❌ Bot crashed with error code %ERRORLEVEL%
    echo 📋 Check bot.log for details
    pause
)
