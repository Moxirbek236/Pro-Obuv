
// Service Worker registratsiyasi
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('SW registered: ', registration);
            })
            .catch(function(registrationError) {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

// Global variables
let currentPath = window.location.pathname;
let updateCartInterval;

// To'liq tarjima lug'ati
const translations = {
    'uz': {
        'home': 'Bosh sahifa',
        'menu': 'Menyu',
        'cart': 'Savatcha',
        'contact': 'Aloqa',
        'about': 'Biz haqimizda',
        'profile': 'Profil',
        'favorites': 'Sevimlilar',
        'login': 'Kirish',
        'logout': 'Chiqish',
        'register': 'Ro\'yxatdan o\'tish',
        'order_now': 'Buyurtma berish',
        'add_to_cart': 'Savatchaga qo\'shish',
        'view_cart': 'Savatchani ko\'rish',
        'checkout': 'To\'lov',
        'total': 'Jami',
        'quantity': 'Miqdor',
        'price': 'Narx',
        'remove': 'O\'chirish',
        'back': 'Orqaga',
        'next': 'Keyingi',
        'save': 'Saqlash',
        'cancel': 'Bekor qilish',
        'confirm': 'Tasdiqlash',
        'loading': 'Yuklanmoqda...',
        'error': 'Xatolik',
        'success': 'Muvaffaqiyat',
        'warning': 'Ogohlantirish',
        'info': 'Ma\'lumot'
    },
    'ru': {
        'home': 'Главная',
        'menu': 'Меню',
        'cart': 'Корзина',
        'contact': 'Контакты',
        'about': 'О нас',
        'profile': 'Профиль',
        'favorites': 'Избранное',
        'login': 'Войти',
        'logout': 'Выйти',
        'register': 'Регистрация',
        'order_now': 'Заказать',
        'add_to_cart': 'В корзину',
        'view_cart': 'Смотреть корзину',
        'checkout': 'Оформить заказ',
        'total': 'Итого',
        'quantity': 'Количество',
        'price': 'Цена',
        'remove': 'Удалить',
        'back': 'Назад',
        'next': 'Далее',
        'save': 'Сохранить',
        'cancel': 'Отмена',
        'confirm': 'Подтвердить',
        'loading': 'Загрузка...',
        'error': 'Ошибка',
        'success': 'Успех',
        'warning': 'Предупреждение',
        'info': 'Информация'
    },
    'en': {
        'home': 'Home',
        'menu': 'Menu',
        'cart': 'Cart',
        'contact': 'Contact',
        'about': 'About',
        'profile': 'Profile',
        'favorites': 'Favorites',
        'login': 'Login',
        'logout': 'Logout',
        'register': 'Register',
        'order_now': 'Order Now',
        'add_to_cart': 'Add to Cart',
        'view_cart': 'View Cart',
        'checkout': 'Checkout',
        'total': 'Total',
        'quantity': 'Quantity',
        'price': 'Price',
        'remove': 'Remove',
        'back': 'Back',
        'next': 'Next',
        'save': 'Save',
        'cancel': 'Cancel',
        'confirm': 'Confirm',
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'warning': 'Warning',
        'info': 'Information'
    }
};

// Til sozlamasini olish
function getCurrentLanguage() {
    return localStorage.getItem('interface_language') || 'uz';
}

// Matnni tarjima qilish
function translate(key) {
    const lang = getCurrentLanguage();
    return translations[lang] && translations[lang][key] ? translations[lang][key] : key;
}

// Sahifadagi barcha tarjima elementlarini yangilash
function updateTranslations() {
    const currentLang = getCurrentLanguage();
    console.log('Til tarjimasi qo\'llandi:', currentLang);
    
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        if (translations[currentLang] && translations[currentLang][key]) {
            if (element.tagName === 'INPUT' && (element.type === 'submit' || element.type === 'button')) {
                element.value = translations[currentLang][key];
            } else {
                element.textContent = translations[currentLang][key];
            }
        }
    });
}

// Savatcha sonini yangilash funksiyasi
function updateCartCount(retryCount = 0) {
    const maxRetries = 3;
    
    fetch('/api/cart-count', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success && typeof data.count === 'number') {
            const cartCountElement = document.getElementById('cart-count');
            if (cartCountElement) {
                cartCountElement.textContent = data.count;
                cartCountElement.style.display = data.count > 0 ? 'inline' : 'none';
            }
        } else {
            throw new Error('Invalid response format');
        }
    })
    .catch(error => {
        console.log('Savatcha sonini olishda xato:', error);
        if (retryCount < maxRetries) {
            setTimeout(() => updateCartCount(retryCount + 1), 1000 * (retryCount + 1));
        } else {
            // Fallback: savatcha sonini 0 ga o'rnatish
            const cartCountElement = document.getElementById('cart-count');
            if (cartCountElement) {
                cartCountElement.textContent = '0';
                cartCountElement.style.display = 'none';
            }
        }
    });
}

// JavaScript xatolarini tutish
window.addEventListener('error', function(event) {
    console.log('JavaScript xatosi:', event.error);
    // Xatolikni server ga yuborish (ixtiyoriy)
    try {
        fetch('/api/log-error', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: event.message,
                source: event.filename,
                line: event.lineno,
                column: event.colno,
                error: event.error ? event.error.toString() : 'Unknown'
            })
        }).catch(() => {}); // Silent fail
    } catch (e) {}
});

// DOM yuklanganda
document.addEventListener('DOMContentLoaded', function() {
    // Sozlamalarni yuklash
    const settings = {
        darkMode: localStorage.getItem('dark_theme') === 'true',
        fontSize: localStorage.getItem('font_size') || 'medium',
        language: localStorage.getItem('interface_language') || 'uz'
    };
    
    console.log('DOMContentLoaded - Loading settings:', settings);
    
    // Dark/Light theme
    if (settings.darkMode) {
        document.body.classList.add('dark-theme');
        console.log('Dark theme qo\'shildi');
    } else {
        document.body.classList.add('light-theme');
        console.log('Light theme qo\'shildi');
    }
    
    // Font size
    document.body.classList.add('font-' + settings.fontSize);
    console.log('Font size qo\'shildi:', 'font-' + settings.fontSize);
    
    // Language
    document.body.classList.add('lang-' + settings.language);
    console.log('Language qo\'shildi:', 'lang-' + settings.language);
    
    // Tarjimalarni qo'llash
    updateTranslations();
    
    // Savatcha sonini yangilash
    updateCartCount();
    
    // Har 10 soniyada savatcha sonini yangilash
    if (updateCartInterval) {
        clearInterval(updateCartInterval);
    }
    updateCartInterval = setInterval(updateCartCount, 10000);
    
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
});

// Buyurtma holatini tekshirish
function checkOrderStatus(ticketNo) {
    fetch(`/user/status/${ticketNo}`)
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                updateOrderStatus(data);
            }
        })
        .catch(error => console.log('Holat tekshirishda xato:', error));
}

// Buyurtma holatini yangilash
function updateOrderStatus(data) {
    const statusElement = document.getElementById('order-status');
    const positionElement = document.getElementById('queue-position');
    const ratingSection = document.getElementById('rating-section');
    
    if (statusElement) {
        statusElement.textContent = data.status_text;
        statusElement.className = `status-${data.status}`;
    }
    
    if (positionElement && data.queue_position > 0) {
        positionElement.textContent = `Navbatdagi o'rningiz: ${data.queue_position}`;
        positionElement.style.display = 'block';
    } else if (positionElement) {
        positionElement.style.display = 'none';
    }
    
    // Baho berish bo'limini ko'rsatish
    if (ratingSection && data.show_rating) {
        ratingSection.style.display = 'block';
    }
}

// Buyurtmani bekor qilish
function cancelOrder(ticketNo) {
    if (confirm('Buyurtmani bekor qilishni xohlaysizmi?')) {
        fetch(`/user/cancel/${ticketNo}`, {method: 'POST'})
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
                console.log('Bekor qilishda xato:', error);
                alert('Xatolik yuz berdi');
            });
    }
}

// Baho berish
function submitRating(orderId) {
    const rating = document.querySelector('input[name="rating"]:checked');
    const comment = document.getElementById('rating-comment');
    
    if (!rating) {
        alert('Iltimos, baho bering');
        return;
    }
    
    const data = {
        order_id: orderId,
        rating: parseInt(rating.value),
        comment: comment ? comment.value : ''
    };
    
    fetch('/api/submit-rating', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Baho yuborildi. Rahmat!');
            document.getElementById('rating-section').style.display = 'none';
        } else {
            alert(result.message || 'Xatolik yuz berdi');
        }
    })
    .catch(error => {
        console.log('Baho yuborishda xato:', error);
        alert('Xatolik yuz berdi');
    });
}

// Til o'zgartirish
function changeLanguage(language) {
    localStorage.setItem('interface_language', language);
    
    fetch('/api/set-language', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({language: language})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Sahifani qayta yuklash
            location.reload();
        }
    })
    .catch(error => console.log('Til o\'zgartirish xato:', error));
}

// Mavzu o'zgartirish
function toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    
    if (isDark) {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        localStorage.setItem('dark_theme', 'false');
    } else {
        document.body.classList.remove('light-theme');
        document.body.classList.add('dark-theme');
        localStorage.setItem('dark_theme', 'true');
    }
    
    // Server ga yuborish
    fetch('/api/set-theme', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({dark_mode: !isDark})
    }).catch(error => console.log('Mavzu o\'zgartirish xato:', error));
}

// Font size o'zgartirish
function changeFontSize(size) {
    // Eski font class larini olib tashlash
    document.body.classList.remove('font-small', 'font-medium', 'font-large');
    
    // Yangi font class qo'shish
    document.body.classList.add('font-' + size);
    
    // Local storage ga saqlash
    localStorage.setItem('font_size', size);
    
    // Server ga yuborish
    const settings = {
        language: localStorage.getItem('interface_language') || 'uz',
        font_size: size,
        dark_theme: localStorage.getItem('dark_theme') === 'true'
    };
    
    fetch('/api/save-settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(settings)
    }).catch(error => console.log('Font size saqlash xato:', error));
}

// Sahifa yuklanishidan oldin tozalash
window.addEventListener('beforeunload', function() {
    if (updateCartInterval) {
        clearInterval(updateCartInterval);
    }
});
