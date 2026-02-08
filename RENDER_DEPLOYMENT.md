# 🚀 Render.com Deployment Guide - Safety.uz

Bu qo'llanma Safety.uz platformasini Render.com serveriga deploy qilish bo'yicha to'liq ko'rsatmalar beradi.

## 📋 Render.com Deployment Arxitekturasi

```
┌─────────────────────────────────────────────────────────────┐
│                    RENDER.COM CLOUD                          │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Backend Service │◄────────┤  Bot Worker      │         │
│  │  (Web Service)   │         │  (Background)    │         │
│  │  safety-uz-      │         │  safety-uz-      │         │
│  │  backend         │         │  telegram-bot    │         │
│  │  .onrender.com   │         │                  │         │
│  └────────┬─────────┘         └──────────────────┘         │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐                                       │
│  │  PostgreSQL DB   │                                       │
│  │  (Neon/Supabase) │                                       │
│  │  External        │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 1. Tayyorgarlik

### 1.1 Kerakli Ma'lumotlar

- ✅ GitHub repository (public yoki private)
- ✅ Neon/Supabase PostgreSQL database URL
- ✅ Telegram Bot Token
- ✅ Uzum API credentials (agar kerak bo'lsa)

### 1.2 Fayllarni Tekshirish

Loyihada quyidagi fayllar bo'lishi kerak:

```
Safety.uz/
├── render.yaml                 # ✅ Render konfiguratsiyasi
├── backend/
│   ├── requirements.txt        # ✅ Backend dependencies
│   ├── app.py                  # ✅ Backend entry point
│   └── .env.example            # Environment variables namunasi
└── bot/
    ├── requirements.txt        # ✅ Bot dependencies (psycopg2-binary qo'shilgan)
    └── telegram_bot.py         # ✅ Bot entry point
```

## 📦 2. GitHub Repository Tayyorlash

### 2.1 Repository Yaratish

```bash
# Local loyihani Git repository qilish
cd /path/to/Safety.uz
git init
git add .
git commit -m "Initial commit for Render deployment"

# GitHub'ga push qilish
git remote add origin https://github.com/your-username/safety-uz.git
git branch -M main
git push -u origin main
```

### 2.2 .gitignore Tekshirish

`.gitignore` faylida quyidagilar bo'lishi kerak:

```
.env
*.pyc
__pycache__/
venv/
*.log
*.pid
.DS_Store
```

## 🚀 3. Render.com'da Deploy Qilish

### 3.1 Render.com Account Yaratish

1. [render.com](https://render.com) ga kiring
2. GitHub account bilan sign up qiling
3. GitHub repository'ga ruxsat bering

### 3.2 Blueprint Deploy (Tavsiya Etiladi)

**Usul 1: render.yaml orqali (Eng oson)**

1. Render Dashboard'ga kiring
2. "New" → "Blueprint" tugmasini bosing
3. GitHub repository'ni tanlang
4. `render.yaml` fayli avtomatik topiladi
5. "Apply" tugmasini bosing

**Render avtomatik ravishda yaratadi:**
- ✅ Backend Web Service
- ✅ Telegram Bot Worker Service

### 3.3 Manual Deploy (Agar Blueprint ishlamasa)

#### Backend Service Yaratish:

1. "New" → "Web Service" tugmasini bosing
2. GitHub repository'ni tanlang
3. Quyidagi sozlamalarni kiriting:

```
Name: safety-uz-backend
Region: Oregon (yoki yaqin region)
Branch: main
Root Directory: (bo'sh qoldiring)
Runtime: Python 3
Build Command: cd backend && pip install -r requirements.txt
Start Command: cd backend && python app.py
Plan: Free
```

#### Bot Worker Yaratish:

1. "New" → "Background Worker" tugmasini bosing
2. GitHub repository'ni tanlang
3. Quyidagi sozlamalarni kiriting:

```
Name: safety-uz-telegram-bot
Region: Oregon (yoki yaqin region)
Branch: main
Root Directory: (bo'sh qoldiring)
Runtime: Python 3
Build Command: cd bot && pip install -r requirements.txt
Start Command: cd bot && python telegram_bot.py
Plan: Free
```

## ⚙️ 4. Environment Variables Sozlash

### 4.1 Backend Service Environment Variables

Render Dashboard → Backend Service → Environment → Add Environment Variable:

```bash
# Flask Settings
FLASK_ENV=production
SECRET_KEY=your-random-secret-key-here
PORT=5000
HOST=0.0.0.0

# Database (Neon/Supabase)
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require

# Telegram Bot
TELEGRAM_BOT_TOKEN=8500801234:AAEs9ZIg5cuMMt9y0kHnfbyh-fq41CRyuEQ

# Backend URL (Render URL)
BACKEND_URL=https://safety-uz-backend.onrender.com

# Uzum API (agar kerak bo'lsa)
UZUM_API_TOKEN=your-uzum-token
UZUM_SHOP_ID=64816

# SMTP (Email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=safetyproobuv@gmail.com
SMTP_PASS=your-smtp-password

# Other settings
PYTHONUNBUFFERED=1
```

### 4.2 Bot Worker Environment Variables

Render Dashboard → Bot Worker → Environment → Add Environment Variable:

```bash
# Database (same as backend)
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require

# Telegram Bot
TELEGRAM_BOT_TOKEN=8500801234:AAEs9ZIg5cuMMt9y0kHnfbyh-fq41CRyuEQ

# Backend URL (Render backend URL)
BACKEND_URL=https://safety-uz-backend.onrender.com

# Other settings
PYTHONUNBUFFERED=1
PORT=10001
```

## 🔍 5. Deployment Tekshirish

### 5.1 Build Logs Ko'rish

1. Render Dashboard → Service → Logs
2. Build jarayonini kuzating
3. Xatolarni tekshiring

### 5.2 Service Status

```
✅ Backend Service: Running
✅ Bot Worker: Running
```

### 5.3 Health Check

```bash
# Backend health check
curl https://safety-uz-backend.onrender.com/health

# Javob:
{"status": "ok", "timestamp": "..."}
```

### 5.4 Telegram Bot Test

Telegram'da botingizga:
```
/start
/products
```

## 🔧 6. Troubleshooting

### Build Failed - psycopg2 Error

**Xato:**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Yechim:**
```bash
# bot/requirements.txt faylida tekshiring:
psycopg2-binary>=2.9.0
```

### Backend Service Crashed

**Logs tekshirish:**
1. Render Dashboard → Backend Service → Logs
2. Xatolarni o'qing

**Keng tarqalgan xatolar:**
- Database connection error → `DATABASE_URL` to'g'riligini tekshiring
- Port already in use → Render avtomatik port beradi, `PORT` env var o'zgartirmang

### Bot Not Responding

**Tekshirish:**
1. Bot Worker logs'ni ko'ring
2. `BACKEND_URL` to'g'riligini tekshiring
3. `TELEGRAM_BOT_TOKEN` to'g'riligini tekshiring

```bash
# Logs'da quyidagi xabarni qidiring:
"Starting Telegram bot"
"✅ HTTPXRequest configured"
```

### Database Connection Error

**Xato:**
```
psycopg2.OperationalError: could not connect to server
```

**Yechim:**
1. `DATABASE_URL` formatini tekshiring:
   ```
   postgresql://user:password@host:5432/dbname?sslmode=require
   ```
2. Neon/Supabase database ishlab turganini tekshiring
3. IP whitelist'ni tekshiring (Render IP'larini qo'shing)

## 📊 7. Monitoring

### 7.1 Render Dashboard

- **Metrics:** CPU, Memory, Request count
- **Logs:** Real-time logs
- **Events:** Deploy history

### 7.2 Custom Domain (Opsional)

1. Render Dashboard → Backend Service → Settings
2. "Custom Domain" → Add domain
3. DNS settings'ni yangilang:
   ```
   CNAME: safety.uz → safety-uz-backend.onrender.com
   ```

## 💰 8. Pricing

### Free Plan Limitations:
- ✅ 750 soat/oy (bitta service uchun)
- ✅ Auto-sleep after 15 minutes inactivity
- ✅ 512 MB RAM
- ⚠️ Cold start (15-30 soniya)

### Paid Plan ($7/month):
- ✅ No auto-sleep
- ✅ 1 GB RAM
- ✅ Faster performance

## 🔄 9. Yangilanishlarni Deploy Qilish

### Auto Deploy (Tavsiya Etiladi)

Render avtomatik deploy qiladi:
```bash
# Local'da o'zgarishlar qiling
git add .
git commit -m "Update feature"
git push origin main

# Render avtomatik deploy boshlaydi
```

### Manual Deploy

1. Render Dashboard → Service
2. "Manual Deploy" → "Deploy latest commit"

## 📝 10. Render.yaml Konfiguratsiyasi

`render.yaml` fayli loyihada mavjud. Bu fayl orqali:
- ✅ Backend va Bot bir vaqtda deploy qilinadi
- ✅ Environment variables avtomatik sozlanadi
- ✅ Build va start commands avtomatik bajariladi

## 🎯 11. Production Checklist

- [ ] `requirements.txt` fayllarida `psycopg2-binary` bor
- [ ] `.env` faylida `BACKEND_URL` to'g'ri sozlangan
- [ ] GitHub repository'ga push qilingan
- [ ] Render'da Backend Service yaratilgan
- [ ] Render'da Bot Worker yaratilgan
- [ ] Environment variables to'liq sozlangan
- [ ] Database (Neon/Supabase) ishlayapti
- [ ] Telegram Bot Token to'g'ri
- [ ] Health check ishlayapti
- [ ] Telegram bot javob berayapti

---

**Yaratilgan:** 2026-02-08  
**Versiya:** 1.0.0  
**Loyiha:** Safety.uz E-commerce Platform  
**Platform:** Render.com
