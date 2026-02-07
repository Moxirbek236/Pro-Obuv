# Frontend Deployment Guide (Netlify)

## Important: Flask on Netlify Limitation

⚠️ **Netlify is optimized for static sites and serverless functions, NOT full Flask apps.**

For Flask app hosting, consider these alternatives:
1. **Render.com** (Recommended) - Supports Flask natively
2. **Heroku** - Good Flask support
3. **Railway.app** - Modern alternative
4. **Vercel** - With Python runtime

## Option 1: Deploy to Render (Recommended)

### Steps:
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Configure:
   - **Root Directory**: `frontend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn server:app --bind 0.0.0.0:$PORT`
   - **Environment Variables**:
     ```
     BACKEND_URL=https://pro-obuv.onrender.com
     SECRET_KEY=your-secret-key
     PORT=10000
     ```

## Option 2: Static Export (Netlify-friendly)

If you want to use Netlify, you need to:
1. Convert Flask templates to static HTML
2. Use JavaScript to fetch data from Backend API
3. Deploy static files to Netlify

### Steps for Static Export:
```bash
# This requires significant refactoring
# All dynamic content must be loaded via JavaScript
```

## Option 3: Netlify Functions (Advanced)

Use Netlify Functions as a proxy:
1. Create serverless functions in `netlify/functions/`
2. Each function proxies to Backend API
3. Serve static HTML from Netlify

This is complex and not recommended for full Flask apps.

## Recommended Architecture

```
┌─────────────────┐
│   Netlify       │  → Static HTML/CSS/JS only
│   (Frontend)    │  → Fetches data via JavaScript
└────────┬────────┘
         │
         │ AJAX/Fetch
         ▼
┌─────────────────┐
│   Render        │  → Flask Backend API
│   (Backend)     │  → Returns JSON data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │  → Database
│   (Render)      │
└─────────────────┘
```

## Current Setup

Your current `frontend/server.py` is a Flask app, which:
- ✅ Works great on **Render**
- ❌ Doesn't work well on **Netlify**

## Recommendation

**Deploy Frontend to Render as well:**
- Frontend: `https://frontend.onrender.com`
- Backend: `https://pro-obuv.onrender.com`

Or refactor to pure static site for Netlify.

## Environment Variables (if using Render)

```
BACKEND_URL=https://pro-obuv.onrender.com
SECRET_KEY=your-frontend-secret-key
PORT=10000
```

## Testing Locally

```bash
cd frontend
export BACKEND_URL=https://pro-obuv.onrender.com
python server.py
```

Visit: http://localhost:3000
