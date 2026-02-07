# Backend Deployment Guide (Render.com)

## Deployment Steps

### 1. Create New Web Service on Render
- Go to https://render.com
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Select `backend` directory as root

### 2. Configure Build Settings
- **Name**: `pro-obuv-backend`
- **Region**: Frankfurt (or closest to your users)
- **Branch**: `main`
- **Root Directory**: `backend`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --workers 2 --timeout 120 --bind 0.0.0.0:$PORT`

### 3. Environment Variables
Set these in Render dashboard:

```
# Database (if using external PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Or for SQLite (not recommended for production)
# DATABASE_PATH=./database/database.sqlite3

# Security
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=production

# Cloudinary (already configured)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Frontend URL (for CORS)
FRONTEND_URL=https://safetyuz.netlify.app

# Telegram Bot (set to 0, bot runs separately)
START_TELEGRAM_BOT=0

# Optional
YANDEX_GEOCODER_API=your-yandex-api-key
```

### 4. Database Migration
If using PostgreSQL on Render:
1. Create a PostgreSQL database on Render
2. Copy the connection string
3. Update `DATABASE_URL` environment variable
4. Run migrations (if you have migration scripts)

### 5. Static Files
- Static files are served from `frontend/static`
- Ensure `frontend` folder is accessible from `backend`
- Or configure CDN for static assets

### 6. Health Check
Render will ping `/` to check if app is running.
Ensure your root route returns 200 OK.

## Post-Deployment

1. Test API endpoints: `https://pro-obuv.onrender.com/api/menu`
2. Check logs in Render dashboard
3. Monitor performance and errors

## Important Notes

- **Free tier**: App sleeps after 15 min of inactivity
- **Paid tier**: Recommended for production
- **Database**: Use PostgreSQL for production (not SQLite)
- **Backups**: Enable automatic backups in Render
