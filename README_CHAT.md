Telegram bot + Website AI chat setup

Overview

- `bot/telegram_bot.py` - minimal telegram bot scaffold using python-telegram-bot. It can forward messages to the Flask app via `/api/chat/receive`.
- `static/chat_widget.js` - lightweight web chat widget that posts messages to `/api/chat/send` and displays AI replies.
- `app.py` - now exposes `/api/chat/receive` and `/api/chat/send` plus the `ai_respond` helper.

Setup

1. Install dependencies: the project already uses `requirements.txt`. Add `python-telegram-bot` if you want the telegram bot:

```powershell
pip install -r requirements.txt
pip install python-telegram-bot==13.XX  # or latest compatible version
```

2. Environment variables (recommended in `.env`):

- `TELEGRAM_BOT_TOKEN` - your Telegram bot token
- `FLASK_APP_URL` - public URL of your Flask app (used by the bot to contact the site)
- `OPENAI_API_KEY` - optional, for using OpenAI GPT for AI replies

3. Running the bot locally (polling):

```powershell
python bot/telegram_bot.py
```

4. Running the Flask app: follow your existing run instructions (e.g., `python run.py` or `gunicorn ...`). Ensure the site is reachable from the bot if using webhooks or requests.

Notes & next improvements

- The `ai_respond` function uses OpenAI if `OPENAI_API_KEY` is set. Otherwise it replies with simple rule-based multilingual shortcuts.
- The current chat persistence is a minimal `chat_messages` table and is created on first use.
- For production AI, integrate a proper OpenAI client, add rate limiting, and sanitize inputs.
- For Telegram product browsing, `bot/telegram_bot.py` calls `/api/menu-search` — you can extend it to send detailed product views by hitting `/product/<id>` and including images + social links.

If you want, I can:

- Wire the product detail flow (show 3 images + social links + option selection) for the Telegram bot messages.
- Add a staff notification mechanism so when a user places "Buy now" from Telegram, a new order entry appears for staff and the staff chat is notified.
- Improve AI responses with multilingual prompts and conversation context storage.
