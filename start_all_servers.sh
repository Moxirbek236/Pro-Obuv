#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# FULL SERVER MANAGEMENT SCRIPT FOR LINUX/UNIX
# ═══════════════════════════════════════════════════════════════════════
# Purpose: Start/restart both Backend and Telegram Bot servers
# Usage: ./start_all_servers.sh
# ═══════════════════════════════════════════════════════════════════════

set -e  # Exit on error

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "   SAFETY.UZ - FULL SERVER STARTUP"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Change to script directory
cd "$(dirname "$0")"

echo "[STEP 1/5] Stopping all existing processes..."
echo "═══════════════════════════════════════════════════════════════════════"

# Kill all Python processes related to our app
echo "Stopping backend processes..."
pkill -f "python.*app.py" 2>/dev/null || true

echo "Stopping bot processes..."
pkill -f "python.*telegram_bot.py" 2>/dev/null || true

# Wait for processes to stop
sleep 3

# Force kill if still running
if pgrep -f "python.*app.py" > /dev/null; then
    echo "Force killing backend..."
    pkill -9 -f "python.*app.py" 2>/dev/null || true
fi

if pgrep -f "python.*telegram_bot.py" > /dev/null; then
    echo "Force killing bot..."
    pkill -9 -f "python.*telegram_bot.py" 2>/dev/null || true
fi

sleep 2

echo "✅ All processes stopped"
echo ""

echo "[STEP 2/5] Checking project structure..."
echo "═══════════════════════════════════════════════════════════════════════"

# Check if backend directory exists
if [ ! -f "backend/app.py" ]; then
    echo "❌ ERROR: backend/app.py not found!"
    exit 1
fi
echo "✅ Backend found"

# Check if bot directory exists
if [ ! -f "bot/telegram_bot.py" ]; then
    echo "❌ ERROR: bot/telegram_bot.py not found!"
    exit 1
fi
echo "✅ Bot found"
echo ""

echo "[STEP 3/5] Starting Backend Server..."
echo "═══════════════════════════════════════════════════════════════════════"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start backend in background
cd backend
nohup python app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
cd ..

# Wait for backend to initialize
echo "Waiting for backend to initialize..."
sleep 5

# Check if backend is still running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend started (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start! Check logs/backend.log"
    exit 1
fi
echo ""

echo "[STEP 4/5] Starting Telegram Bot..."
echo "═══════════════════════════════════════════════════════════════════════"

# Start bot in background
cd bot
nohup python telegram_bot.py > ../logs/bot.log 2>&1 &
BOT_PID=$!
echo $BOT_PID > ../logs/bot.pid
cd ..

# Wait for bot to initialize
echo "Waiting for bot to initialize..."
sleep 5

# Check if bot is still running
if ps -p $BOT_PID > /dev/null; then
    echo "✅ Bot started (PID: $BOT_PID)"
else
    echo "❌ Bot failed to start! Check logs/bot.log"
    exit 1
fi
echo ""

echo "[STEP 5/5] Server Status"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "✅ ALL SERVERS STARTED SUCCESSFULLY!"
echo ""
echo "📊 Backend Server:"
echo "   - URL: http://localhost:5000/"
echo "   - PID: $BACKEND_PID"
echo "   - Log: logs/backend.log"
echo ""
echo "📡 Telegram Bot:"
echo "   - Health: http://localhost:10001/health"
echo "   - PID: $BOT_PID"
echo "   - Log: logs/bot.log"
echo ""
echo "💡 To stop servers:"
echo "   - Run: ./stop_all_servers.sh"
echo "   - Or: kill $BACKEND_PID $BOT_PID"
echo ""
echo "📋 To view logs:"
echo "   - Backend: tail -f logs/backend.log"
echo "   - Bot: tail -f logs/bot.log"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
