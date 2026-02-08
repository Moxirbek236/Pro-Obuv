# 🚀 Tezkor Deployment - Safety.uz

## Production Serverga Deploy Qilish

### 1️⃣ .env Faylini Sozlash

**Backend `.env` faylida o'zgartiring:**

```bash
# Production URL (serveringiz manzili)
BACKEND_URL=https://safety.uz

# Yoki IP manzil
BACKEND_URL=http://your-server-ip:5000
```

### 2️⃣ Telegram Bot Sozlash

Bot endi `BACKEND_URL` dan ma'lumot oladi:
- ✅ Local development: `http://127.0.0.1:5000`
- ✅ Production: `https://safety.uz` yoki server IP

### 3️⃣ Serverda Ishga Tushirish

```bash
# Supervisor bilan (tavsiya etiladi)
sudo supervisorctl start safety-backend
sudo supervisorctl start safety-bot

# Yoki qo'lda
cd /var/www/safety.uz
./start_all_servers.sh
```

## 📋 Muhim Eslatmalar

1. **Backend va Bot alohida serverlarda:**
   - Backend: `safety.uz:5000` (yoki boshqa server)
   - Bot: Istalgan serverda (backend URL orqali ulanadi)

2. **BACKEND_URL to'g'ri sozlangan bo'lishi kerak:**
   ```bash
   # .env faylda
   BACKEND_URL=https://safety.uz  # Production
   # yoki
   BACKEND_URL=http://127.0.0.1:5000  # Local
   ```

3. **Bot API endpointlari:**
   - `/api/products` - Mahsulotlar
   - `/api/chat/receive` - Chat xabarlari

## 🔍 Tekshirish

```bash
# Backend ishlayotganini tekshirish
curl https://safety.uz/health

# Bot ishlayotganini tekshirish
curl http://bot-server:10001/health

# Loglarni ko'rish
sudo tail -f /var/log/supervisor/safety-backend.out.log
sudo tail -f /var/log/supervisor/safety-bot.out.log
```

## 📞 Yordam

To'liq qo'llanma: `DEPLOYMENT_GUIDE.md`
