@echo off
setlocal

echo ========================================================
echo Safety.uz Local Bot Development Runner
echo ========================================================
echo.
echo This script helps run the bot locally without conflicting with Render production.
echo.

if exist .env.test (
    echo Loading test configuration from .env.test...
    for /f "tokens=*" %%a in (.env.test) do set %%a
)

if defined TELEGRAM_BOT_TOKEN_TEST (
    echo [INFO] Using TEST token for development. Safe to run.
    goto :run
)

echo [WARNING] No TELEGRAM_BOT_TOKEN_TEST found.
echo You are about to use the PRODUCTION token (from backend/.env).
echo.
echo If the production bot is running on Render, this will fail with a Conflict error.
echo.
echo To fix this:
echo 1. Create a new bot via @BotFather
echo 2. Create a file named '.env.test' in this folder
echo 3. Add: TELEGRAM_BOT_TOKEN_TEST=your_test_token_here
echo.
set /p confirm="Do you want to continue with PROD token? (y/n): "
if /i "%confirm%" neq "y" exit /b

:run
echo Starting bot...
python telegram_bot.py
pause
