#!/bin/bash

# Background bot runner for production
echo "🚀 Starting Telegram Bot in Background..."

# Kill existing processes
pkill -f "python telegram_bot.py" 2>/dev/null || true
sleep 2

# Set environment
export PYTHONUNBUFFERED=1
export PORT=${PORT:-10000}

# Check token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ ERROR: TELEGRAM_BOT_TOKEN is not set!"
    exit 1
fi

# Start bot in background with nohup
echo "🤖 Starting bot in background..."
nohup python telegram_bot.py > bot.log 2>&1 &
BOT_PID=$!

echo "✅ Bot started with PID: $BOT_PID"
echo "📋 Logs: bot.log"
echo "📊 Health: http://localhost:$PORT/health"
echo "🛑 To stop: kill $BOT_PID"

# Save PID for later use
echo $BOT_PID > bot.pid

# Check if bot is running
sleep 3
if ps -p $BOT_PID > /dev/null; then
    echo "✅ Bot is running successfully!"
else
    echo "❌ Bot failed to start. Check bot.log"
    exit 1
fi
