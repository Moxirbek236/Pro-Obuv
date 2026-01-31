# 🚀 Quick Reference: Responsive E-Commerce Classes

## 📱 Breakpoints
```css
Mobile Small:  ≤ 320px
Mobile:        ≤ 480px
Tablet:        481px - 768px
Laptop:        769px - 1024px
Desktop:       1025px - 1280px
Large:         ≥ 1281px
```

## 🎨 Spacing (Fluid)
```css
--space-3xs  /* 4-6px */
--space-2xs  /* 8-12px */
--space-xs   /* 12-16px */
--space-sm   /* 16-24px */
--space-md   /* 24-32px */
--space-lg   /* 32-48px */
--space-xl   /* 48-64px */
--space-2xl  /* 64-96px */
--space-3xl  /* 96-128px */
```

## 📝 Typography (Fluid)
```css
--text-xs    /* 12-14px */
--text-sm    /* 14-16px */
--text-base  /* 16-18px */
--text-lg    /* 18-20px */
--text-xl    /* 20-24px */
--text-2xl   /* 24-32px */
--text-3xl   /* 32-40px */
--text-4xl   /* 40-56px */
--text-5xl   /* 48-72px */
```

## 🎯 Touch Targets
```css
--touch-target-min: 44px         /* WCAG AAA minimum */
--touch-target-comfortable: 48px /* Recommended */
--touch-target-large: 56px       /* Large buttons */
```

## 📦 Layout Classes

### Product Grid
```html
<div class="product-grid">
    <!-- Auto-responsive: 1-4 columns based on screen size -->
</div>
```

### Shop Layout (Grid + Sidebar)
```html
<div class="shop-layout">
    <aside class="filter-sidebar"><!-- Filters --></aside>
    <main class="product-grid"><!-- Products --></main>
</div>
```

### Container
```html
<div class="container"><!-- Max-width container --></div>
<div class="container-fluid"><!-- Full-width container --></div>
```

## 🛍️ Product Card
```html
<div class="product-card">
    <div class="product-card__image">
        <img src="..." alt="..." loading="lazy">
    </div>
    <div class="product-card__content">
        <span class="product-card__category">Category</span>
        <h3 class="product-card__title">Product Name</h3>
        <div class="product-card__price">$99.99</div>
        <div class="product-card__actions">
            <button class="product-card__btn">Add to Cart</button>
        </div>
    </div>
</div>
```

## 🎛️ Filter Sidebar

### Desktop: Sticky Sidebar
```css
/* Automatically sticky on ≥ 769px */
.filter-sidebar { }
```

### Mobile: Bottom Sheet
```html
<!-- Toggle button (mobile only) -->
<button onclick="toggleFilters()">Filters</button>

<!-- Sidebar -->
<aside class="filter-sidebar" id="filterSidebar">
    <!-- Filters -->
</aside>

<!-- Backdrop -->
<div class="filter-backdrop" id="filterBackdrop"></div>

<script>
function toggleFilters() {
    document.getElementById('filterSidebar').classList.toggle('filter-sidebar--open');
    document.getElementById('filterBackdrop').classList.toggle('filter-backdrop--visible');
}
</script>
```

## 🧭 Navigation

### Responsive Navbar
```html
<nav class="navbar">
    <div class="navbar__container container">
        <a href="/" class="navbar__brand">LOGO</a>
        <button class="navbar__toggle">☰</button>
        <ul class="navbar__menu" id="navMenu">
            <li><a href="#" class="navbar__link">Link</a></li>
        </ul>
    </div>
</nav>
```

## 📊 Responsive Tables

### Card View on Mobile
```html
<table class="table-mobile-cards">
    <thead>
        <tr>
            <th>Product</th>
            <th>Price</th>
            <th>Stock</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td data-label="Product">Safety Boot</td>
            <td data-label="Price">$99.99</td>
            <td data-label="Stock">In Stock</td>
        </tr>
    </tbody>
</table>
```

## 🎨 Utility Classes

### Visibility
```css
.hide-mobile     /* Hidden on ≤ 480px */
.hide-tablet     /* Hidden on 481-768px */
.hide-desktop    /* Hidden on ≥ 769px */
.show-mobile     /* Visible only on ≤ 480px */
.show-tablet     /* Visible only on 481-768px */
.show-desktop    /* Visible only on ≥ 769px */
```

### Flexbox
```css
.d-flex
.flex-column
.flex-wrap
.align-items-center
.justify-content-center
.justify-content-between
.gap-sm
.gap-md
```

### Spacing
```css
.mt-auto
.mb-auto
.mx-auto
```

### Text
```css
.text-center
.text-left
.text-right
```

### Width
```css
.w-100    /* width: 100% */
.w-auto   /* width: auto */
```

## ♿ Accessibility

### Skip to Main
```html
<a href="#main-content" class="skip-to-main">Skip to main content</a>
<main id="main-content"><!-- Content --></main>
```

### Screen Reader Only
```html
<span class="sr-only">Hidden text for screen readers</span>
```

### Focus Visible
```css
/* Automatically applied to all focusable elements */
*:focus-visible {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
}
```

## 📱 Touch Optimization

### Forms
```html
<!-- Automatically touch-friendly (≥ 44px) -->
<input type="text" class="form-control">
<select class="form-select"></select>
<button class="btn">Button</button>
```

### Buttons
```html
<button class="btn">
    <!-- Min height: 44px (mobile), 48px (touch devices) -->
</button>
```

## 🎯 Common Patterns

### Product Grid with Filters
```html
<div class="container">
    <!-- Mobile filter toggle -->
    <button class="btn hide-desktop" onclick="toggleFilters()">
        Filters
    </button>
    
    <div class="shop-layout">
        <!-- Sidebar -->
        <aside class="filter-sidebar" id="filterSidebar">
            <h4>Filters</h4>
            <input type="search" class="form-control" placeholder="Search...">
            <select class="form-select">
                <option>All Categories</option>
            </select>
        </aside>
        
        <!-- Products -->
        <div class="product-grid">
            <!-- Product cards here -->
        </div>
    </div>
    
    <!-- Backdrop -->
    <div class="filter-backdrop" id="filterBackdrop"></div>
</div>
```

### Responsive Footer
```html
<footer class="footer">
    <div class="container">
        <div class="footer-grid">
            <div class="footer__column">
                <h5 class="footer__title">Company</h5>
                <a href="#" class="footer__link">About</a>
                <a href="#" class="footer__link">Contact</a>
            </div>
            <!-- More columns -->
        </div>
    </div>
</footer>
```

## 🚀 Performance Tips

### Lazy Load Images
```html
<img src="image.jpg" alt="..." loading="lazy">
```

### Responsive Images
```html
<img 
    srcset="small.jpg 480w, medium.jpg 768w, large.jpg 1200w"
    sizes="(max-width: 480px) 100vw, (max-width: 768px) 50vw, 33vw"
    src="medium.jpg"
    alt="..."
    loading="lazy">
```

### GPU Acceleration
```css
.gpu-accelerated {
    transform: translateZ(0);
    will-change: transform;
}
```

## 🧪 Testing Checklist

- [ ] No horizontal scroll
- [ ] Touch targets ≥ 44px
- [ ] Text readable (≥ 16px)
- [ ] Images scale properly
- [ ] Forms usable
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] Performance (Lighthouse ≥ 90)

## 📚 Files

- **CSS:** `static/css/ecommerce-responsive-universal.css`
- **Guide:** `ECOMMERCE_RESPONSIVE_IMPLEMENTATION.md`
- **Summary:** `RESPONSIVE_DESIGN_SUMMARY.md`

---

**Quick Start:**
1. CSS is already loaded in `base.html`
2. Use `.product-grid` for product layouts
3. Use `.shop-layout` for grid + sidebar
4. Use `.product-card` for product cards
5. Add `loading="lazy"` to images
6. Test on real devices!

**Version:** 2.0.0 | **Updated:** 2026-01-31
