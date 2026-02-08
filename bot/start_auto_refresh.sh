#!/bin/bash

# Auto-refresh Telegram bot with Uzum products
echo "🚀 Auto-refresh Telegram Bot starting..."

# Kill existing processes
pkill -f "python telegram_bot.py" 2>/dev/null || true
pkill -f "python auto_refresh.py" 2>/dev/null || true
sleep 2

# Set environment
export PYTHONUNBUFFERED=1
export PORT=${PORT:-10000}
export REFRESH_MODE=auto

# Check token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ ERROR: TELEGRAM_BOT_TOKEN is not set!"
    exit 1
fi

echo "✅ Starting auto-refresh system..."
echo "📊 Mahsulotlar har 5 daqiqada yangilanadi"
echo "🤖 Bot doimiy ishlaydi"

# Start auto-refresh in background
echo "🔄 Auto-refresh service starting..."
nohup python auto_refresh.py > refresh.log 2>&1 &
REFRESH_PID=$!

# Wait for refresh to start
sleep 2

# Start bot
echo "🤖 Starting Telegram bot..."
python telegram_bot.py &
BOT_PID=$!

echo "✅ System started!"
echo "🔄 Auto-refresh PID: $REFRESH_PID"
echo "🤖 Bot PID: $BOT_PID"
echo "📋 Refresh logs: refresh.log"
echo "📋 Bot logs: telegram_bot.log"
echo "📊 Health: http://localhost:$PORT/health"

# Save PIDs
echo $REFRESH_PID > refresh.pid
echo $BOT_PID > bot.pid

# Monitor both processes
wait
