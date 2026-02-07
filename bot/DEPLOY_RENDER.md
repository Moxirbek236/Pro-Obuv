# Telegram Bot Deployment Guide (Render.com)

## Deployment Steps

### 1. Create New Background Worker on Render
- Go to https://render.com
- Click "New +" → "Background Worker"
- Connect your GitHub repository
- Select `bot` directory as root

### 2. Configure Build Settings
- **Name**: `safety-uz-telegram-bot`
- **Region**: Frankfurt (or closest to your users)
- **Branch**: `main`
- **Root Directory**: `bot`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python telegram_bot.py`

### 3. Environment Variables
Set these in Render dashboard:

```
# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=your-bot-token-here

# Backend API URL
FLASK_APP_URL=https://pro-obuv.onrender.com

# Database (if bot needs direct DB access)
# Usually bot should use API, not direct DB
# DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 4. Testing
1. Start the bot on Render
2. Open Telegram and search for your bot
3. Send `/start` command
4. Check logs in Render dashboard

## Important Notes

- **Always On**: Background workers don't sleep (even on free tier)
- **Logs**: Monitor logs for errors
- **API Communication**: Bot should communicate with Backend via API
- **No Direct DB Access**: Bot should NOT access database directly
- **Restart**: Auto-restarts on crash

## Troubleshooting

### Bot not responding
1. Check if worker is running in Render dashboard
2. Verify `TELEGRAM_BOT_TOKEN` is correct
3. Check logs for errors
4. Ensure `FLASK_APP_URL` points to correct backend

### Conflict errors
- Only ONE instance of bot should run
- If running locally, stop it before deploying
- Check no other services are running the bot
