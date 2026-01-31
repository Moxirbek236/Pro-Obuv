# 🚀 Admin Panel - Quick Reference Guide

## 📱 Responsive Breakpoints
```css
Mobile:        ≤ 480px      (1 column, slide-in sidebar)
Tablet:        481-768px    (2 columns, slide-in sidebar)
Laptop:        769-1024px   (3 columns, fixed sidebar 260px)
Desktop:       1025-1599px  (4 columns, fixed sidebar 280px)
Ultra-wide:    ≥ 1600px     (5 columns, fixed sidebar 280px)
```

## 🎨 Color Variables
```css
/* Backgrounds */
--admin-bg-primary: #f8fafc
--admin-bg-secondary: #ffffff
--admin-bg-tertiary: #f1f5f9

/* Text */
--admin-text-primary: #0f172a
--admin-text-secondary: #64748b
--admin-text-muted: #94a3b8

/* Accents */
--admin-accent-primary: #3b82f6    (Blue)
--admin-accent-success: #10b981    (Green)
--admin-accent-warning: #f59e0b    (Orange)
--admin-accent-danger: #ef4444     (Red)
--admin-accent-info: #06b6d4       (Cyan)
```

## 📏 Spacing
```css
--admin-space-xs: 8-12px
--admin-space-sm: 12-16px
--admin-space-md: 16-24px
--admin-space-lg: 24-32px
--admin-space-xl: 32-48px
```

## 🧩 Layout Classes

### Dashboard Layout
```html
<main class="dashboard-layout">
    <aside class="dashboard-sidebar">...</aside>
    <main class="dashboard-main">...</main>
</main>
```

### Sidebar Navigation
```html
<a href="#" class="nav-link-modern active">
    <i class="bi bi-grid"></i>
    Dashboard
</a>
```

### Top Header
```html
<header class="top-header">
    <button class="mobile-menu-toggle">☰</button>
    <div class="header-title">
        <h2>Page Title</h2>
        <p class="header-subtitle">Subtitle</p>
    </div>
    <div class="header-actions">...</div>
</header>
```

### Dashboard Content
```html
<div class="dashboard-content">
    <!-- Your content here -->
</div>
```

## 📊 Dashboard Grid (Stat Cards)
```html
<div class="dashboard-grid">
    <div class="stat-card">
        <div class="stat-icon primary">
            <i class="bi bi-users"></i>
        </div>
        <h3>1,234</h3>
        <p>Total Users</p>
    </div>
</div>
```

**Grid Columns:**
- Mobile: 1
- Tablet: 2
- Laptop: 3
- Desktop: 4
- Ultra-wide: 5

## 📋 Responsive Tables

### Desktop/Laptop View
```html
<div class="table-responsive-wrapper">
    <table class="table-modern">
        <thead>
            <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>John Doe</td>
                <td>john@example.com</td>
                <td><button class="btn btn-sm">Edit</button></td>
            </tr>
        </tbody>
    </table>
</div>
```

### Mobile Card View
```html
<div class="table-responsive-wrapper">
    <table class="table-modern table-mobile-cards">
        <thead>
            <tr>
                <th>Name</th>
                <th>Email</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td data-label="Name">John Doe</td>
                <td data-label="Email">john@example.com</td>
            </tr>
        </tbody>
    </table>
</div>
```

## 📝 Forms

### Basic Form
```html
<form>
    <div class="mb-3">
        <label class="form-label">Username</label>
        <input type="text" class="form-control" placeholder="Enter username">
    </div>
    
    <div class="mb-3">
        <label class="form-label">Role</label>
        <select class="form-select">
            <option>Admin</option>
            <option>Staff</option>
        </select>
    </div>
    
    <button type="submit" class="btn btn-primary">Save</button>
</form>
```

## 🔘 Buttons

### Button Variants
```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-success">Success</button>
<button class="btn btn-danger">Danger</button>
<button class="btn btn-light-modern">Light</button>
```

### Button Sizes
```html
<button class="btn btn-sm btn-primary">Small</button>
<button class="btn btn-primary">Default</button>
<button class="btn btn-lg btn-primary">Large</button>
```

## 🎴 Cards
```html
<div class="card-modern">
    <h3>Card Title</h3>
    <p>Card content goes here...</p>
</div>
```

## 🎯 Stat Icons
```html
<div class="stat-icon primary">
    <i class="bi bi-users"></i>
</div>

<div class="stat-icon success">
    <i class="bi bi-check-circle"></i>
</div>

<div class="stat-icon warning">
    <i class="bi bi-exclamation-triangle"></i>
</div>

<div class="stat-icon danger">
    <i class="bi bi-x-circle"></i>
</div>

<div class="stat-icon info">
    <i class="bi bi-info-circle"></i>
</div>
```

## 📱 Mobile Sidebar Toggle

### JavaScript
```javascript
function toggleSidebar() {
    const sidebar = document.querySelector('.dashboard-sidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    
    sidebar.classList.toggle('show');
    backdrop.classList.toggle('show');
}
```

### HTML
```html
<!-- Mobile toggle button -->
<button class="mobile-menu-toggle" onclick="toggleSidebar()">
    <i class="bi bi-list"></i>
</button>

<!-- Sidebar backdrop -->
<div class="sidebar-backdrop" onclick="toggleSidebar()"></div>
```

## 🎨 Utility Classes

### Text Colors
```html
<p class="text-primary">Primary text</p>
<p class="text-secondary">Secondary text</p>
<p class="text-muted">Muted text</p>
```

### Backgrounds
```html
<div class="bg-primary">Primary background</div>
<div class="bg-secondary">Secondary background</div>
<div class="bg-tertiary">Tertiary background</div>
```

### Spacing
```html
<div class="p-responsive">Responsive padding</div>
<div class="px-responsive">Responsive horizontal padding</div>
<div class="py-responsive">Responsive vertical padding</div>
```

## ♿ Accessibility

### Touch Targets
- All buttons: min-height 44px
- All inputs: min-height 44px
- All links: min-height 44px

### Keyboard Navigation
- Tab through interactive elements
- Enter/Space to activate
- Escape to close modals

### Focus Indicators
```css
*:focus-visible {
    outline: 2px solid var(--admin-accent-primary);
    outline-offset: 2px;
}
```

## 📊 Responsive Behavior

### Sidebar
| Screen | Behavior |
|--------|----------|
| Desktop (≥1025px) | Fixed, 280px wide |
| Laptop (769-1024px) | Fixed, 260px wide |
| Tablet (481-768px) | Slide-in, 240px wide |
| Mobile (≤480px) | Slide-in, 280px wide |

### Content Padding
| Screen | Padding |
|--------|---------|
| Ultra-wide (≥1600px) | 48px |
| Desktop (1025-1599px) | 32px |
| Laptop (769-1024px) | 24px |
| Tablet (481-768px) | 16px |
| Mobile (≤480px) | 12px |

### Dashboard Grid
| Screen | Columns |
|--------|---------|
| Mobile (≤480px) | 1 |
| Tablet (481-768px) | 2 |
| Laptop (769-1024px) | 3 |
| Desktop (1025-1599px) | 4 |
| Ultra-wide (≥1600px) | 5 |

## 🧪 Testing Checklist

### Quick Tests
- [ ] Sidebar toggles on mobile
- [ ] No horizontal scroll
- [ ] All buttons tappable (≥44px)
- [ ] Forms usable on mobile
- [ ] Tables adapt to mobile
- [ ] Navigation works everywhere

### Performance
- [ ] Lighthouse ≥ 90
- [ ] FCP < 1.5s
- [ ] LCP < 2.5s
- [ ] CLS < 0.1

## 🚀 Quick Start

### 1. CSS is Already Loaded
The admin panel responsive CSS is automatically loaded in `dashboard_base.html`.

### 2. Use Semantic Classes
```html
<!-- Good -->
<div class="dashboard-grid">
    <div class="stat-card">...</div>
</div>

<!-- Avoid -->
<div style="display: grid;">
    <div style="padding: 20px;">...</div>
</div>
```

### 3. Add Mobile Toggle
```html
<button class="mobile-menu-toggle" onclick="toggleSidebar()">
    <i class="bi bi-list"></i>
</button>
```

### 4. Test on Real Devices
Don't rely only on browser DevTools. Test on actual mobile devices.

## 📚 Files

- **CSS:** `static/css/admin-panel-responsive.css`
- **Guide:** `ADMIN_PANEL_RESPONSIVE_GUIDE.md`
- **Quick Ref:** `ADMIN_PANEL_QUICK_REFERENCE.md` (this file)

---

**Version:** 3.0.0  
**Updated:** 2026-01-31  
**Status:** ✅ Production Ready
