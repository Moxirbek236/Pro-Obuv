# Telegram Bot Setup Guide

## Database Tables

The bot requires two PostgreSQL tables that are **automatically created** when the backend starts:

### bot_commands
Stores broadcast commands from the admin panel.
- `id`: Serial primary key
- `type`: Command type (broadcast, send_message)
- `payload`: JSONB - command data
- `status`: pending/completed/failed
- `created_at`: Timestamp
- `processed_at`: Timestamp (when bot processes)
- `error`: Error message if failed

### bot_users
Stores bot subscribers for broadcasts.
- `id`: Serial primary key
- `user_id`: Unique Telegram user ID
- `name`: User's display name
- `created_at`: First interaction timestamp
- `last_active`: Last interaction timestamp

## Automatic Initialization

Tables are created automatically when:
1. The backend starts (`get_db_pool()` is called)
2. Function `init_bot_tables()` runs once
3. Uses `CREATE TABLE IF NOT EXISTS` - safe to run multiple times

## Manual Initialization (If Needed)

If tables don't auto-create, run:

```bash
cd backend
python init_bot_tables.py
```

This script:
- Reads `DATABASE_URL` from environment
- Creates both tables
- Creates necessary indexes
- Safe to run multiple times

## Deployment on Render.com

### Backend Service
1. Environment variable `DATABASE_URL` must be set
2. Tables auto-create on first request
3. Check logs for: `✓ Bot tables initialized successfully`

### Bot Service
1. Set `BACKEND_URL` to your backend URL (e.g., `https://staff.safety.uz`)
2. Set `TELEGRAM_BOT_TOKEN`
3. Bot polls backend every 5 seconds for commands

## Troubleshooting

**Error**: `relation "bot_commands" does not exist`
- Tables didn't auto-create
- Run `python init_bot_tables.py` manually
- Check DATABASE_URL is correct
- Verify PostgreSQL connection

**Bot not receiving commands:**
- Check bot logs for polling errors
- Verify BACKEND_URL is accessible
- Test `/api/bot/commands/pending` endpoint

## Admin Panel Usage

1. Go to `/super-admin/bot-control`
2. Enter broadcast message
3. Optional: Add photo URL and buttons
4. Click "Yuborish"
5. Bot processes within 5 seconds
6. Check "Tarix" for status
