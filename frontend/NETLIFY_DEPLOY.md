# Frontend Deployment to Netlify - UPDATED

## ✅ Frontend endi to'liq STATIC!

Frontend endi Flask dan mustaqil, to'liq static HTML/CSS/JavaScript.
Barcha ma'lumotlar Backend API dan JavaScript orqali olinadi.

## Netlify Deployment

### 1. GitHub Repository
Ensure your code is pushed to GitHub.

### 2. Netlify Setup
1. Go to https://netlify.com
2. Click "Add new site" → "Import an existing project"
3. Connect to GitHub
4. Select your repository
5. Configure build settings:
   - **Base directory**: `frontend`
   - **Build command**: (leave empty - no build needed)
   - **Publish directory**: `.` (current directory)

### 3. Environment Variables
In Netlify dashboard, add:
```
BACKEND_URL=https://pro-obuv.onrender.com
```

### 4. Deploy
Click "Deploy site"

Your site will be live at: `https://your-site-name.netlify.app`

## Custom Domain (Optional)

1. In Netlify dashboard → Domain settings
2. Add custom domain: `safetyuz.netlify.app` or your own domain
3. Update DNS records as instructed

## How It Works

```
┌─────────────────┐
│   Browser       │
│   (User)        │
└────────┬────────┘
         │
         │ 1. Loads HTML/CSS/JS
         ▼
┌─────────────────┐
│   Netlify       │  Static Files
│   Frontend      │  (HTML, CSS, JS)
└────────┬────────┘
         │
         │ 2. JavaScript makes API calls
         ▼
┌─────────────────┐
│   Render        │  Backend API
│   Backend       │  (JSON responses)
└─────────────────┘
```

## Role-Based Rendering

Frontend JavaScript automatically shows/hides components based on user role:

- **Guest**: Navbar + Footer
- **User**: Navbar + Footer + Cart
- **Staff**: Staff Navbar + Minimal Footer + Staff Sidebar
- **Courier**: Courier Navbar + Minimal Footer + Courier Sidebar
- **Superadmin**: Admin Navbar + **NO FOOTER** + Admin Sidebar

## Files Structure

```
frontend/
├── index.html              # Main entry point
├── menu.html               # Products page
├── login.html              # Login page
├── staff/                  # Staff pages
├── courier/                # Courier pages
├── superadmin/             # Superadmin pages
├── static/
│   ├── css/                # Styles
│   ├── js/
│   │   ├── config.js       # API configuration
│   │   ├── api.js          # API helper
│   │   ├── auth.js         # Authentication
│   │   ├── components.js   # UI components (role-based)
│   │   ├── router.js       # Client-side routing
│   │   └── main.js         # Main app logic
│   └── img/                # Images
└── netlify.toml            # Netlify configuration
```

## Testing Locally

```bash
cd frontend
python -m http.server 3000
```

Visit: http://localhost:3000

## Important Notes

✅ **No Flask needed** - Pure static site
✅ **Fast loading** - Served from CDN
✅ **Role-based UI** - JavaScript handles visibility
✅ **API calls** - All data from Backend
✅ **Session management** - Via cookies and localStorage

## Troubleshooting

### API calls fail (CORS error)
- Ensure Backend has CORS enabled for Netlify domain
- Check `BACKEND_URL` in `config.js`

### User role not detected
- Check browser localStorage
- Verify session cookies are being sent

### Page not loading
- Check browser console for errors
- Verify all JS files are loaded correctly
