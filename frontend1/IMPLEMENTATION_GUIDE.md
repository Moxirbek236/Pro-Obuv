# Safety.uz Frontend Implementation Guide

## 🎉 Loyiha muvaffaqiyatli yaratildi!

Ushbu loyiha **FRONTEND_GENERATION_PROMPT.txt** asosida yaratilgan zamonaviy React + TypeScript frontend ilovasidir.

## 📁 Yaratilgan Struktura

```
frontend1/
├── public/                 # Static files
├── src/
│   ├── api/               # API client va endpoint funksiyalari
│   │   ├── client.ts      # Axios instance
│   │   ├── auth.ts        # Authentication API
│   │   ├── products.ts    # Products API
│   │   ├── cart.ts        # Cart API
│   │   ├── orders.ts      # Orders API
│   │   └── users.ts       # Users API
│   ├── components/
│   │   └── common/        # Umumiy komponentlar
│   │       ├── Navbar.tsx
│   │       └── Footer.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx # Authentication context
│   ├── hooks/             # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useDebounce.ts
│   │   ├── useResponsive.ts
│   │   ├── useStorage.ts
│   │   └── useDom.ts
│   ├── layouts/
│   │   └── MainLayout.tsx # Asosiy layout
│   ├── pages/
│   │   ├── public/        # Ochiq sahifalar
│   │   ├── user/          # User sahifalari
│   │   ├── staff/         # Staff sahifalari
│   │   └── superadmin/    # Superadmin sahifalari
│   ├── routes/
│   │   └── index.tsx      # Routing konfiguratsiyasi
│   ├── styles/
│   │   └── globals.css    # Global CSS
│   ├── types/             # TypeScript type definitions
│   │   ├── auth.types.ts
│   │   ├── product.types.ts
│   │   ├── order.types.ts
│   │   ├── cart.types.ts
│   │   ├── api.types.ts
│   │   └── user.types.ts
│   ├── utils/             # Utility funksiyalar
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   ├── constants.ts
│   │   └── helpers.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── .env.local             # Development environment
├── .env.production        # Production environment
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── README.md
```

## ✅ Yaratilgan Asosiy Xususiyatlar

### 1. **Authentication System**
- ✅ Session-based authentication
- ✅ 3 ta rol: user, staff, superadmin
- ✅ Login/Logout funksiyalari
- ✅ Protected routes
- ✅ AuthContext va useAuth hook

### 2. **API Integration**
- ✅ Axios client with interceptors
- ✅ Auth API (login, logout, register)
- ✅ Products API
- ✅ Cart API
- ✅ Orders API
- ✅ Users API
- ✅ Error handling
- ✅ Session timeout handling

### 3. **Routing**
- ✅ React Router v6
- ✅ Protected routes
- ✅ Role-based access control
- ✅ Public, User, Staff, Superadmin routes

### 4. **UI Components**
- ✅ Responsive Navbar
- ✅ Footer
- ✅ MainLayout
- ✅ Loading states
- ✅ Toast notifications

### 5. **Styling**
- ✅ Tailwind CSS
- ✅ Dark mode support
- ✅ Custom color palette
- ✅ Responsive design
- ✅ Animations

### 6. **TypeScript**
- ✅ Strict mode
- ✅ Type definitions for all entities
- ✅ API response types
- ✅ Component props types

### 7. **Utilities**
- ✅ Date/currency formatters
- ✅ Form validators
- ✅ Helper functions
- ✅ Constants
- ✅ Custom hooks

## 🚀 Keyingi Qadamlar

### 1. Paketlarni O'rnatish (Agar hali o'rnatilmagan bo'lsa)
```bash
cd frontend1
npm install
```

### 2. Development Server Ishga Tushirish
```bash
npm run dev
```

Brauzerda ochiladi: `http://localhost:3000`

### 3. Qo'shimcha Sahifalarni Yaratish

Hozirda placeholder sahifalar mavjud. Quyidagilarni to'ldirish kerak:

#### Public Pages
- [ ] MenuPage - Mahsulotlar katalogi
- [ ] ProductDetailPage - Mahsulot tafsilotlari
- [ ] RegisterPage - Ro'yxatdan o'tish
- [ ] AboutPage - Biz haqimizda
- [ ] ContactPage - Aloqa

#### User Pages
- [ ] ProfilePage - Foydalanuvchi profili
- [ ] CartPage - Savatcha
- [ ] FavoritesPage - Sevimlilar
- [ ] OrdersPage - Buyurtmalar tarixi
- [ ] SettingsPage - Sozlamalar

#### Staff Pages
- [ ] StaffLoginPage - Xodimlar kirish
- [ ] StaffDashboardPage - Xodimlar paneli
- [ ] StaffMenuPage - Mahsulotlarni boshqarish
- [ ] StaffChatPage - Chat

#### Superadmin Pages
- [ ] SuperadminLoginPage - Superadmin kirish
- [ ] SuperadminDashboardPage - Superadmin paneli
- [ ] AnalyticsPage - Analitika
- [ ] ReportsPage - Hisobotlar
- [ ] SystemPage - Tizim sozlamalari
- [ ] LogsPage - Loglar
- [ ] UserManagementPage - Foydalanuvchilarni boshqarish
- [ ] StaffManagementPage - Xodimlarni boshqarish
- [ ] NewsManagementPage - Yangiliklar

### 4. Komponentlarni Yaratish

Quyidagi komponentlar kerak:

#### Product Components
- [ ] ProductCard - Mahsulot kartasi
- [ ] ProductGallery - Rasm galereyasi
- [ ] ProductFilters - Filtrlar
- [ ] ProductList - Mahsulotlar ro'yxati

#### Cart Components
- [ ] CartItem - Savatcha elementi
- [ ] CartSummary - Savatcha xulosasi
- [ ] CheckoutForm - Checkout forma

#### Order Components
- [ ] OrderCard - Buyurtma kartasi
- [ ] OrderStatus - Buyurtma holati
- [ ] OrderTimeline - Buyurtma vaqt chizig'i

#### Common Components
- [ ] Button - Tugma
- [ ] Input - Input maydoni
- [ ] Modal - Modal oyna
- [ ] Toast - Bildirishnoma
- [ ] Loader - Yuklanish indikatori
- [ ] ErrorBoundary - Xatolik chegarasi

### 5. Multilingual Support
- [ ] Translation context yaratish
- [ ] Til almashtirish funksiyasi
- [ ] Tarjimalar faylini yaratish

### 6. Theme Support
- [ ] Theme context yaratish
- [ ] Dark/Light mode toggle
- [ ] Font size adjuster

### 7. Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E tests

### 8. Production Build
```bash
npm run build
```

### 9. Deployment
- Netlify, Vercel yoki Render'ga deploy qilish
- Environment variables sozlash
- Production domain ulash

## 🔧 Muhim Konfiguratsiyalar

### Environment Variables

**Development (.env.local):**
```
VITE_API_BASE_URL=http://localhost:5000
VITE_APP_NAME=Safety.uz
VITE_DEFAULT_LANGUAGE=uz
VITE_ENABLE_DEBUG=true
```

**Production (.env.production):**
```
VITE_API_BASE_URL=https://pro-obuv.onrender.com
VITE_APP_NAME=Safety.uz
VITE_DEFAULT_LANGUAGE=uz
VITE_ENABLE_DEBUG=false
```

### API Endpoints

Backend API: `https://pro-obuv.onrender.com`

Barcha endpoint'lar `src/api/` papkasida belgilangan.

## 📚 Texnologiyalar

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router v6** - Routing
- **Axios** - HTTP client
- **React Query** - Server state
- **Tailwind CSS** - Styling
- **Recharts** - Charts
- **Lucide React** - Icons
- **React Hot Toast** - Notifications

## 🎨 Design System

### Colors
- **Primary**: Industrial Blue (#2563eb)
- **Secondary**: Safety Orange (#f97316)
- **Accent**: Dark Gray (#1f2937)

### Typography
- **Headings**: Outfit
- **Body**: Inter

### Breakpoints
- **sm**: 640px
- **md**: 768px
- **lg**: 1024px
- **xl**: 1280px

## 📝 Coding Standards

1. **TypeScript Strict Mode** - Har doim type'larni belgilang
2. **Functional Components** - Class componentlardan foydalanmang
3. **Custom Hooks** - Qayta ishlatiladigan logikani hook'larga ajrating
4. **Error Handling** - Barcha API chaqiruvlarida error handling
5. **Loading States** - Har bir async operatsiyada loading ko'rsating
6. **Responsive Design** - Mobile-first yondashuv
7. **Accessibility** - ARIA labels va keyboard navigation

## 🐛 Debugging

Development rejimida:
```bash
npm run dev
```

Browser console'da xatolarni ko'ring.

## 📖 Qo'shimcha Resurslar

- [React Documentation](https://react.dev)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Router Documentation](https://reactrouter.com)

## 🤝 Yordam

Savollar yoki muammolar bo'lsa:
1. README.md faylini o'qing
2. FRONTEND_GENERATION_PROMPT.txt ga qarang
3. Backend API documentation'ni tekshiring

---

**Loyiha holati:** ✅ Asosiy struktura yaratildi, placeholder sahifalar qo'shildi

**Keyingi qadam:** Sahifalarni va komponentlarni to'ldirish

**Muvaffaqiyatlar!** 🚀
