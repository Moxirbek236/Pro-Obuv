@echo off
REM Server start script for Telegram bot (Windows)
REM This script handles bot process management and prevents conflicts

echo 🚀 Starting Telegram Bot Server...

REM Kill any existing Python processes
echo 🔄 Stopping existing processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

REM Wait for processes to stop
timeout /t 3 /nobreak >nul

REM Check if TELEGRAM_BOT_TOKEN is set
if "%TELEGRAM_BOT_TOKEN%"=="" (
    echo ❌ ERROR: TELEGRAM_BOT_TOKEN is not set!
    echo Please set the token in your environment variables:
    echo set TELEGRAM_BOT_TOKEN=your_bot_token_here
    echo Or create a .env file with the token
    pause
    exit /b 1
)

REM Set environment variables
set PYTHONUNBUFFERED=1
if "%PORT%"=="" set PORT=10000

echo ✅ Starting bot on port %PORT%...
echo 📊 Bot will be available at health endpoints:
echo    - http://localhost:%PORT%/
echo    - http://localhost:%PORT%/health
echo    - http://localhost:%PORT%/ping

REM Start the bot
echo 🤖 Starting Telegram bot...
python telegram_bot.py

REM If script exits, show status
if %ERRORLEVEL% EQU 0 (
    echo ✅ Bot stopped successfully
) else (
    echo ❌ Bot crashed with error code %ERRORLEVEL%
    echo 📋 Check the console output for details
)

pause
