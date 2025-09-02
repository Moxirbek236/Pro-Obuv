// To'liq tarjima lug'ati
const translations = {
    'uz': {
        'menu': 'Menyu',
        'cart': 'Savatcha',
        'profile': 'Profil',
        'login': 'Kirish',
        'logout': 'Chiqish',
        'register': 'Ro\'yxatdan o\'tish',
        'contact': 'Bog\'lanish',
        'about': 'Biz haqimizda',
        'home': 'Bosh sahifa',
        'order_now': 'Buyurtma berish',
        'add_to_cart': 'Savatchaga qo\'shish',
        'view_cart': 'Savatchani ko\'rish',
        'place_order': 'Buyurtma berish',
        'favorites': 'Sevimlilar',
        'settings': 'Sozlamalar',
        'language': 'Til',
        'theme': 'Mavzu',
        'notifications': 'Xabarnomalar',
        'search': 'Qidirish',
        'cancel': 'Bekor qilish',
        'confirm': 'Tasdiqlash',
        'save': 'Saqlash',
        'edit': 'Tahrirlash',
        'delete': 'O\'chirish',
        'success': 'Muvaffaqiyatli',
        'error': 'Xatolik',
        'loading': 'Yuklanmoqda...',
        'no_items': 'Mahsulotlar topilmadi',
        'total': 'Jami',
        'price': 'Narx',
        'quantity': 'Miqdor',
        'delivery': 'Yetkazib berish',
        'pickup': 'Olib ketish'
    },
    'ru': {
        'menu': 'Меню',
        'cart': 'Корзина',
        'profile': 'Профиль',
        'login': 'Войти',
        'logout': 'Выйти',
        'register': 'Регистрация',
        'contact': 'Контакты',
        'about': 'О нас',
        'home': 'Главная',
        'order_now': 'Заказать',
        'add_to_cart': 'В корзину',
        'view_cart': 'Корзина',
        'place_order': 'Оформить заказ',
        'favorites': 'Избранное',
        'settings': 'Настройки',
        'language': 'Язык',
        'theme': 'Тема',
        'notifications': 'Уведомления',
        'search': 'Поиск',
        'cancel': 'Отмена',
        'confirm': 'Подтвердить',
        'save': 'Сохранить',
        'edit': 'Редактировать',
        'delete': 'Удалить',
        'success': 'Успешно',
        'error': 'Ошибка',
        'loading': 'Загрузка...',
        'no_items': 'Товары не найдены',
        'total': 'Итого',
        'price': 'Цена',
        'quantity': 'Количество',
        'delivery': 'Доставка',
        'pickup': 'Самовывоз'
    },
    'en': {
        'menu': 'Menu',
        'cart': 'Cart',
        'profile': 'Profile',
        'login': 'Login',
        'logout': 'Logout',
        'register': 'Register',
        'contact': 'Contact',
        'about': 'About',
        'home': 'Home',
        'order_now': 'Order Now',
        'add_to_cart': 'Add to Cart',
        'view_cart': 'View Cart',
        'place_order': 'Place Order',
        'favorites': 'Favorites',
        'settings': 'Settings',
        'language': 'Language',
        'theme': 'Theme',
        'notifications': 'Notifications',
        'search': 'Search',
        'cancel': 'Cancel',
        'confirm': 'Confirm',
        'save': 'Save',
        'edit': 'Edit',
        'delete': 'Delete',
        'success': 'Success',
        'error': 'Error',
        'loading': 'Loading...',
        'no_items': 'No items found',
        'total': 'Total',
        'price': 'Price',
        'quantity': 'Quantity',
        'delivery': 'Delivery',
        'pickup': 'Pickup'
    }
};

// Current path variable declaration
const currentPath = window.location.pathname;

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
            throw new Error('Server HTML qaytardi JSON o\'rniga');
        }
        
        return response.json();
    })
    .then(data => {
        const cartCountElement = document.querySelector('.cart-count, #cart-count, [data-cart-count]');
        if (cartCountElement && typeof data.count !== 'undefined') {
            cartCountElement.textContent = data.count;
            cartCountElement.style.display = data.count > 0 ? 'inline' : 'none';
        }
    })
    .catch(error => {
        console.log('Savatcha sonini olishda xatolik:', error);
        
        if (retryCount < maxRetries) {
            setTimeout(() => updateCartCount(retryCount + 1), 1000 * (retryCount + 1));
        } else {
            const cartCountElement = document.querySelector('.cart-count, #cart-count, [data-cart-count]');
            if (cartCountElement) {
                cartCountElement.textContent = '0';
                cartCountElement.style.display = 'none';
            }
        }
    });
}

// Buyurtma holatini tekshirish
function checkOrderStatus(ticketNo) {
    fetch(`/user/status/${ticketNo}`)
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                const statusElement = document.getElementById('order-status');
                const queueElement = document.getElementById('queue-position');
                
                if (statusElement) {
                    statusElement.textContent = data.status_text;
                }
                
                if (queueElement && data.queue_position > 0) {
                    queueElement.textContent = `Navbatdagi o'rni: ${data.queue_position}`;
                    queueElement.style.display = 'block';
                } else if (queueElement) {
                    queueElement.style.display = 'none';
                }

                // Agar buyurtma yetkazib berilgan bo'lsa, baho berish tugmasini ko'rsatish
                if (data.show_rating) {
                    showRatingModal(data.order_id);
                }
            }
        })
        .catch(error => console.error('Status tekshirishda xatolik:', error));
}

// Buyurtmani bekor qilish
function cancelOrder(ticketNo) {
    if (confirm('Buyurtmani bekor qilishni xohlaysizmi?')) {
        fetch(`/user/cancel/${ticketNo}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
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
            console.error('Bekor qilishda xatolik:', error);
            alert('Buyurtmani bekor qilishda xatolik');
        });
    }
}

// Baho berish modali
function showRatingModal(orderId) {
    const modalHtml = `
        <div class="modal fade" id="ratingModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Buyurtmani baholang</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-3">
                            <div class="rating-stars" data-order-id="${orderId}">
                                <span class="star" data-rating="1">⭐</span>
                                <span class="star" data-rating="2">⭐</span>
                                <span class="star" data-rating="3">⭐</span>
                                <span class="star" data-rating="4">⭐</span>
                                <span class="star" data-rating="5">⭐</span>
                            </div>
                        </div>
                        <textarea class="form-control" id="ratingComment" placeholder="Izoh (ixtiyoriy)" rows="3"></textarea>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Bekor qilish</button>
                        <button type="button" class="btn btn-primary" onclick="submitRating()">Baholash</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Star rating events
    document.querySelectorAll('.star').forEach(star => {
        star.addEventListener('click', function() {
            const rating = this.dataset.rating;
            const stars = this.parentElement.querySelectorAll('.star');
            
            stars.forEach((s, index) => {
                if (index < rating) {
                    s.style.color = '#ffc107';
                } else {
                    s.style.color = '#ddd';
                }
            });
            
            this.parentElement.dataset.selectedRating = rating;
        });
    });
    
    const modal = new bootstrap.Modal(document.getElementById('ratingModal'));
    modal.show();
}

// Bahoni yuborish
function submitRating() {
    const ratingElement = document.querySelector('.rating-stars');
    const rating = ratingElement.dataset.selectedRating;
    const comment = document.getElementById('ratingComment').value;
    const orderId = ratingElement.dataset.orderId;
    
    if (!rating) {
        alert('Iltimos, baho bering');
        return;
    }
    
    fetch('/api/submit-rating', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            order_id: orderId,
            rating: parseInt(rating),
            comment: comment
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Baho muvaffaqiyatli saqlandi!');
            const modal = bootstrap.Modal.getInstance(document.getElementById('ratingModal'));
            modal.hide();
            location.reload();
        } else {
            alert(data.message || 'Xatolik yuz berdi');
        }
    })
    .catch(error => {
        console.error('Baho yuborishda xatolik:', error);
        alert('Baho yuborishda xatolik');
    });
}

// Til o'zgartirish funksiyasi
function applyLanguage(lang) {
    console.log('Til tarjimasi qo\'llandi:', lang);
    const elements = document.querySelectorAll('[data-translate]');
    elements.forEach(element => {
        const key = element.dataset.translate;
        if (translations[lang] && translations[lang][key]) {
            if (element.tagName === 'INPUT' && element.type === 'submit') {
                element.value = translations[lang][key];
            } else if (element.placeholder !== undefined) {
                element.placeholder = translations[lang][key];
            } else {
                element.textContent = translations[lang][key];
            }
        }
    });
}

// Til sozlamasini saqlash
function saveLanguage(language) {
    console.log('Til saqlanyapti:', language);
    
    fetch('/api/set-language', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({language: language})
    })
    .then(response => response.json())
    .then(data => {
        console.log('Til o\'zgarishi javob:', data);
        if (data.success) {
            localStorage.setItem('language', language);
            applyLanguage(language);
        }
    })
    .catch(error => {
        console.error('Til saqlashda xatolik:', error);
    });
}

// Mavzuni o'zgartirish
function applyTheme(isDark) {
    if (isDark) {
        document.body.classList.add('dark-theme');
        console.log('Dark theme qo\'shildi');
    } else {
        document.body.classList.remove('dark-theme');
        console.log('Light theme qo\'shildi');
    }
}

// Font size ni o'zgartirish
function applyFontSize(size) {
    document.body.classList.remove('font-small', 'font-medium', 'font-large');
    document.body.classList.add(`font-${size}`);
    console.log('Font size qo\'shildi:', `font-${size}`);
}

// Sozlamalarni yuklash
function loadSettings() {
    const settings = {
        darkMode: localStorage.getItem('darkMode') === 'true',
        fontSize: localStorage.getItem('fontSize') || 'medium',
        language: localStorage.getItem('language') || 'uz'
    };
    
    console.log('DOMContentLoaded - Loading settings:', settings);
    
    applyTheme(settings.darkMode);
    applyFontSize(settings.fontSize);
    applyLanguage(settings.language);
    
    // Til classini qo'shish
    document.body.classList.remove('lang-uz', 'lang-ru', 'lang-en');
    document.body.classList.add(`lang-${settings.language}`);
    console.log('Language qo\'shildi:', `lang-${settings.language}`);
    
    return settings;
}

// Service Worker ro'yxatdan o'tkazish
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
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
                column: event.colno
            })
        }).catch(() => {}); // Silent fail
    } catch (e) {}
});

// DOMContentLoaded event
document.addEventListener('DOMContentLoaded', function() {
    // Sozlamalarni yuklash
    loadSettings();
    
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
    
    // Til o'zgartirish event listenerlari
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        const currentLang = localStorage.getItem('language') || 'uz';
        languageSelect.value = currentLang;
        
        languageSelect.addEventListener('change', function() {
            saveLanguage(this.value);
        });
    }
    
    // Theme toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const isDark = localStorage.getItem('darkMode') === 'true';
        themeToggle.checked = isDark;
        
        themeToggle.addEventListener('change', function() {
            const isDark = this.checked;
            localStorage.setItem('darkMode', isDark);
            applyTheme(isDark);
            
            // Server ga yuborish
            fetch('/api/set-theme', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dark_mode: isDark})
            }).catch(error => console.error('Theme saqlashda xatolik:', error));
        });
    }
    
    // Font size selector
    const fontSizeSelect = document.getElementById('fontSizeSelect');
    if (fontSizeSelect) {
        const currentSize = localStorage.getItem('fontSize') || 'medium';
        fontSizeSelect.value = currentSize;
        
        fontSizeSelect.addEventListener('change', function() {
            const size = this.value;
            localStorage.setItem('fontSize', size);
            applyFontSize(size);
        });
    }
});