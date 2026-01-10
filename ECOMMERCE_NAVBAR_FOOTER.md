# E-COMMERCE NAVBAR VA FOOTER YARATILDI

## Yaratilgan Fayllar

### 1. CSS Fayl
**`static/css/ecommerce-navbar-footer.css`**
- ✅ Zamonaviy navbar dizayni
- ✅ Professional footer dizayni
- ✅ Tungi/Kunduzgi theme qo'llab-quvvatlash
- ✅ To'liq responsive (mobile, tablet, desktop)
- ✅ Smooth animatsiyalar

### 2. Navbar Komponenti
**`templates/components/ecommerce_navbar.html`**

**Xususiyatlar:**
- Logo va branding
- Qidiruv paneli
- Navigation links (Mahsulotlar, Yangiliklar, Biz haqimizda, Aloqa)
- Savatcha (cart badge bilan)
- Foydalanuvchi menyu
- Theme toggle (tungi/kunduzgi)
- Til tanlash (UZ, RU, EN, KZ)
- Mobile menu

### 3. Footer Komponenti
**`templates/components/ecommerce_footer.html`**

**Xususiyatlar:**
- Brand ma'lumotlari
- Ijtimoiy tarmoqlar
- Tezkor havolalar
- Mijozlar xizmati
- Aloqa ma'lumotlari (telefon, email, manzil, ish vaqti)
- To'lov usullari (Click, Payme, Uzum, Cash)
- Copyright

## Keyingi Qadam: base.html ni Yangilash

`base.html` faylida navbar va footer joylarini topish va almashtirish kerak.

### Qidirilishi Kerak:
1. Eski navbar kodi
2. Eski footer kodi
3. `{% block content %}` joyi

### Qo'shilishi Kerak:
```html
<!-- Navbar -->
{% include 'components/ecommerce_navbar.html' %}

<!-- Main Content -->
<main>
  {% block content %}{% endblock %}
</main>

<!-- Footer -->
{% include 'components/ecommerce_footer.html' %}
```

## Theme Xususiyatlari

### Kunduzgi Theme (Light)
- Navbar: Oq fon (#ffffff)
- Footer: To'q kulrang (#1f2937)
- Matn: Qora (#1f2937)

### Tungi Theme (Dark)
- Navbar: To'q kulrang (#1f2937)
- Footer: Juda to'q (#111827)
- Matn: Oq (#f9fafb)

## Responsive Breakpoints

```css
/* Desktop: > 1024px */
- To'liq navbar
- 4 ustunli footer

/* Tablet: 768px - 1024px */
- Qisqartirilgan qidiruv
- 2 ustunli footer

/* Mobile: < 768px */
- Hamburger menu
- Qidiruv yashirin
- 1 ustunli footer
```

## JavaScript Funksiyalar

### Theme Toggle
```javascript
// localStorage da saqlanadi
// body.dark-theme class qo'shiladi/olib tashlanadi
```

### Mobile Menu
```javascript
// .mobile-menu.active class bilan ochiladi
// Link bosilganda avtomatik yopiladi
```

### Language Change
```javascript
// changeLanguage(lang) funksiyasi
// /set-language API ga so'rov yuboradi
// Sahifani reload qiladi
```

## Foydalanish

### 1. CSS Qo'shilgan
`base.html` da allaqachon qo'shilgan:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/ecommerce-navbar-footer.css') }}" />
```

### 2. Komponentlarni Qo'shish
`base.html` da body qismida:
```html
{% include 'components/ecommerce_navbar.html' %}
<main>
  {% block content %}{% endblock %}
</main>
{% include 'components/ecommerce_footer.html' %}
```

## Test Qilish

1. Serverni ishga tushiring
2. Istalgan sahifani oching
3. Tekshiring:
   - ✅ Navbar yuqorida ko'rinadi
   - ✅ Theme toggle ishlaydi
   - ✅ Mobile menu ishlaydi
   - ✅ Footer pastda ko'rinadi
   - ✅ Responsive dizayn ishlaydi

---

**Status:** Komponentlar tayyor, base.html ga qo'shish kerak  
**Sana:** 2026-01-09  
**Versiya:** 1.0
