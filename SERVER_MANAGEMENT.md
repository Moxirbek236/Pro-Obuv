# 🚀 Safety.uz Server Management

Server boshqaruvi uchun skriptlar to'plami.

## 📋 Mavjud Skriptlar

### Windows Server

#### 1. **start_all_servers.bat** - Barcha serverlarni ishga tushirish
```cmd
start_all_servers.bat
```
Bu skript:
- ✅ Barcha mavjud Python jarayonlarini to'xtatadi
- ✅ Backend serverni alohida oynada ishga tushiradi (Port 5000)
- ✅ Telegram botni alohida oynada ishga tushiradi (Port 10001)
- ✅ Har bir server uchun status ko'rsatadi

#### 2. **backend/start_backend.bat** - Faqat Backend
```cmd
cd backend
start_backend.bat
```

#### 3. **bot/start_bot.bat** - Faqat Telegram Bot
```cmd
cd bot
start_bot.bat
```

### Linux/Unix Server

#### 1. **start_all_servers.sh** - Barcha serverlarni ishga tushirish
```bash
chmod +x start_all_servers.sh
./start_all_servers.sh
```
Bu skript:
- ✅ Barcha mavjud jarayonlarni to'xtatadi
- ✅ Backend serverni background'da ishga tushiradi
- ✅ Telegram botni background'da ishga tushiradi
- ✅ PID fayllarini yaratadi (logs/backend.pid, logs/bot.pid)
- ✅ Loglarni saqlaydi (logs/backend.log, logs/bot.log)

#### 2. **stop_all_servers.sh** - Barcha serverlarni to'xtatish
```bash
chmod +x stop_all_servers.sh
./stop_all_servers.sh
```

## 🔧 Tezkor Ishga Tushirish

### Windows
```cmd
# Loyiha papkasiga o'ting
cd D:\Safety.uz

# Barcha serverlarni ishga tushiring
start_all_servers.bat
```

### Linux/Unix
```bash
# Loyiha papkasiga o'ting
cd /path/to/Safety.uz

# Skriptga ruxsat bering
chmod +x start_all_servers.sh
chmod +x stop_all_servers.sh

# Ishga tushiring
./start_all_servers.sh

# To'xtatish uchun
./stop_all_servers.sh
```

## 📊 Server Manzillari

### Backend Server
- **URL:** http://localhost:5000/
- **Admin:** http://localhost:5000/admin
- **API:** http://localhost:5000/api/

### Telegram Bot
- **Health Check:** http://localhost:10001/health
- **Ping:** http://localhost:10001/ping

## 📋 Loglarni Ko'rish

### Windows
```cmd
# Backend log
type backend\backend.log

# Bot log
type bot\bot.log
```

### Linux/Unix
```bash
# Real-time backend log
tail -f logs/backend.log

# Real-time bot log
tail -f logs/bot.log
```

## 🛑 Serverlarni To'xtatish

### Windows
```cmd
# Barcha Python jarayonlarini to'xtatish
taskkill /F /IM python.exe

# Yoki har bir oynani yoping
```

### Linux/Unix
```bash
# Stop skriptidan foydalaning
./stop_all_servers.sh

# Yoki PID orqali
kill $(cat logs/backend.pid)
kill $(cat logs/bot.pid)
```

## ⚙️ Muhim Eslatmalar

1. **Environment Variables**: `.env` fayl to'g'ri sozlanganligiga ishonch hosil qiling
2. **Port Conflicts**: 5000 va 10001 portlar bo'sh bo'lishi kerak
3. **Database**: PostgreSQL/Neon database ulanishi ishlayotganligiga ishonch hosil qiling
4. **Telegram Token**: `TELEGRAM_BOT_TOKEN` sozlanganligini tekshiring

## 🔍 Troubleshooting

### Backend ishlamayapti
```bash
# Logni tekshiring
cat logs/backend.log  # Linux
type backend\backend.log  # Windows

# .env faylni tekshiring
cat backend/.env
```

### Bot ishlamayapti
```bash
# Logni tekshiring
cat logs/bot.log  # Linux
type bot\bot.log  # Windows

# Token mavjudligini tekshiring
echo $TELEGRAM_BOT_TOKEN  # Linux
```

### Port band
```bash
# Linux - portni tekshirish
lsof -i :5000
lsof -i :10001

# Windows - portni tekshirish
netstat -ano | findstr :5000
netstat -ano | findstr :10001
```

## 📞 Yordam

Muammo yuzaga kelsa:
1. Loglarni tekshiring
2. `.env` faylni tekshiring
3. Database ulanishini tekshiring
4. Portlar bo'sh ekanligini tekshiring

---

**Yaratilgan:** 2026-02-08  
**Versiya:** 1.0.0  
**Loyiha:** Safety.uz E-commerce Platform
