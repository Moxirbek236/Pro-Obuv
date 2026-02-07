#!/bin/bash

# Server start script for Telegram bot
# This script handles bot process management and prevents conflicts

echo "🚀 Starting Telegram Bot Server..."

# Kill any existing Python processes
echo "🔄 Stopping existing processes..."
pkill -f "python telegram_bot.py" 2>/dev/null || true
pkill -f "python.*telegram" 2>/dev/null || true

# Wait for processes to stop
sleep 3

# Check if processes are still running
if pgrep -f "python telegram_bot.py" > /dev/null; then
    echo "⚠️  Warning: Some processes are still running"
    # Force kill
    pkill -9 -f "python telegram_bot.py" 2>/dev/null || true
    sleep 2
fi

# Set environment variables
export PYTHONUNBUFFERED=1
export PORT=${PORT:-10000}

# Check if token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ ERROR: TELEGRAM_BOT_TOKEN is not set!"
    echo "Please set token in your environment variables:"
    echo "export TELEGRAM_BOT_TOKEN='your_bot_token_here'"
    exit 1
fi

# Start the bot with proper signal handling
echo "✅ Starting bot on port $PORT..."
echo "📊 Bot will be available at health endpoints:"
echo "   - http://localhost:$PORT/"
echo "   - http://localhost:$PORT/health"
echo "   - http://localhost:$PORT/ping"
echo "📡 Use Ctrl+C to stop gracefully"

# Start with error handling and trap signals
trap 'echo "📡 Received signal, shutting down..."; exit 0' SIGTERM SIGINT

python telegram_bot.py 2>&1 | tee bot.log

# If script exits, show status
if [ $? -eq 0 ]; then
    echo "✅ Bot stopped successfully"
else
    echo "❌ Bot crashed with error code $?"
    echo "📋 Check bot.log for details"
fi
