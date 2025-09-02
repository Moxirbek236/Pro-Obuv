
// Global o'zgaruvchilar
const currentPath = window.location.pathname;

// To'liq tarjima lug'ati
const translations = {
    'uz': {
        'welcome': '🍽️ Bizning Restoranga Xush Kelibsiz!',
        'best_food': 'Eng mazali taomlar va a\'lo xizmat',
        'restaurant_order': 'Restoranda buyurtma berish',
        'restaurant_desc': 'Restoranda o\'tirib, navbat oling va buyurtma bering',
        'get_queue': 'Navbat olish',
        'delivery_service': 'Dostavka xizmati',
        'delivery_desc': 'Uyingizgacha yetkazib berish xizmati',
        'order_now': 'Buyurtma berish',
        'menu': 'Menyu',
        'contact': 'Bog\'lanish',
        'about': 'Biz haqimizda',
        'login': 'Kirish',
        'register': 'Ro\'yxatdan o\'tish',
        'cart': 'Savatcha',
        'home': 'Bosh sahifa',
        'language': 'Til',
        'dark_mode': 'Tungi rejim',
        'light_mode': 'Kunduzgi rejim',
        'settings': 'Sozlamalar',
        'profile': 'Profil',
        'logout': 'Chiqish',
        'favorites': 'Sevimlilar',
        'downloads': 'Yuklab olish'
    },
    'ru': {
        'welcome': '🍽️ Добро пожаловать в наш ресторан!',
        'best_food': 'Самая вкусная еда и отличный сервис',
        'restaurant_order': 'Заказ в ресторане',
        'restaurant_desc': 'Садитесь в ресторане, встаньте в очередь и сделайте заказ',
        'get_queue': 'Встать в очередь',
        'delivery_service': 'Служба доставки',
        'delivery_desc': 'Доставка на дом',
        'order_now': 'Заказать сейчас',
        'menu': 'Меню',
        'contact': 'Контакты',
        'about': 'О нас',
        'login': 'Войти',
        'register': 'Регистрация',
        'cart': 'Корзина',
        'home': 'Главная',
        'language': 'Язык',
        'dark_mode': 'Темный режим',
        'light_mode': 'Светлый режим',
        'settings': 'Настройки',
        'profile': 'Профиль',
        'logout': 'Выйти',
        'favorites': 'Избранное',
        'downloads': 'Скачать'
    },
    'en': {
        'welcome': '🍽️ Welcome to Our Restaurant!',
        'best_food': 'The most delicious food and excellent service',
        'restaurant_order': 'Restaurant ordering',
        'restaurant_desc': 'Sit in the restaurant, get in line and place an order',
        'get_queue': 'Get in queue',
        'delivery_service': 'Delivery service',
        'delivery_desc': 'Home delivery service',
        'order_now': 'Order now',
        'menu': 'Menu',
        'contact': 'Contact',
        'about': 'About us',
        'login': 'Login',
        'register': 'Register',
        'cart': 'Cart',
        'home': 'Home',
        'language': 'Language',
        'dark_mode': 'Dark mode',
        'light_mode': 'Light mode',
        'settings': 'Settings',
        'profile': 'Profile',
        'logout': 'Logout',
        'favorites': 'Favorites',
        'downloads': 'Downloads'
    }
};

// Savatcha sonini yangilash funksiyasi
function updateCartCount(retryCount = 0) {
    const maxRetries = 3;
    
    fetch('/api/cart-count', {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Response is not JSON');
        }
        return response.json();
    })
    .then(data => {
        const cartBadge = document.querySelector('.cart-badge');
        if (cartBadge && data.count !== undefined) {
            cartBadge.textContent = data.count;
            cartBadge.style.display = data.count > 0 ? 'inline' : 'none';
        }
    })
    .catch(error => {
        console.log('Savatcha sonini olishda xato:', error);
        if (retryCount < maxRetries) {
            setTimeout(() => updateCartCount(retryCount + 1), 1000 * (retryCount + 1));
        }
    });
}

// Buyurtma holatini tekshirish
function checkOrderStatus(ticketNo) {
    fetch(`/user/status/${ticketNo}`)
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                updateOrderDisplay(data);
            }
        })
        .catch(error => {
            console.error('Buyurtma holatini tekshirishda xatolik:', error);
        });
}

// Buyurtma ko'rinishini yangilash
function updateOrderDisplay(data) {
    const statusElement = document.getElementById('order-status');
    const queueElement = document.getElementById('queue-position');
    
    if (statusElement) {
        statusElement.textContent = data.status_text;
    }
    
    if (queueElement && data.queue_position > 0) {
        queueElement.textContent = `Navbatdagi o'rningiz: ${data.queue_position}`;
        queueElement.style.display = 'block';
    } else if (queueElement) {
        queueElement.style.display = 'none';
    }

    // Baho berish tugmasini ko'rsatish
    if (data.show_rating) {
        showRatingModal(data.order_id);
    }
}

// Buyurtmani bekor qilish
function cancelOrder(ticketNo) {
    if (confirm('Buyurtmani rostdan ham bekor qilmoqchimisiz?')) {
        fetch(`/user/cancel/${ticketNo}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                alert('Buyurtma bekor qilindi');
                location.reload();
            } else {
                alert(data.msg || 'Xatolik yuz berdi');
            }
        })
        .catch(error => {
            console.error('Buyurtmani bekor qilishda xatolik:', error);
            alert('Xatolik yuz berdi');
        });
    }
}

// Baho berish modali
function showRatingModal(orderId) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Xizmatni baholang</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="rating-stars mb-3">
                        ${[1,2,3,4,5].map(i => `<span class="star" data-rating="${i}">⭐</span>`).join('')}
                    </div>
                    <textarea class="form-control" placeholder="Izohingiz (ixtiyoriy)" id="rating-comment"></textarea>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" onclick="submitRating(${orderId})">Baholash</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Yulduzchalarni bosilganda
    modal.querySelectorAll('.star').forEach(star => {
        star.addEventListener('click', function() {
            const rating = this.dataset.rating;
            modal.querySelectorAll('.star').forEach((s, index) => {
                s.style.opacity = index < rating ? '1' : '0.3';
            });
            modal.dataset.selectedRating = rating;
        });
    });
}

// Baho yuborish
function submitRating(orderId) {
    const modal = document.querySelector('.modal');
    const rating = modal.dataset.selectedRating;
    const comment = modal.querySelector('#rating-comment').value;
    
    if (!rating) {
        alert('Iltimos baho bering');
        return;
    }
    
    fetch('/api/submit-rating', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            order_id: orderId,
            rating: rating,
            comment: comment
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Rahmat! Sizning bahoyingiz saqlandi.');
            bootstrap.Modal.getInstance(modal).hide();
            location.reload();
        } else {
            alert(data.message || 'Xatolik yuz berdi');
        }
    })
    .catch(error => {
        console.error('Baho yuborishda xatolik:', error);
        alert('Xatolik yuz berdi');
    });
}

// Sozlamalarni yuklash
function loadSettings() {
    const darkMode = localStorage.getItem('darkMode') === 'true';
    const fontSize = localStorage.getItem('fontSize') || 'medium';
    const language = localStorage.getItem('language') || 'uz';
    
    return { darkMode, fontSize, language };
}

// Sozlamalarni saqlash
function saveSettings(settings) {
    localStorage.setItem('darkMode', settings.darkMode);
    localStorage.setItem('fontSize', settings.fontSize);
    localStorage.setItem('language', settings.language);
}

// Mavzuni o'zgartirish
function applyTheme(isDark) {
    document.body.setAttribute('data-dark-mode', isDark);
    
    if (isDark) {
        document.body.classList.add('dark-theme');
        console.log('Dark theme qo\'shildi');
    } else {
        document.body.classList.remove('dark-theme');
        console.log('Light theme qo\'shildi');
    }
}

// Font o'lchamini o'zgartirish
function applyFontSize(size) {
    document.body.setAttribute('data-font-size', size);
    document.body.classList.remove('font-small', 'font-medium', 'font-large');
    document.body.classList.add(`font-${size}`);
    console.log('Font size qo\'shildi:', `font-${size}`);
}

// Tilni o'zgartirish
function applyLanguage(lang) {
    document.body.setAttribute('data-language', lang);
    document.body.classList.remove('lang-uz', 'lang-ru', 'lang-en');
    document.body.classList.add(`lang-${lang}`);
    console.log('Language qo\'shildi:', `lang-${lang}`);
    
    // Tarjimalarni qo'llash
    const elementsToTranslate = document.querySelectorAll('[data-translate]');
    elementsToTranslate.forEach(element => {
        const key = element.getAttribute('data-translate');
        if (translations[lang] && translations[lang][key]) {
            element.textContent = translations[lang][key];
        }
    });
    console.log('Til tarjimasi qo\'llandi:', lang);
}

// Service Worker ro'yxatdan o'tkazish
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

// Sahifa yuklanganda
document.addEventListener('DOMContentLoaded', function() {
    // Sozlamalarni yuklash va qo'llash
    const settings = loadSettings();
    console.log('DOMContentLoaded - Loading settings:', settings);
    
    applyTheme(settings.darkMode);
    applyFontSize(settings.fontSize);
    applyLanguage(settings.language);
    
    // Service Worker ni ro'yxatdan o'tkazish
    registerServiceWorker();
    
    // Savatcha sonini yangilash
    updateCartCount();
    
    // Buyurtma holati sahifasi uchun
    if (currentPath.includes('/user/success/')) {
        const ticketNo = currentPath.split('/').pop();
        
        // Dastlabki holat tekshiruvi
        checkOrderStatus(ticketNo);
        
        // Har 5 soniyada holat tekshiruvi
        setInterval(() => checkOrderStatus(ticketNo), 5000);
        
        // Bekor qilish tugmasini qo'shish
        const orderInfo = document.querySelector('.order-info');
        if (orderInfo) {
            const cancelBtn = document.createElement('button');
            cancelBtn.className = 'btn btn-danger mt-3';
            cancelBtn.innerHTML = '❌ Buyurtmani bekor qilish';
            cancelBtn.onclick = () => cancelOrder(ticketNo);
            orderInfo.appendChild(cancelBtn);
        }
    }
    
    // Savatchaga qo'shish tugmalari
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function() {
            setTimeout(updateCartCount, 500);
        });
    });
    
    // Sozlamalar modali tugmalari
    const settingsModal = document.getElementById('settingsModal');
    if (settingsModal) {
        // Til o'zgartirish tugmalari
        const languageButtons = settingsModal.querySelectorAll('[data-language]');
        languageButtons.forEach(button => {
            button.addEventListener('click', function() {
                const newLang = this.dataset.language;
                const currentSettings = loadSettings();
                currentSettings.language = newLang;
                
                applyLanguage(newLang);
                saveSettings(currentSettings);
                
                // Server ga ham yuborish
                fetch('/api/set-language', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ language: newLang })
                }).catch(console.error);
            });
        });
        
        // Mavzu o'zgartirish
        const themeToggle = settingsModal.querySelector('#themeToggle');
        if (themeToggle) {
            themeToggle.checked = loadSettings().darkMode;
            themeToggle.addEventListener('change', function() {
                const currentSettings = loadSettings();
                currentSettings.darkMode = this.checked;
                
                applyTheme(this.checked);
                saveSettings(currentSettings);
                
                // Server ga ham yuborish
                fetch('/api/set-theme', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dark_mode: this.checked })
                }).catch(console.error);
            });
        }
        
        // Font o'lchami
        const fontSizeSelect = settingsModal.querySelector('#fontSizeSelect');
        if (fontSizeSelect) {
            fontSizeSelect.value = loadSettings().fontSize;
            fontSizeSelect.addEventListener('change', function() {
                const currentSettings = loadSettings();
                currentSettings.fontSize = this.value;
                
                applyFontSize(this.value);
                saveSettings(currentSettings);
            });
        }
    }
});
