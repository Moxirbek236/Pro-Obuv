#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# CLEAN AND RUN BOT SCRIPT
# ═══════════════════════════════════════════════════════════════════════

echo "🛑 Tozalanmoqda (Stopping all python servers)..."

# Kill all python processes related to the project
# This stops both the backend (app.py) and the bot (telegram_bot.py)
pkill -f "python.*telegram_bot.py" || true
pkill -f "python.*app.py" || true

# Wait for them to die
sleep 2

# Force kill if needed
pkill -9 -f "python.*telegram_bot.py" 2>/dev/null || true
pkill -9 -f "python.*app.py" 2>/dev/null || true

echo "✅ Barcha serverlar to'xtatildi."

# Check if we need to enter the bot directory
if [ -d "bot" ]; then
    cd bot
fi

# Activate virtual environment if available (checking standard locations)
if [ -f "../venv/bin/activate" ]; then
    echo "🔌 Virtual muhit faollashtirilmoqda (../venv)..."
    source ../venv/bin/activate
elif [ -f "../.venv/bin/activate" ]; then
    echo "🔌 Virtual muhit faollashtirilmoqda (../.venv)..."
    source ../.venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "🚀 Telegram bot ishga tushirilmoqda..."
if [ -f "telegram_bot.py" ]; then
    python3 telegram_bot.py
else
    echo "❌ Xatolik: telegram_bot.py topilmadi!"
fi
