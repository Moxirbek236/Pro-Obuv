# Render Deployment Guide for Telegram Bot

## 🚀 Serverga yuklash uchun kerakli fayllar:

### 1. Asosiy fayllar:
- ✅ `telegram_bot.py` - Bot kodlari
- ✅ `requirements.txt` - Python kutubxonalari
- ✅ `Procfile` - Render uchun konfiguratsiya
- ✅ `.env` - Token va boshqa sozlamalar

### 2. Server start skriptlari:
- ✅ `start_server.sh` - Linux/Mac uchun
- ✅ `start_server.bat` - Windows uchun
- ✅ `Dockerfile` - Docker uchun

## 📋 Render uchun qo'shimcha sozlamalar:

### Build Command:
```bash
# Agar kerak bo'lsa, build command qo'shing
pip install -r requirements.txt
```

### Start Command:
```bash
# Render avtomatik Procfile dan foydalanadi
# Lekin qo'lda qo'shish mumkin:
python telegram_bot.py
```

### Environment Variables:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
PORT=10000
PYTHONUNBUFFERED=1
```

## 🔧 Qanday ishlatish:

### 1. Local server (Windows):
```bash
# CMD ni oching
start_server.bat
```

### 2. Local server (Linux/Mac):
```bash
# Terminalda
chmod +x start_server.sh
./start_server.sh
```

### 3. Render ga yuklash:
1. GitHub ga yuklang
2. Render da yangi Web Service yarating
3. GitHub repository ni ulang
4. Environment variables ni sozlang
5. Deploy qiling

## 🛠️ Muammolarni hal qilish:

### "Another bot process is running" xatosi:
- ✅ `start_server.bat` ishlatin (Windows)
- ✅ `start_server.sh` ishlatin (Linux)
- ✅ Yoki qo'lda: `taskkill /F /IM python.exe`

### Token topilmadi:
- ✅ `.env` fayl yarating:
```
TELEGRAM_BOT_TOKEN=your_actual_token
PORT=10000
```

### Internet aloqasi muammosi:
- ✅ Firewall tekshiring
- ✅ Proxy sozlamalari
- ✅ VPN dan foydalaning

## 📊 Monitoring:
- Health check: `http://your-app-url/health`
- Logs: Render dashboard
- Bot test: `/test` komandasi

## ✅ Tayyor!
Bot endi serverga yuklashga tayyor! 🚀
