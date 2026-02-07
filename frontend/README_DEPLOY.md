# Frontend Server - Safety.uz

Ushbu server **faqat** Frontend (HTML, CSS, JS) ni xizmat qiladi.
Barcha ma'lumotlar Backend API dan olinadi.

## Rollar (Roles)

Frontend server quyidagi rollarni qo'llab-quvvatlaydi:

1. **Guest** (Mehmon) - Ro'yxatdan o'tmagan foydalanuvchi
   - Sahifalar: `/`, `/menu`, `/product/<id>`, `/contact`, `/about`, `/login`, `/register`

2. **User** (Foydalanuvchi) - Oddiy mijoz
   - Qo'shimcha: `/profile`, `/cart`, buyurtmalar

3. **Staff** (Xodim) - Restoran xodimlari
   - Dashboard: `/staff`, `/staff/dashboard`
   - Login: `/staff/login`

4. **Courier** (Kuryer) - Yetkazib beruvchilar
   - Dashboard: `/courier`, `/courier/dashboard`
   - Login: `/courier/login`

5. **Superadmin** (Bosh Administrator)
   - Dashboard: `/superadmin`, `/super-admin`, `/admin/super`
   - Login: `/admin/login`

## Ishga tushirish

### Lokal (Development)
```bash
cd frontend
python server.py
```

Server `http://localhost:3000` da ishga tushadi.
Backend: `http://127.0.0.1:5000` (lokal) yoki `https://pro-obuv.onrender.com` (production)

### Production (Netlify/Vercel)
```bash
# Environment variable
BACKEND_URL=https://pro-obuv.onrender.com

# Install dependencies
pip install -r requirements.txt

# Run with gunicorn
gunicorn server:app
```

## Ma'lumotlar oqimi

1. Foydalanuvchi Frontend sahifasini ochadi
2. Frontend HTML ni ko'rsatadi
3. JavaScript (client-side) Backend API ga so'rov yuboradi
4. Backend ma'lumot qaytaradi
5. JavaScript sahifani yangilaydi

## Muhim

- Frontend **hech qachon** database ga to'g'ridan-to'g'ri ulanmaydi
- Barcha ma'lumotlar Backend `/api/*` endpointlari orqali olinadi
- Session ma'lumotlari Backend bilan sinxronlashtiriladi
