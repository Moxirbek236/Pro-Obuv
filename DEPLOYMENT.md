# Safety.uz - Complete Deployment Guide

Bu qo'llanma loyihani to'liq production muhitiga joylashtirish bo'yicha.

## Arxitektura

```
┌──────────────────────────────────────────────────────────┐
│                     PRODUCTION SETUP                      │
└──────────────────────────────────────────────────────────┘

┌─────────────────┐
│   Render.com    │  Frontend Server (Flask)
│   Frontend      │  https://safetyuz.onrender.com
│   Port: 10000   │  → Serves HTML/CSS/JS
└────────┬────────┘  → Calls Backend API
         │
         │ HTTP/AJAX
         ▼
┌─────────────────┐
│   Render.com    │  Backend API (Flask)
│   Backend       │  https://pro-obuv.onrender.com
│   Port: 10000   │  → Returns JSON data
└────────┬────────┘  → Manages business logic
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│   Render.com    │  │  Cloudinary     │
│   PostgreSQL    │  │  Image Storage  │
│   Database      │  │                 │
└─────────────────┘  └─────────────────┘

         ┌─────────────────┐
         │   Render.com    │  Telegram Bot (Background Worker)
         │   Bot Worker    │  → Listens to Telegram updates
         │                 │  → Calls Backend API
         └─────────────────┘
```

## 1. Backend Deployment (Render)

### Qadamlar:
1. **Render.com** ga kiring
2. **New Web Service** yarating
3. **GitHub** repository ni ulang
4. Sozlamalar:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --workers 2 --timeout 120`

### Environment Variables:
```bash
# Security
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production

# Database (Render PostgreSQL)
DATABASE_URL=postgresql://user:pass@host/dbname

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# CORS (Frontend URL)
FRONTEND_URL=https://safetyuz.onrender.com

# Bot (disable auto-start)
START_TELEGRAM_BOT=0
```

### Database Setup:
1. Render dashboardda **PostgreSQL** yarating
2. Connection string ni nusxalang
3. `DATABASE_URL` ga qo'ying
4. Migratsiyalarni ishga tushiring (agar bo'lsa)

## 2. Frontend Deployment (Render)

⚠️ **Muhim**: Netlify Flask app uchun mos emas. Render ishlatamiz.

### Qadamlar:
1. **Render.com** da yangi **Web Service** yarating
2. Sozlamalar:
   - Root Directory: `frontend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn server:app`

### Environment Variables:
```bash
BACKEND_URL=https://pro-obuv.onrender.com
SECRET_KEY=frontend-secret-key
PORT=10000
```

## 3. Telegram Bot Deployment (Render)

### Qadamlar:
1. **Render.com** da **Background Worker** yarating
2. Sozlamalar:
   - Root Directory: `bot`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python telegram_bot.py`

### Environment Variables:
```bash
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
FLASK_APP_URL=https://pro-obuv.onrender.com
```

## 4. Cloudinary (Rasmlar)

Rasmlar allaqachon Cloudinary ga ulangan.
Faqat environment variables to'g'ri sozlanganligini tekshiring.

## 5. Domain Sozlamalari (Ixtiyoriy)

Agar custom domain bo'lsa:
1. Render dashboardda **Custom Domain** qo'shing
2. DNS sozlamalarini yangilang:
   ```
   Type: CNAME
   Name: www
   Value: your-app.onrender.com
   ```

## 6. Testing

### Backend API:
```bash
curl https://pro-obuv.onrender.com/api/menu
```

### Frontend:
```
https://safetyuz.onrender.com
```

### Bot:
Telegram da botni toping va `/start` yuboring

## 7. Monitoring

- **Logs**: Render dashboardda har bir service uchun
- **Metrics**: CPU, Memory, Request count
- **Alerts**: Email orqali xatoliklar haqida xabar

## 8. Backup

- **Database**: Render auto-backup (paid plan)
- **Code**: GitHub repository
- **Images**: Cloudinary (cloud storage)

## 9. Cost Estimate

### Free Tier:
- Backend: Free (sleeps after 15 min)
- Frontend: Free (sleeps after 15 min)
- Bot: Free (always on)
- Database: Free (90 days, then expires)

### Paid Tier (Recommended):
- Backend: $7/month (Starter)
- Frontend: $7/month (Starter)
- Bot: Free (included)
- Database: $7/month (PostgreSQL)
- **Total**: ~$21/month

## 10. Troubleshooting

### Backend not responding:
- Check logs in Render dashboard
- Verify environment variables
- Check database connection

### Frontend shows errors:
- Verify `BACKEND_URL` is correct
- Check CORS settings in backend
- Review browser console for errors

### Bot not working:
- Verify `TELEGRAM_BOT_TOKEN`
- Check if worker is running
- Ensure only ONE bot instance is active

## Keyingi Qadamlar

1. ✅ Backend ni deploy qiling
2. ✅ Database yarating va ulangtiring
3. ✅ Frontend ni deploy qiling
4. ✅ Bot ni deploy qiling
5. ✅ Barcha environment variables ni sozlang
6. ✅ Test qiling
7. ✅ Custom domain ulang (ixtiyoriy)
8. ✅ Monitoring sozlang

Omad! 🚀
