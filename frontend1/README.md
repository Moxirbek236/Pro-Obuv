# Safety.uz Frontend

O'zbekistonning yetakchi sanoat xavfsizlik poyabzallari e-tijorat platformasi uchun zamonaviy frontend ilovasi.

## 🚀 Texnologiyalar

- **Core:** React 18, TypeScript, Vite
- **Styling:** Tailwind CSS, PostCSS
- **State Management:** React Query (Server State), Context API (Auth/Cart)
- **Routing:** React Router v6
- **UI Components:** Lucide React Icons, React Hot Toast
- **Architecture:** Feature-based folder structure

## 🛠 O'rnatish va Ishga Tushirish

Loyihani mahalliy kompyuteringizda ishga tushirish uchun quyidagi qadamlarni bajaring:

1. **Repozitoriyni klonlash:**
   ```bash
   git clone <repository-url>
   cd frontend1
   ```

2. **Kutubxonalarni o'rnatish:**
   ```bash
   npm install
   ```

3. **Loyihani ishga tushirish:**
   ```bash
   npm run dev
   ```
   Loyiha `http://localhost:3000` (yoki boshqa port) da ochiladi.

## 📂 Loyiha Strukturasi

```
src/
├── api/            # API integratsiyasi (Axios)
├── components/     # Qayta ishlatiluvchi komponentlar
│   ├── common/     # Umumiy (Navbar, Footer, Button...)
│   ├── product/    # Mahsulot kartalari, filtrlar
│   └── cart/       # Savatcha komponentlari
├── contexts/       # Global state (Auth, Cart)
├── hooks/          # Custom hooks (useAuth, useCart...)
├── layouts/        # Sahifa layoutlari
├── pages/          # Sahifalar
│   ├── public/     # Ochiq sahifalar (Home, Catalog...)
│   ├── user/       # Foydalanuvchi kabineti
│   ├── staff/      # Xodimlar paneli
│   └── superadmin/ # Superadmin boshqaruv paneli
├── routes/         # Marshrutlar konfiguratsiyasi
├── styles/         # Global CSS va Tailwind
├── types/          # TypeScript tiplari
└── utils/          # Yordamchi funksiyalar
```

## 🔐 Xavfsizlik va Rolelar

Tizimda 3 xil rol mavjud:
1. **User:** Oddiy xaridor (Ro'yxatdan o'tish, xarid qilish, profil)
2. **Staff:** Xodimlar (Buyurtmalarni boshqarish, mahsulotlar) - `/staff-secure-login-w7m2k`
3. **Superadmin:** Tizim administratori (To'liq nazorat) - `/super-admin-master-login-z9x4m`

##  API Integratsiyasi

Hozirgi vaqtda loyiha **Mock Data** rejimida ishlaydi (backend ulanmagan bo'lsa ham UI ni to'liq test qilish mumkin). Backend tayyor bo'lgach, `.env` faylida `VITE_API_URL` ni o'zgartirish kifoya.

## 🎨 Dizayn

Dizayn "Safety" brendiga mos ravishda qizil (Primary), to'q kulrang va oq ranglar asosida qurilgan. Dark mode to'liq qo'llab-quvvatlanadi.

---
© 2024 Safety.uz. Barcha huquqlar himoyalangan.
