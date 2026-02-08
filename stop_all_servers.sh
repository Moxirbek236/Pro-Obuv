#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# STOP ALL SERVERS SCRIPT FOR LINUX/UNIX
# ═══════════════════════════════════════════════════════════════════════
# Purpose: Stop both Backend and Telegram Bot servers
# Usage: ./stop_all_servers.sh
# ═══════════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "   SAFETY.UZ - STOPPING ALL SERVERS"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Change to script directory
cd "$(dirname "$0")"

echo "Stopping Backend Server..."
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        echo "✅ Backend stopped (PID: $BACKEND_PID)"
    else
        echo "⚠️  Backend not running"
    fi
    rm -f logs/backend.pid
else
    echo "⚠️  Backend PID file not found"
fi

echo ""
echo "Stopping Telegram Bot..."
if [ -f "logs/bot.pid" ]; then
    BOT_PID=$(cat logs/bot.pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        kill $BOT_PID
        echo "✅ Bot stopped (PID: $BOT_PID)"
    else
        echo "⚠️  Bot not running"
    fi
    rm -f logs/bot.pid
else
    echo "⚠️  Bot PID file not found"
fi

# Additional cleanup - kill any remaining processes
echo ""
echo "Cleaning up remaining processes..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*telegram_bot.py" 2>/dev/null || true

sleep 2

echo ""
echo "✅ All servers stopped"
echo ""
