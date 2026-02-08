# 🚀 Production Deployment Guide - Safety.uz

Bu qo'llanma Safety.uz platformasini production serverga deploy qilish bo'yicha to'liq ko'rsatmalar beradi.

## 📋 Deployment Arxitekturasi

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION SERVER                         │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Backend Server  │◄────────┤  Telegram Bot    │         │
│  │  (Flask)         │         │  (python-telegram│         │
│  │  Port: 5000      │         │   -bot)          │         │
│  │  safety.uz       │         │  Port: 10001     │         │
│  └────────┬─────────┘         └──────────────────┘         │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐                                       │
│  │  PostgreSQL DB   │                                       │
│  │  (Neon/Supabase) │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 1. Server Tayyorlash

### 1.1 Server Talablari
- **OS:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM:** Minimum 2GB (4GB tavsiya etiladi)
- **CPU:** 2 core (4 core tavsiya etiladi)
- **Disk:** 20GB bo'sh joy
- **Python:** 3.9+
- **PostgreSQL:** 14+ (yoki Neon/Supabase cloud database)

### 1.2 Kerakli Paketlarni O'rnatish

```bash
# System paketlarini yangilash
sudo apt update && sudo apt upgrade -y

# Python va kerakli kutubxonalarni o'rnatish
sudo apt install -y python3 python3-pip python3-venv git nginx supervisor

# PostgreSQL client (agar local DB kerak bo'lsa)
sudo apt install -y postgresql-client

# SSL sertifikat uchun (Let's Encrypt)
sudo apt install -y certbot python3-certbot-nginx
```

## 📦 2. Loyihani Deploy Qilish

### 2.1 Loyihani Serverga Ko'chirish

```bash
# Loyiha papkasini yaratish
sudo mkdir -p /var/www/safety.uz
sudo chown $USER:$USER /var/www/safety.uz

# Git orqali clone qilish
cd /var/www
git clone https://github.com/your-repo/safety.uz.git
cd safety.uz

# Yoki SCP orqali ko'chirish
# scp -r /path/to/Safety.uz user@server:/var/www/
```

### 2.2 Virtual Environment Yaratish

```bash
# Backend uchun
cd /var/www/safety.uz/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Bot uchun
cd /var/www/safety.uz/bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 Environment Variables Sozlash

```bash
# Backend .env faylini tahrirlash
cd /var/www/safety.uz/backend
nano .env
```

**MUHIM:** `.env` faylida quyidagilarni o'zgartiring:

```bash
# Production URL
BACKEND_URL=https://safety.uz

# Database (Neon yoki Supabase)
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require

# Flask Environment
FLASK_ENV=production
SECRET_KEY=your-very-secure-random-secret-key-here

# Server
HOST=0.0.0.0
PORT=5000

# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
```

## 🔐 3. Nginx Sozlash

### 3.1 Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/safety.uz
```

Quyidagi konfiguratsiyani qo'shing:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name safety.uz www.safety.uz;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name safety.uz www.safety.uz;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/safety.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/safety.uz/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logs
    access_log /var/log/nginx/safety.uz.access.log;
    error_log /var/log/nginx/safety.uz.error.log;

    # Max upload size
    client_max_body_size 50M;

    # Backend proxy
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /var/www/safety.uz/frontend/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media {
        alias /var/www/safety.uz/data;
        expires 7d;
    }
}
```

### 3.2 Nginx Faollashtirish

```bash
# Konfiguratsiyani faollashtirish
sudo ln -s /etc/nginx/sites-available/safety.uz /etc/nginx/sites-enabled/

# Nginx testdan o'tkazish
sudo nginx -t

# Nginx qayta yuklash
sudo systemctl restart nginx
```

### 3.3 SSL Sertifikat Olish

```bash
# Let's Encrypt SSL sertifikat
sudo certbot --nginx -d safety.uz -d www.safety.uz

# Auto-renewal tekshirish
sudo certbot renew --dry-run
```

## 🔄 4. Supervisor Sozlash (Process Management)

### 4.1 Backend Supervisor Config

```bash
sudo nano /etc/supervisor/conf.d/safety-backend.conf
```

```ini
[program:safety-backend]
command=/var/www/safety.uz/backend/venv/bin/python app.py
directory=/var/www/safety.uz/backend
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/supervisor/safety-backend.err.log
stdout_logfile=/var/log/supervisor/safety-backend.out.log
environment=PYTHONUNBUFFERED=1
```

### 4.2 Telegram Bot Supervisor Config

```bash
sudo nano /etc/supervisor/conf.d/safety-bot.conf
```

```ini
[program:safety-bot]
command=/var/www/safety.uz/bot/venv/bin/python telegram_bot.py
directory=/var/www/safety.uz/bot
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/supervisor/safety-bot.err.log
stdout_logfile=/var/log/supervisor/safety-bot.out.log
environment=PYTHONUNBUFFERED=1
```

### 4.3 Supervisor Faollashtirish

```bash
# Konfiguratsiyani qayta yuklash
sudo supervisorctl reread
sudo supervisorctl update

# Servislarni ishga tushirish
sudo supervisorctl start safety-backend
sudo supervisorctl start safety-bot

# Status tekshirish
sudo supervisorctl status
```

## 🎯 5. Production Deployment Buyruqlari

### 5.1 Birinchi Marta Deploy

```bash
# 1. Loyihani clone qilish
cd /var/www
git clone https://github.com/your-repo/safety.uz.git
cd safety.uz

# 2. Dependencies o'rnatish
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd ../bot && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate

# 3. .env sozlash
cd /var/www/safety.uz/backend
nano .env
# BACKEND_URL=https://safety.uz ga o'zgartiring

# 4. Nginx va Supervisor sozlash (yuqoridagi ko'rsatmalar bo'yicha)

# 5. Ishga tushirish
sudo supervisorctl start safety-backend safety-bot
```

### 5.2 Yangilanishlarni Deploy Qilish

```bash
# 1. Serverlarni to'xtatish
sudo supervisorctl stop safety-backend safety-bot

# 2. Yangilanishlarni olish
cd /var/www/safety.uz
git pull origin main

# 3. Dependencies yangilash (agar kerak bo'lsa)
cd backend && source venv/bin/activate && pip install -r requirements.txt && deactivate
cd ../bot && source venv/bin/activate && pip install -r requirements.txt && deactivate

# 4. Qayta ishga tushirish
sudo supervisorctl start safety-backend safety-bot

# 5. Status tekshirish
sudo supervisorctl status
```

## 📊 6. Monitoring va Logs

### 6.1 Loglarni Ko'rish

```bash
# Backend logs
sudo tail -f /var/log/supervisor/safety-backend.out.log
sudo tail -f /var/log/supervisor/safety-backend.err.log

# Bot logs
sudo tail -f /var/log/supervisor/safety-bot.out.log
sudo tail -f /var/log/supervisor/safety-bot.err.log

# Nginx logs
sudo tail -f /var/log/nginx/safety.uz.access.log
sudo tail -f /var/log/nginx/safety.uz.error.log
```

### 6.2 Status Tekshirish

```bash
# Supervisor status
sudo supervisorctl status

# Nginx status
sudo systemctl status nginx

# Port tekshirish
sudo netstat -tulpn | grep :5000
sudo netstat -tulpn | grep :10001
```

## 🔒 7. Security Best Practices

1. **Firewall Sozlash:**
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

2. **SSH Key Authentication:**
```bash
# Password authentication o'chirish
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
sudo systemctl restart sshd
```

3. **Fail2Ban O'rnatish:**
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 🚨 8. Troubleshooting

### Backend ishlamayapti
```bash
# Loglarni tekshirish
sudo tail -100 /var/log/supervisor/safety-backend.err.log

# Qo'lda ishga tushirish (debug uchun)
cd /var/www/safety.uz/backend
source venv/bin/activate
python app.py
```

### Bot ishlamayapti
```bash
# Loglarni tekshirish
sudo tail -100 /var/log/supervisor/safety-bot.err.log

# BACKEND_URL to'g'riligini tekshirish
cd /var/www/safety.uz/backend
cat .env | grep BACKEND_URL
```

### Database ulanish xatosi
```bash
# DATABASE_URL to'g'riligini tekshirish
cat /var/www/safety.uz/backend/.env | grep DATABASE_URL

# Database ulanishini test qilish
psql "postgresql://user:password@host:5432/dbname?sslmode=require"
```

## 📝 9. Environment Variables Cheat Sheet

### Development (Local)
```bash
BACKEND_URL=http://127.0.0.1:5000
FLASK_ENV=development
```

### Production (Server)
```bash
BACKEND_URL=https://safety.uz
FLASK_ENV=production
```

---

**Yaratilgan:** 2026-02-08  
**Versiya:** 1.0.0  
**Loyiha:** Safety.uz E-commerce Platform
