# 🚀 Deployment Guide - PostgreSQL/Supabase Production

This guide provides step-by-step instructions for deploying the application with PostgreSQL (Supabase) in production.

---

## 📋 Pre-Deployment Checklist

### ✅ Required Items

- [ ] Supabase account created
- [ ] PostgreSQL database provisioned
- [ ] SSL certificate configured (automatic with Supabase)
- [ ] Environment variables prepared
- [ ] Application tested locally with PostgreSQL
- [ ] Database schema verified

---

## 1️⃣ Supabase Setup

### Create a New Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Choose your organization
4. Enter project details:
   - **Name**: Your project name
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
5. Click "Create new project"
6. Wait for the project to initialize (~2 minutes)

### Get Connection Details

1. Go to **Settings** → **Database**
2. Under "Connection string", select **URI**
3. Copy the connection string (format):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
4. **Important**: Add `?sslmode=require` to the end:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
   ```

### Get API Keys

1. Go to **Settings** → **API**
2. Copy the following:
   - **anon public** key → `SUPABASE_PUBLISHABLE_KEY`
   - **service_role** key → `SUPABASE_SECRET_KEY`

---

## 2️⃣ Environment Configuration

### Create Production .env

```env
# ═══════════════════════════════════════════════════════════════
# PRODUCTION ENVIRONMENT CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-long-random-secret-key-here-minimum-32-chars

# ═══════════════════════════════════════════════════════════════
# DATABASE (PostgreSQL / Supabase)
# ═══════════════════════════════════════════════════════════════
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres?sslmode=require

# Supabase API Keys
SUPABASE_PUBLISHABLE_KEY=sb_publishable_your_key
SUPABASE_SECRET_KEY=sb_secret_your_key

# Connection Pool Settings (adjust based on your plan)
DB_POOL_MAX_CONNECTIONS=20

# ═══════════════════════════════════════════════════════════════
# SECURITY
# ═══════════════════════════════════════════════════════════════
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Admin Credentials (CHANGE THESE!)
SUPER_ADMIN_USERNAME=your_admin_username
SUPER_ADMIN_PASSWORD=your_strong_password

# Swagger UI Credentials
SWAGGER_USER=your_swagger_user
SWAGGER_PASS=your_swagger_password

# ═══════════════════════════════════════════════════════════════
# EXTERNAL SERVICES
# ═══════════════════════════════════════════════════════════════
# Cloudinary (for image storage)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# SMTP (for email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_FROM=your_email@gmail.com

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token

# Maps
YANDEX_GEOCODER_API=your_api_key
YANDEX_MAPS_API=your_api_key

# ═══════════════════════════════════════════════════════════════
# PERFORMANCE
# ═══════════════════════════════════════════════════════════════
THREAD_POOL_MAX_WORKERS=10
LOG_LEVEL=INFO

# Redis (optional)
REDIS_URL=memory://  # or redis://your-redis-url:6379

# Server
PORT=5000
HOST=0.0.0.0
```

---

## 3️⃣ Database Initialization

### Option A: Using Supabase SQL Editor

1. Go to your Supabase project
2. Click on **SQL Editor**
3. Run the schema creation script from `database/schema_export.sql`

### Option B: Using Migration Script

1. SSH into your server
2. Run the migration verification:

```bash
python scripts/verify_postgresql_migration.py
```

---

## 4️⃣ Hosting Deployment

### Option A: Render.com

1. Create a new **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Add environment variables from `.env`
5. Deploy

### Option B: Railway

1. Create a new project
2. Connect your repository
3. Add environment variables
4. Deploy automatically

### Option C: Heroku

1. Create a new app
2. Add Postgres add-on (or use Supabase)
3. Set config vars:
```bash
heroku config:set DATABASE_URL="postgresql://..."
heroku config:set SECRET_KEY="your-secret"
# ... add all env vars
```
4. Deploy:
```bash
git push heroku main
```

### Option D: VPS/Docker

1. Build Docker image:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "4"]
```

2. Run with Docker:
```bash
docker build -t safety-uz .
docker run -d -p 5000:5000 --env-file .env safety-uz
```

---

## 5️⃣ Post-Deployment Verification

### Run Health Checks

```bash
# Check database connection
python scripts/verify_postgresql_migration.py

# List all tables
python list_pg_tables.py

# Test API endpoints
curl https://your-domain/api/health
curl https://your-domain/api/translations
```

### Monitor Logs

```bash
# Render.com
# View in dashboard under "Logs"

# Heroku
heroku logs --tail

# Docker
docker logs -f container_name
```

---

## 6️⃣ Common Issues & Solutions

### Issue: Connection Timeout

**Symptom**: `connection timed out` or `SSL handshake failed`

**Solutions**:
1. Verify SSL mode: `?sslmode=require`
2. Check firewall rules on your hosting provider
3. Verify Supabase project is active (not paused)

### Issue: Too Many Connections

**Symptom**: `remaining connection slots are reserved`

**Solutions**:
1. Reduce `DB_POOL_MAX_CONNECTIONS` (try 10)
2. Enable connection pooling in Supabase (pgBouncer mode)
3. Ensure connections are properly closed

### Issue: Query Timeout

**Symptom**: Slow queries or timeouts

**Solutions**:
1. Add indexes for frequently queried columns
2. Use EXPLAIN ANALYZE to optimize queries
3. Check Supabase dashboard for slow query logs

### Issue: Authentication Errors

**Symptom**: `FATAL: password authentication failed`

**Solutions**:
1. Verify password in `DATABASE_URL`
2. Check for special characters (URL encode them)
3. Reset database password in Supabase

---

## 7️⃣ Security Best Practices

### ✅ Do's

- Use environment variables for all secrets
- Enable SSL for all database connections
- Set strong admin passwords
- Use HTTPS for all production traffic
- Rotate API keys regularly
- Enable RLS (Row Level Security) in Supabase

### ❌ Don'ts

- Never commit `.env` to version control
- Don't use default passwords
- Don't expose service_role key to clients
- Don't disable SSL in production
- Don't log sensitive data

---

## 8️⃣ Backup & Recovery

### Automated Backups

Supabase provides automatic daily backups on Pro plan.

### Manual Backup

```bash
# Export data using pg_dump
pg_dump "postgresql://..." > backup.sql

# Or use Supabase dashboard:
# Settings → Database → Backups → Create backup
```

### Recovery

```bash
# Restore from backup
psql "postgresql://..." < backup.sql
```

---

## 9️⃣ Monitoring & Maintenance

### Supabase Dashboard

- Monitor database size
- View slow query logs
- Track API usage
- Check connection count

### Application Monitoring

- Set up error tracking (Sentry, etc.)
- Monitor response times
- Track error rates
- Set up alerts for critical issues

---

## 📞 Support

For issues:
1. Check the logs first
2. Review `docs/POSTGRESQL_MIGRATION_COMPLETED.md`
3. Run the verification script
4. Check Supabase status page

---

**Good luck with your deployment! 🎉**
