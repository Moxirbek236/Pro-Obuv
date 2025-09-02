
// Universal Restaurant System - Main JavaScript

// Global o'zgaruvchilar
let cartCount = 0;
let currentPath = window.location.pathname;

// Professional Translation System
// Global translations object - check if already exists to prevent redeclaration
if (typeof translations === 'undefined') {
    var translations = {
        uz: {
            menu: '📋 Menyu',
            favorites: '❤️ Sevimlilar',
            contact: '📞 Aloqa',
            about: '❓ Savollar',
            downloads: '📱 Yuklamalar',
            cart: '🛒 Savatcha',
            profile_info: '👤 Profil ma\'lumotlari',
            profile_settings: '⚙️ Profil sozlamalari',
            settings: '🔧 Sozlamalar',
            logout: '🚪 Chiqish',
            login: '🔐 Kirish',
            register: '📝 Ro\'yxat',
            user: '👤 Foydalanuvchi',
            staff: '👨‍💼 Xodim',
            courier: '🚚 Kuryer',
            admin: '🔧 Admin',
            dashboard: '🏠 Dashboard',
            analytics: '📊 Analytics',
            reports: '📈 Hisobotlar',
            system: '⚙️ Tizim',
            logs: '📝 Loglar'
        },
        ru: {
            menu: '📋 Меню',
            favorites: '❤️ Избранное',
            contact: '📞 Контакты',
            about: '❓ Вопросы',
            downloads: '📱 Загрузки',
            cart: '🛒 Корзина',
            profile_info: '👤 Данные профиля',
            profile_settings: '⚙️ Настройки профиля',
            settings: '🔧 Настройки',
            logout: '🚪 Выход',
            login: '🔐 Вход',
            register: '📝 Регистрация',
            user: '👤 Пользователь',
            staff: '👨‍💼 Сотрудник',
            courier: '🚚 Курьер',
            admin: '🔧 Админ',
            dashboard: '🏠 Панель',
            analytics: '📊 Аналитика',
            reports: '📈 Отчеты',
            system: '⚙️ Система',
            logs: '📝 Логи'
        },
        en: {
            menu: '📋 Menu',
            favorites: '❤️ Favorites',
            contact: '📞 Contact',
            about: '❓ About',
            downloads: '📱 Downloads',
            cart: '🛒 Cart',
            profile_info: '👤 Profile Info',
            profile_settings: '⚙️ Profile Settings',
            settings: '🔧 Settings',
            logout: '🚪 Logout',
            login: '🔐 Login',
            register: '📝 Register',
            user: '👤 User',
            staff: '👨‍💼 Staff',
            courier: '🚚 Courier',
            admin: '🔧 Admin',
            dashboard: '🏠 Dashboard',
            analytics: '📊 Analytics',
            reports: '📈 Reports',
            system: '⚙️ System',
            logs: '📝 Logs'
        }
    };
}

// Universal Theme Management
class UniversalThemeManager {
    constructor() {
        this.initializeTheme();
        this.setupEventListeners();
    }

    initializeTheme() {
        const darkMode = localStorage.getItem('darkMode') === 'true';
        const fontSize = localStorage.getItem('fontSize') || 'medium';
        const language = localStorage.getItem('language') || 'uz';

        console.log('Universal Theme - Initializing:', { darkMode, fontSize, language });

        this.applyTheme(darkMode);
        this.applyFontSize(fontSize);
        this.applyLanguage(language);
    }

    applyTheme(isDark) {
        const body = document.body;
        const navbar = document.querySelector('.navbar');

        // Clear theme classes
        body.classList.remove('dark-theme', 'light-theme');

        if (isDark) {
            body.classList.add('dark-theme');
            body.setAttribute('data-theme', 'dark');

            if (navbar) {
                navbar.classList.remove('navbar-light', 'bg-light');
                navbar.classList.add('navbar-dark', 'bg-dark');
            }

            console.log('Universal Theme - Dark mode applied');
        } else {
            body.classList.add('light-theme');
            body.setAttribute('data-theme', 'light');

            if (navbar) {
                navbar.classList.remove('navbar-dark', 'bg-dark');
                navbar.classList.add('navbar-light', 'bg-light');
            }

            console.log('Universal Theme - Light mode applied');
        }

        // Save to localStorage
        localStorage.setItem('darkMode', isDark);

        // Save to server
        this.saveToServer('theme', isDark ? 'dark' : 'light');
    }

    applyFontSize(size) {
        const body = document.body;

        // Clear font classes
        body.classList.remove('font-small', 'font-medium', 'font-large', 'font-xlarge');

        // Apply font size
        body.classList.add('font-' + size);
        body.setAttribute('data-font-size', size);

        console.log('Universal Theme - Font size applied:', size);

        // Save to localStorage
        localStorage.setItem('fontSize', size);

        // Save to server
        this.saveToServer('font_size', size);
    }

    applyLanguage(language) {
        const body = document.body;

        // Clear language classes
        body.classList.remove('lang-uz', 'lang-ru', 'lang-en');

        // Apply language
        body.classList.add('lang-' + language);
        body.setAttribute('data-language', language);

        console.log('Universal Theme - Language applied:', language);

        // Save to localStorage
        localStorage.setItem('language', language);

        // Translate page
        this.translatePage(language);

        // Save to server
        this.saveToServer('language', language);
    }

    translatePage(language) {
        const trans = window.translations[language] || window.translations.uz;

        // Navbar links
        this.updateElementText('a[href*="menu"]', trans.menu);
        this.updateElementText('a[href*="favorites"]', trans.favorites);
        this.updateElementText('a[href*="contact"]', trans.contact);
        this.updateElementText('a[href*="about"]', trans.about);
        this.updateElementText('a[href*="downloads"]', trans.downloads);

        // Cart link
        const cartLink = document.querySelector('a[href*="cart"]');
        if (cartLink && cartLink.innerHTML.includes('🛒')) {
            const cartBadge = cartLink.querySelector('.cart-badge') || cartLink.querySelector('#cart-count');
            const badgeHtml = cartBadge ? cartBadge.outerHTML : '';
            cartLink.innerHTML = trans.cart + ' ' + badgeHtml;
        }

        // Login/Register links
        this.updateElementText('a[href*="login"]:not([href*="staff"]):not([href*="courier"])', trans.login);
        this.updateElementText('a[href*="register"]:not([href*="staff"]):not([href*="courier"])', trans.register);

        // Dropdown items
        this.translateDropdownItems(trans);

        console.log('Universal Theme - Translation completed:', language);
    }

    updateElementText(selector, text) {
        const element = document.querySelector(selector);
        if (element && !element.innerHTML.includes('<')) {
            element.innerHTML = text;
        }
    }

    translateDropdownItems(trans) {
        const dropdownItems = document.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            const text = item.textContent.trim();

            if (text.includes('Foydalanuvchi')) {
                item.innerHTML = trans.user;
            } else if (text.includes('Xodim')) {
                item.innerHTML = trans.staff;
            } else if (text.includes('Kuryer')) {
                item.innerHTML = trans.courier;
            } else if (text.includes('Admin')) {
                item.innerHTML = trans.admin;
            } else if (text.includes('Profil ma\'lumotlari')) {
                item.innerHTML = trans.profile_info;
            } else if (text.includes('Profil sozlamalari')) {
                item.innerHTML = trans.profile_settings;
            } else if (text.includes('Sozlamalar')) {
                item.innerHTML = trans.settings;
            } else if (text.includes('Dashboard')) {
                item.innerHTML = trans.dashboard;
            } else if (text.includes('Chiqish')) {
                item.innerHTML = trans.logout;
            } else if (text.includes('Analytics')) {
                item.innerHTML = trans.analytics;
            } else if (text.includes('Hisobotlar')) {
                item.innerHTML = trans.reports;
            } else if (text.includes('Tizim')) {
                item.innerHTML = trans.system;
            } else if (text.includes('Loglar')) {
                item.innerHTML = trans.logs;
            }
        });
    }

    saveToServer(setting, value) {
        const endpoint = setting === 'language' ? '/api/set-language' : '/api/set-settings';
        const payload = setting === 'language' ? { language: value } : { [setting]: value };

        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Universal Theme - Setting saved:', setting, value);
            }
        }).catch(error => {
            console.log('Universal Theme - Save error:', error);
        });
    }

    setupEventListeners() {
        // Storage event listener
        window.addEventListener('storage', (e) => {
            if (e.key === 'darkMode') {
                this.applyTheme(e.newValue === 'true');
            } else if (e.key === 'fontSize') {
                this.applyFontSize(e.newValue);
            } else if (e.key === 'language') {
                this.applyLanguage(e.newValue);
            }
        });

        // Theme toggle listeners
        document.addEventListener('change', (e) => {
            if (e.target.name === 'theme_mode') {
                this.applyTheme(e.target.value === 'dark');
            } else if (e.target.name === 'font_size') {
                this.applyFontSize(e.target.value);
            }
        });
    }
}

// Global functions
window.changeTheme = function(isDark) {
    if (window.universalTheme) {
        window.universalTheme.applyTheme(isDark);
    }
};

window.changeFontSize = function(size) {
    if (window.universalTheme) {
        window.universalTheme.applyFontSize(size);
    }
};

window.changeLanguage = function(language) {
    if (window.universalTheme) {
        window.universalTheme.applyLanguage(language);
        // Show notification
        showNotification('Til muvaffaqiyatli o\'zgartirildi');
    }
};

// Cart Management
class CartManager {
    constructor() {
        this.updateCartCount();
        this.setupAutoUpdate();
    }

    updateCartCount() {
        fetch('/api/cart-count')
            .then(response => response.json())
            .then(data => {
                const cartCountElements = document.querySelectorAll('#cart-count, .cart-badge');
                cartCountElements.forEach(element => {
                    if (data.count > 0) {
                        element.textContent = data.count;
                        element.style.display = 'inline-block';
                        if (element.classList.contains('cart-badge-floating')) {
                            element.classList.add('show');
                        }
                    } else {
                        element.style.display = 'none';
                        if (element.classList.contains('cart-badge-floating')) {
                            element.classList.remove('show');
                        }
                    }
                });
                cartCount = data.count;
            })
            .catch(error => console.log('Cart count error:', error));
    }

    setupAutoUpdate() {
        // Update every 10 seconds
        setInterval(() => {
            this.updateCartCount();
        }, 10000);
    }

    addToCart(itemId, quantity = 1) {
        fetch('/api/add-to-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item_id: itemId,
                quantity: quantity
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.updateCartCount();
                showNotification('Mahsulot savatga qo\'shildi', 'success');
            } else {
                showNotification(data.message || 'Xatolik yuz berdi', 'error');
            }
        })
        .catch(error => {
            console.log('Add to cart error:', error);
            showNotification('Savatga qo\'shishda xatolik', 'error');
        });
    }
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `toast-notification toast-${type}`;

    notification.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
            <span class="toast-message">${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);

    // Hide and remove notification
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Service Worker Registration
function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(error => {
                console.log('SW registration failed: ', error);
            });
    }
}

// Universal Initialization
let universalTheme;
let cartManager;

document.addEventListener('DOMContentLoaded', function() {
    try {
        // Initialize theme manager
        universalTheme = new UniversalThemeManager();
        window.universalTheme = universalTheme;

        // Initialize cart manager
        cartManager = new CartManager();
        window.cartManager = cartManager;

        // Register service worker
        registerServiceWorker();

        // Setup menu item clicks
        setupMenuItemClicks();

        // Setup form submissions
        setupFormSubmissions();

        console.log('Universal System - Initialization complete');

    } catch (error) {
        console.error('Initialization error:', error);
    }
});

// Menu item click handlers
function setupMenuItemClicks() {
    document.addEventListener('click', function(e) {
        // Add to cart buttons
        if (e.target.classList.contains('add-to-cart-btn')) {
            e.preventDefault();
            const itemId = e.target.getAttribute('data-item-id');
            const quantity = e.target.getAttribute('data-quantity') || 1;
            if (itemId && window.cartManager) {
                window.cartManager.addToCart(itemId, quantity);
            }
        }

        // Theme toggle buttons
        if (e.target.classList.contains('theme-toggle')) {
            e.preventDefault();
            const isDark = !document.body.classList.contains('dark-theme');
            if (window.universalTheme) {
                window.universalTheme.applyTheme(isDark);
            }
        }
    });
}

// Form submission handlers
function setupFormSubmissions() {
    // Settings form
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(settingsForm);
            const settings = Object.fromEntries(formData);

            // Apply settings immediately
            if (settings.theme_mode && window.universalTheme) {
                window.universalTheme.applyTheme(settings.theme_mode === 'dark');
            }
            if (settings.font_size && window.universalTheme) {
                window.universalTheme.applyFontSize(settings.font_size);
            }
            if (settings.language && window.universalTheme) {
                window.universalTheme.applyLanguage(settings.language);
            }

            showNotification('Sozlamalar saqlandi', 'success');
        });
    }
}

// Utility Functions
function formatPrice(price) {
    return new Intl.NumberFormat('uz-UZ', {
        style: 'currency',
        currency: 'UZS',
        minimumFractionDigits: 0
    }).format(price);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('uz-UZ', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

// Global error handler
window.addEventListener('error', function(e) {
    console.error('JavaScript xatosi:', e.error);
    if (typeof showNotification === 'function') {
        showNotification('Sahifada xatolik yuz berdi', 'error');
    }
});

// Page visibility handler
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && window.cartManager) {
        window.cartManager.updateCartCount();
    }
});

// Resize handler
window.addEventListener('resize', function() {
    // Handle responsive changes if needed
    const isMobile = window.innerWidth < 768;
    document.body.classList.toggle('mobile-view', isMobile);
});

// Export for global use
window.showNotification = showNotification;
