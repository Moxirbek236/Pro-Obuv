// Savatcha sonini yangilash funksiyasi
function updateCartCount() {
    fetch('/get_cart_count')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const cartBadge = document.querySelector('.cart-badge');
            const cartCountElements = document.querySelectorAll('.cart-count');

            if (cartBadge) {
                cartBadge.textContent = data.count || 0;
                // Agar savatcha bo'sh bo'lsa, badge ni yashirish
                cartBadge.style.display = data.count > 0 ? 'flex' : 'none';
            }

            // Barcha cart-count elementlarini yangilash
            cartCountElements.forEach(element => {
                element.textContent = data.count || 0;
            });
        })
        .catch(error => {
            console.error('Savatcha sonini olishda xato:', error);
        });
}

// Miqdor oshirish funksiyasi
function increaseQuantity(button) {
    const input = button.parentElement.querySelector('input[name="quantity"]');
    if (input) {
        let currentValue = parseInt(input.value) || 1;
        if (currentValue < 99) {
            input.value = currentValue + 1;
        }
    }
}

// Miqdor kamaytirish funksiyasi
function decreaseQuantity(button) {
    const input = button.parentElement.querySelector('input[name="quantity"]');
    if (input) {
        let currentValue = parseInt(input.value) || 1;
        if (currentValue > 1) {
            input.value = currentValue - 1;
        }
    }
}

// Miqdor o'zgartirish funksiyasi (eski versiya uchun backward compatibility)
function changeQuantity(button, change) {
    if (change > 0) {
        increaseQuantity(button);
    } else {
        decreaseQuantity(button);
    }
}

// Loading animatsiyasini ko'rsatish
function showLoading(element) {
    if (element) {
        const originalText = element.innerHTML;
        element.innerHTML = '<span class="loading"></span> Yuklanmoqda...';
        element.disabled = true;

        // Ma'lum vaqtdan keyin qaytarish
        setTimeout(() => {
            element.innerHTML = originalText;
            element.disabled = false;
        }, 2000);
    }
}

// Form yuborish uchun loading qo'shish
function handleFormSubmit(form) {
    console.log('handleFormSubmit chaqirildi:', form);
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        console.log('Submit tugma topildi:', submitButton);
        showLoading(submitButton);

        // Form validation
        const requiredInputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.style.borderColor = '#e53e3e';
                input.classList.add('is-invalid');
            } else {
                input.style.borderColor = '#48bb78';
                input.classList.add('is-valid');
            }
        });

        if (!isValid) {
            submitButton.disabled = false;
            submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Yuborish';
            showNotification('Barcha majburiy maydonlarni to\'ldiring!', 'error');
            return false;
        }

        // Form ni submit qilish
        setTimeout(() => {
            form.submit();
        }, 100);

        return true;
    } else {
        console.log('Submit tugma topilmadi');
        return false;
    }
}

// Notification ko'rsatish funksiyasi
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification alert alert-${type}`;
    notification.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: inherit; font-size: 1.2rem; cursor: pointer; padding: 0; margin-left: 10px;">&times;</button>
        </div>
    `;

    document.body.appendChild(notification);

    // 5 soniyadan keyin avtomatik o'chirish
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Buyurtma holatini tekshirish
function checkOrderStatus(ticketNo) {
    if (!ticketNo) return;

    fetch(`/user/status/${ticketNo}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.ok) {
                updateOrderStatus(data);
            }
        })
        .catch(error => {
            console.error('Holat tekshirishda xato:', error);
        });
}

// Buyurtma holatini yangilash
function updateOrderStatus(data) {
    const statusElement = document.querySelector('.order-status');
    const queueElement = document.querySelector('.queue-position');
    const statusCard = document.querySelector('.order-status-card');

    if (statusElement) {
        let statusText = '';
        let statusClass = '';
        let cardColor = '';

        switch(data.status) {
            case 'waiting':
                statusText = '⏳ Buyurtmangiz tayyorlanmoqda...';
                statusClass = 'status-waiting';
                cardColor = 'linear-gradient(135deg, #ff9500 0%, #ff7b00 100%)';
                break;
            case 'ready':
                statusText = '✅ Buyurtmangiz tayyor! Olib ketishingiz mumkin.';
                statusClass = 'status-ready';
                cardColor = 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)';
                // Notification ko'rsatish
                if (Notification.permission === 'granted') {
                    new Notification('Buyurtmangiz tayyor!', {
                        body: 'Olib ketishingiz mumkin!',
                        icon: '/static/icon.png'
                    });
                }
                break;
            case 'served':
                statusText = '🎉 Buyurtmangiz berildi! Yoqimli ishtaha!';
                statusClass = 'status-served';
                cardColor = 'linear-gradient(135deg, #4299e1 0%, #3182ce 100%)';
                break;
            case 'cancelled':
                statusText = '❌ Buyurtmangiz bekor qilindi.';
                statusClass = 'status-cancelled';
                cardColor = 'linear-gradient(135deg, #e53e3e 0%, #c53030 100%)';
                break;
            default:
                statusText = '❓ Noma\'lum holat';
                statusClass = 'status-waiting';
                cardColor = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        }

        statusElement.innerHTML = `<span class="${statusClass}">${statusText}</span>`;

        // Status card rangini o'zgartirish
        if (statusCard) {
            const statusCardElement = statusCard.parentElement;
            statusCardElement.style.background = cardColor;

            // Status card ichidagi barcha yozuvlarni oq qilish
            const statusSpan = statusElement.querySelector('span');
            if (statusSpan) {
                statusSpan.style.color = 'white';
                statusSpan.style.background = 'rgba(255, 255, 255, 0.2)';
                statusSpan.style.borderColor = 'rgba(255, 255, 255, 0.4)';
            }
        }
    }

    if (queueElement && data.queue_position && data.status === 'waiting') {
        queueElement.innerHTML = `<span style="color: rgba(255,255,255,0.8);">Sizdan oldin: ${data.queue_position - 1} ta buyurtma</span>`;
    } else if (queueElement && data.status !== 'waiting') {
        queueElement.innerHTML = '';
    }
}

// Buyurtmani bekor qilish
function cancelOrder(ticketNo) {
    if (!confirm('Buyurtmani bekor qilishni xohlaysizmi?')) {
        return;
    }

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
        console.error('Bekor qilishda xato:', error);
        alert('Xatolik yuz berdi');
    });
}

// URL role parametrini qo'shish
function addRoleToURL() {
    const urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('role')) {
        // Session dan role ni aniqlash
        let userRole = 'guest';

        // Body class yoki session ma'lumotlaridan role ni aniqlash
        if (document.querySelector('.navbar-text')?.textContent.includes('Super Admin')) {
            userRole = 'admin';
        } else if (document.querySelector('.navbar-text')?.textContent.includes('👨‍💼')) {
            userRole = 'staff';
        } else if (document.querySelector('.navbar-text')?.textContent.includes('🚚')) {
            userRole = 'courier';
        } else if (document.querySelector('.navbar-text')?.textContent.includes('👤')) {
            userRole = 'user';
        }

        // URL ga role parametrini qo'shish
        if (userRole !== 'guest') {
            urlParams.set('role', userRole);
            const newURL = window.location.pathname + '?' + urlParams.toString();
            window.history.replaceState({}, '', newURL);

            // Body ga role class qo'shish
            document.body.classList.add('role-' + userRole);
        }
    }
}

// To'liq tarjima lug'ati
const translations = {
    'uz': {
        // Navbar
        'brand': '🍽️ Restoran',
        'menu': '📋 Menyu',
        'favorites': '❤️ Sevimlilar', 
        'contact': '📞 Aloqa',
        'about': '❓ Savollar',
        'downloads': '📱 Yuklamalar',
        'cart': '🛒 Savatcha',
        'login': '🔐 Kirish',
        'register': '📝 Ro\'yxat',

        // Profile dropdown
        'profile_info': '👤 Profil ma\'lumotlari',
        'profile_settings': '⚙️ Profil sozlamalari',
        'settings': '🔧 Sozlamalar',
        'logout': '🚪 Chiqish',

        // Sahifa matnlari
        'welcome': 'Bizning Restoranga Xush Kelibsiz!',
        'best_food': 'Eng mazali taomlar va a\'lo xizmat',
        'restaurant_order': 'Restoranda buyurtma berish',
        'restaurant_desc': 'Restoranda o\'tirib, navbat oling va buyurtma bering',
        'get_queue': 'Navbat olish',
        'delivery_service': 'Dostavka xizmati',
        'delivery_desc': 'Uyingizgacha yetkazib berish xizmati',
        'order_now': 'Buyurtma berish',
        'contact_us': 'Biz bilan bog\'lanish',
        'work_time': 'Ish vaqti',

        // Menu sahifasi
        'menu_title': 'Restoran Menyusi',
        'all_categories': 'Hammasi',
        'food_category': 'Taomlar',
        'drink_category': 'Ichimliklar',
        'add_to_cart': 'Qo\'shish',
        'add_to_favorites': 'Sevimli',

        // Cart sahifasi
        'cart_title': 'Savatcha',
        'delete': 'O\'chirish',
        'place_order': 'Buyurtma berish',
        'dine_in': 'Restoranda iste\'mol qilish',
        'delivery': 'Yetkazib berish',
        'total': 'Jami',
        'order_type': 'Buyurtma turi',
        'delivery_info_title': 'Yetkazib berish ma\'lumotlari',

        // Favorites sahifasi
        'favorites_title': 'Sevimli taomlarim',
        'remove': 'Olib tashlash',
        'no_favorites': 'Sevimli taomlaringiz yo\'q',
        'go_to_menu': 'Menyuga o\'tish',

        // About sahifasi
        'faq_title': 'Ko\'p so\'raladigan savollar',

        // Contact sahifasi
        'send_question': 'Savol yuborish',
        'send': 'Yuborish',

        // Downloads sahifasi
        'mobile_apps': 'Mobil Ilovalar',

        // Footer
        'copyright': '© 2025 Restoran Tizimi | Barcha huquqlar himoyalangan',
        'questions_phone': 'Savollar uchun: +998 99 145 96 86'
    },
    'ru': {
        // Navbar
        'brand': '🍽️ Ресторан',
        'menu': '📋 Меню',
        'favorites': '❤️ Избранное',
        'contact': '📞 Контакты', 
        'about': '❓ Вопросы',
        'downloads': '📱 Загрузки',
        'cart': '🛒 Корзина',
        'login': '🔐 Вход',
        'register': '📝 Регистрация',

        // Profile dropdown
        'profile_info': '👤 Данные профиля',
        'profile_settings': '⚙️ Настройки профиля',
        'settings': '🔧 Настройки',
        'logout': '🚪 Выход',

        // Sahifa matnlari
        'welcome': 'Добро пожаловать в наш ресторан!',
        'best_food': 'Самые вкусные блюда и отличный сервис',
        'restaurant_order': 'Заказ в ресторане',
        'restaurant_desc': 'Займите очередь и сделайте заказ в ресторане',
        'get_queue': 'Занять очередь',
        'delivery_service': 'Служба доставки',
        'delivery_desc': 'Доставка на дом',
        'order_now': 'Заказать',
        'contact_us': 'Связаться с нами',
        'work_time': 'Время работы',

        // Menu sahifasi
        'menu_title': 'Меню ресторана',
        'all_categories': 'Все',
        'food_category': 'Блюда',
        'drink_category': 'Напитки',
        'add_to_cart': 'Добавить',
        'add_to_favorites': 'Избранное',

        // Cart sahifasi
        'cart_title': 'Корзина',
        'delete': 'Удалить',
        'place_order': 'Оформить заказ',
        'dine_in': 'В ресторане',
        'delivery': 'Доставка',
        'total': 'Итого',
        'order_type': 'Тип заказа',
        'delivery_info_title': 'Информация о доставке',

        // Favorites sahifasi
        'favorites_title': 'Мои избранные блюда',
        'remove': 'Удалить',
        'no_favorites': 'У вас нет избранных блюд',
        'go_to_menu': 'Перейти в меню',

        // About sahifasi
        'faq_title': 'Часто задаваемые вопросы',

        // Contact sahifasi
        'send_question': 'Отправить вопрос',
        'send': 'Отправить',

        // Downloads sahifasi
        'mobile_apps': 'Мобильные приложения',

        // Footer
        'copyright': '© 2025 Система ресторана | Все права защищены',
        'questions_phone': 'По вопросам: +998 99 145 96 86'
    },
    'en': {
        // Navbar
        'brand': '🍽️ Restaurant',
        'menu': '📋 Menu',
        'favorites': '❤️ Favorites',
        'contact': '📞 Contact',
        'about': '❓ About',
        'downloads': '📱 Downloads',
        'cart': '🛒 Cart',
        'login': '🔐 Login',
        'register': '📝 Register',

        // Profile dropdown
        'profile_info': '👤 Profile Info',
        'profile_settings': '⚙️ Profile Settings',
        'settings': '🔧 Settings',
        'logout': '🚪 Logout',

        // Sahifa matnlari
        'welcome': 'Welcome to our Restaurant!',
        'best_food': 'The most delicious food and excellent service',
        'restaurant_order': 'Restaurant Order',
        'restaurant_desc': 'Take a queue and order at the restaurant',
        'get_queue': 'Get Queue',
        'delivery_service': 'Delivery Service',
        'delivery_desc': 'Home delivery service',
        'order_now': 'Order Now',
        'contact_us': 'Contact Us',
        'work_time': 'Working Hours',

        // Menu sahifasi
        'menu_title': 'Restaurant Menu',
        'all_categories': 'All',
        'food_category': 'Food',
        'drink_category': 'Drinks',
        'add_to_cart': 'Add',
        'add_to_favorites': 'Favorite',

        // Cart sahifasi
        'cart_title': 'Cart',
        'delete': 'Delete',
        'place_order': 'Place Order',
        'dine_in': 'Dine In',
        'delivery': 'Delivery',
        'total': 'Total',
        'order_type': 'Order Type',
        'delivery_info_title': 'Delivery Information',

        // Favorites sahifasi
        'favorites_title': 'My Favorite Foods',
        'remove': 'Remove',
        'no_favorites': 'You have no favorite foods',
        'go_to_menu': 'Go to Menu',

        // About sahifasi
        'faq_title': 'Frequently Asked Questions',

        // Contact sahifasi
        'send_question': 'Send Question',
        'send': 'Send',

        // Downloads sahifasi
        'mobile_apps': 'Mobile Applications',

        // Footer
        'copyright': '© 2025 Restaurant System | All rights reserved',
        'questions_phone': 'For questions: +998 99 145 96 86'
    }
};

function translatePage(language) {
    const lang = translations[language] || translations['uz'];

    // Mavzu sozlamalarini yuklash va qo'llash
    const darkMode = localStorage.getItem('darkMode') === 'true';
    const fontSize = localStorage.getItem('fontSize') || 'medium';

    // Body klasslarini yangilash
    document.body.classList.remove('dark-theme', 'font-small', 'font-medium', 'font-large', 'font-xlarge');
    document.body.classList.remove('lang-uz', 'lang-ru', 'lang-en');

    // Mavzu klassini qo'shish
    if (darkMode) {
        document.body.classList.add('dark-theme');
    }

    // Font o'lcham klassini qo'shish
    document.body.classList.add('font-' + fontSize);

    // Til klassini qo'shish
    document.body.classList.add('lang-' + language);

    // Navbar brand
    const brand = document.querySelector('.navbar-brand');
    if (brand) brand.textContent = lang.brand;

    // Navbar links
    const menuLink = document.querySelector('a[href*="menu"]');
    if (menuLink) menuLink.innerHTML = lang.menu;

    const favoritesLink = document.querySelector('a[href*="favorites"]');
    if (favoritesLink) favoritesLink.innerHTML = lang.favorites;

    const contactLink = document.querySelector('a[href*="contact"]');
    if (contactLink) contactLink.innerHTML = lang.contact;

    const aboutLink = document.querySelector('a[href*="about"]');
    if (aboutLink) aboutLink.innerHTML = lang.about;

    const downloadsLink = document.querySelector('a[href*="downloads"]');
    if (downloadsLink) downloadsLink.innerHTML = lang.downloads;

    const cartLink = document.querySelector('a[href*="cart"]');
    if (cartLink) {
        const cartBadge = cartLink.querySelector('.cart-badge');
        const badgeHTML = cartBadge ? cartBadge.outerHTML : '';
        cartLink.innerHTML = `${lang.cart} ${badgeHTML}`;
    }

    // Login/Register links
    const loginLink = document.querySelector('a[href*="login"]');
    if (loginLink) loginLink.innerHTML = lang.login;

    const registerLink = document.querySelector('a[href*="register"]');
    if (registerLink) registerLink.innerHTML = lang.register;

    // Profile dropdown items
    document.querySelectorAll('.dropdown-item').forEach(item => {
        if (item.innerHTML.includes('Profil ma\'lumotlari') || item.innerHTML.includes('Данные профиля') || item.innerHTML.includes('Profile Info')) {
            item.innerHTML = lang.profile_info;
        } else if (item.innerHTML.includes('Profil sozlamalari') || item.innerHTML.includes('Настройки профиля') || item.innerHTML.includes('Profile Settings')) {
            item.innerHTML = lang.profile_settings;
        } else if (item.innerHTML.includes('Sozlamalar') || item.innerHTML.includes('Настройки') || item.innerHTML.includes('Settings')) {
            item.innerHTML = lang.settings;
        } else if (item.innerHTML.includes('Chiqish') || item.innerHTML.includes('Выход') || item.innerHTML.includes('Logout')) {
            item.innerHTML = lang.logout;
        }
    });

    // Hero section (bosh sahifa uchun)
    const heroTitle = document.querySelector('.hero-section h1, .display-4');
    if (heroTitle) heroTitle.innerHTML = `🍽️ ${lang.welcome}`;

    const heroSubtitle = document.querySelector('.hero-section .lead');
    if (heroSubtitle) heroSubtitle.textContent = lang.best_food;

    // Service cards
    document.querySelectorAll('.service-card h3').forEach((title, index) => {
        if (index === 0) {
            title.textContent = lang.restaurant_order;
        } else if (index === 1) {
            title.textContent = lang.delivery_service;
        }
    });

    document.querySelectorAll('.service-card p').forEach((desc, index) => {
        if (index === 0) {
            desc.textContent = lang.restaurant_desc;
        } else if (index === 1) {
            desc.textContent = lang.delivery_desc;
        }
    });

    document.querySelectorAll('.btn-service').forEach((btn, index) => {
        if (index === 0) {
            btn.textContent = lang.get_queue;
        } else if (index === 1) {
            btn.textContent = lang.order_now;
        }
    });

    // Contact section
    const contactTitle = document.querySelector('h3');
    if (contactTitle && contactTitle.innerHTML.includes('bog\'lanish')) {
        contactTitle.innerHTML = `📞 ${lang.contact_us}`;
    }

    // Footer
    const copyright = document.querySelector('.footer p:first-child');
    if (copyright) copyright.textContent = lang.copyright;

    const questionsPhone = document.querySelector('.footer .muted');
    if (questionsPhone) questionsPhone.textContent = lang.questions_phone;

    // Data attributelarini yangilash
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        if (lang[key]) {
            element.textContent = lang[key];
        }
    });

    // Barcha sahifalar uchun umumiy elementlar
    // Menu sahifasi
    if (window.location.pathname.includes('/menu')) {
        const menuTitle = document.querySelector('.menu-title');
        if (menuTitle) menuTitle.textContent = `🍽️ ${lang.menu_title || 'Restoran Menyusi'}`;

        const categoryButtons = document.querySelectorAll('.category-btn');
        if (categoryButtons.length > 0) {
            categoryButtons[0].textContent = lang.all_categories || 'Hammasi';
            categoryButtons[1].textContent = lang.food_category || '🍽️ Taomlar';
            categoryButtons[2].textContent = lang.drink_category || '🥤 Ichimliklar';
        }

        const addToCartButtons = document.querySelectorAll('.btn-add-cart');
        addToCartButtons.forEach(btn => {
            if (btn.innerHTML.includes('Qo\'shish')) {
                btn.innerHTML = `🛒 ${lang.add_to_cart || 'Qo\'shish'}`;
            } else if (btn.innerHTML.includes('Sevimli')) {
                btn.innerHTML = `❤️ ${lang.add_to_favorites || 'Sevimli'}`;
            }
        });
    }

    // Savatcha sahifasi
    if (window.location.pathname.includes('/cart')) {
        const cartTitle = document.querySelector('.section-title');
        if (cartTitle) cartTitle.innerHTML = `🛒 ${lang.cart}`;

        const deleteButtons = document.querySelectorAll('.btn.danger');
        deleteButtons.forEach(btn => {
            btn.innerHTML = `🗑️ ${lang.delete || 'O\'chirish'}`;
        });

        const checkoutButton = document.querySelector('#checkout-button');
        if (checkoutButton) {
            checkoutButton.innerHTML = `🛒 ${lang.place_order || 'Buyurtma berish'}`;
        }

        // Order type labels
        const dineInLabel = document.querySelector('input[value="dine_in"]');
        if (dineInLabel && dineInLabel.nextElementSibling) {
            dineInLabel.nextElementSibling.innerHTML = `🍽️ ${lang.dine_in || 'Restoranda iste\'mol qilish'}`;
        }

        const deliveryLabel = document.querySelector('input[value="delivery"]');
        if (deliveryLabel && deliveryLabel.nextElementSibling) {
            deliveryLabel.nextElementSibling.innerHTML = `🚚 ${lang.delivery || 'Yetkazib berish'}`;
        }
    }

    // Favorites sahifasi
    if (window.location.pathname.includes('/favorites')) {
        const favoritesTitle = document.querySelector('h2');
        if (favoritesTitle) favoritesTitle.innerHTML = `❤️ ${lang.favorites_title || 'Sevimli taomlarim'}`;

        const removeButtons = document.querySelectorAll('.btn[style*="background: #dc3545"]');
        removeButtons.forEach(btn => {
            btn.innerHTML = `🗑️ ${lang.remove || 'Olib tashlash'}`;
        });
    }

    // About sahifasi
    if (window.location.pathname.includes('/about')) {
        const aboutTitle = document.querySelector('h2');
        if (aboutTitle) aboutTitle.innerHTML = `❓ ${lang.faq_title || 'Ko\'p so\'raladigan savollar'}`;
    }

    // Contact sahifasi
    if (window.location.pathname.includes('/contact')) {
        const contactFormTitle = document.querySelector('h4');
        if (contactFormTitle) contactFormTitle.innerHTML = `📋 ${lang.send_question || 'Savol yuborish'}`;

        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton) submitButton.innerHTML = `📨 ${lang.send || 'Yuborish'}`;
    }

    // Downloads sahifasi
    if (window.location.pathname.includes('/downloads')) {
        const downloadTitle = document.querySelector('h1');
        if (downloadTitle) downloadTitle.innerHTML = `📱 ${lang.mobile_apps || 'Mobil Ilovalar'}`;
    }
}

// Til o'zgartirishni global qilish
window.changeLanguage = function(language) {
    console.log('Til o\'zgartirilmoqda:', language);

    // Darhol til klassini va tarjimani qo'llash
    document.body.classList.remove('lang-uz', 'lang-ru', 'lang-en');
    document.body.classList.add('lang-' + language);

    localStorage.setItem('language', language);
    translatePage(language);

    // Server ga yuborish
    fetch('/api/set-language', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language: language })
    }).then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Til muvaffaqiyatli saqlandi:', language);

            // 1 soniya kutib, sahifani qayta yuklash
            setTimeout(() => {
                location.reload();
            }, 1000);
        }
    }).catch(error => {
        console.log('Til sozlamasini saqlashda xato:', error);
        location.reload();
    });
};

function translateToRussian() {
    changeLanguage('ru');
}

function translateToEnglish() {
    changeLanguage('en');
}

// Global mavzu o'zgartirish funksiyasi
window.toggleDarkMode = function(isDark) {
    // Body klassini o'zgartirish
    if (isDark) {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }

    // LocalStorage ga saqlash
    localStorage.setItem('darkMode', isDark.toString());

    // Server ga yuborish
    fetch('/api/set-theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ dark_mode: isDark })
    }).catch(error => console.log('Mavzu sozlamasini saqlashda xato:', error));
};

// Global font o'lcham o'zgartirish funksiyasi
window.changeFontSize = function(size) {
    // Eski klasslarni olib tashlash
    document.body.classList.remove('font-small', 'font-medium', 'font-large', 'font-xlarge');

    // Yangi klassni qo'shish
    document.body.classList.add('font-' + size);

    // LocalStorage ga saqlash
    localStorage.setItem('fontSize', size);

    // Server ga yuborish
    const language = localStorage.getItem('language') || 'uz';
    const darkMode = localStorage.getItem('darkMode') === 'true';

    fetch('/api/save-settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            language: language,
            font_size: size,
            dark_theme: darkMode
        })
    }).catch(error => console.log('Font o\'lcham sozlamasini saqlashda xato:', error));
};

// Sahifa yuklanganda ishga tushiradigan funksiyalar
document.addEventListener('DOMContentLoaded', function() {
    // URL role parametrini qo'shish
    addRoleToURL();

    // Barcha sozlamalarni darhol yuklash va qo'llash
    const darkMode = localStorage.getItem('darkMode') === 'true';
    const fontSize = localStorage.getItem('fontSize') || 'medium';
    const language = localStorage.getItem('language') || 'uz';

    // Body klasslarini tozalash
    document.body.classList.remove('dark-theme', 'font-small', 'font-medium', 'font-large', 'font-xlarge');
    document.body.classList.remove('lang-uz', 'lang-ru', 'lang-en');

    // Mavzu klassini qo'shish
    if (darkMode) {
        document.body.classList.add('dark-theme');
    }

    // Font o'lcham klassini qo'shish
    document.body.classList.add('font-' + fontSize);

    // Til klassini qo'shish
    document.body.classList.add('lang-' + language);

    // Tilni tarjima qilish
    translatePage(language);

    // Savatcha sonini dastlabki yuklanish
    updateCartCount();

    // Har 5 soniyada savatcha sonini yangilash
    setInterval(updateCartCount, 5000);

    // Form submit eventlarini tinglash
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Buyurtma berish formi uchun maxsus logic
            if (this.action && this.action.includes('/user')) {
                console.log('Buyurtma berish formi submit qilindi');

                // Formda kerakli maydonlar borligini tekshirish
                const requiredFields = this.querySelectorAll('input[required], select[required]');
                let isValid = true;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        isValid = false;
                        field.style.borderColor = 'red';
                    } else {
                        field.style.borderColor = '';
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    alert('Barcha majburiy maydonlarni to\'ldiring!');
                    return false;
                }

                // Loading ko'rsatish
                handleFormSubmit(this);
            }
        });
    });

    // Miqdor inputlariga event listener qo'shish
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const value = parseInt(this.value);
            if (isNaN(value) || value < 1) {
                this.value = 1;
            } else if (value > 99) {
                this.value = 99;
            }

            // Savatcha sonini yangilash
            setTimeout(updateCartCount, 500);
        });
    });

    // Buyurtma holati sahifasi uchun
    const currentPath = window.location.pathname;
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

// Xodim dashboard uchun avtomatik yangilanish
if (window.location.pathname === '/staff') {
    let reloadInterval = setInterval(function() {
        // Faqat foydalanuvchi sahifada faol bo'lsa yangilash
        if (!document.hidden) {
            location.reload();
        }
    }, 10000); // 10 soniyada bir marta

    // Sahifa yashirilganda intervallarni to'xtatish
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            clearInterval(reloadInterval);
        } else {
            reloadInterval = setInterval(function() {
                location.reload();
            }, 10000);
        }
    });
}

// Monitor sahifasi uchun avtomatik yangilanish
if (window.location.pathname === '/monitor') {
    setInterval(function() {
        if (!document.hidden) {
            location.reload();
        }
    }, 5000); // 5 soniyada bir marta
}

// Service Worker registratsiyasi (ixtiyoriy)
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

// Utility funksiyalar
function formatPrice(price) {
    return new Intl.NumberFormat('uz-UZ').format(price) + ' so\'m';
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('uz-UZ', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// Error handling uchun global function
window.addEventListener('error', function(e) {
    console.error('JavaScript xatosi:', e.error);
});