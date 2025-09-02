// ===== GLOBAL VARIABLES =====
// Current path variable declaration
let currentLanguage = 'uz';
// Global o'zgaruvchilarni xavfsiz e'lon qilish
window.currentPath = window.location.pathname || '/';

// Til tarjimalari - faqat bir marta e'lon qilish
if (typeof window.translations === 'undefined') {
    window.translations = {
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

    // Global scope ga qo'shish
    window.translations = translations;
} else {
    translations = window.translations;
}

// ===== CART FUNCTIONS =====
// Savatcha sonini yangilash funksiyasi
function updateCartCount(retryCount = 0) {
    const maxRetries = 3;

    // The API endpoint for fetching cart count has been corrected to '/api/cart-count'
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
        console.error('JavaScript xatosi:', error.message || error);

        if (retryCount < maxRetries) {
            console.log(`Qayta urinish ${retryCount + 1}/${maxRetries}`);
            setTimeout(() => updateCartCount(retryCount + 1), 1000 * (retryCount + 1));
        } else {
            console.error('Savatcha sonini yangilashda xatolik:', error.message || error);
            // Default count ko'rsatish
            const cartCountElement = document.querySelector('.cart-count, #cart-count, [data-cart-count]');
            if (cartCountElement) {
                cartCountElement.textContent = '0';
                cartCountElement.style.display = 'inline-block';
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

// Current path variable is already defined as window.currentPath above

// Til o'zgartirish funksiyasi
function applyLanguage(lang) {
    const translationsObj = window.translations;
    if (!translationsObj || !translationsObj[lang]) {
        console.warn('Til topilmadi:', lang);
        return;
    }

    const langData = translationsObj[lang];
    const elements = document.querySelectorAll('[data-translate]');
    elements.forEach(element => {
        const key = element.dataset.translate;
        if (langData && langData[key]) {
            if (element.tagName === 'INPUT' && element.type === 'submit') {
                element.value = langData[key];
            } else if (element.placeholder !== undefined) {
                element.placeholder = langData[key];
            } else {
                element.textContent = langData[key];
            }
        }
    });

    console.log('Til tarjimasi qo\'llandi:', lang);
}

// Super Admin Dashboard funksiyalari
function initializeSuperAdminDashboard() {
    console.log('Super admin dashboard funksiyalari ishga tushirildi');

    // Tab funksiyalarini global qilish
    window.showTab = showTab;
    window.loadOrders = loadOrders;
    window.loadMenu = loadMenu;
    window.loadReceipts = loadReceipts;
    window.loadRatings = loadRatings;

    // Modal funksiyalarini global qilish
    window.showAddStaffModal = showAddStaffModal;
    window.showAddCourierModal = showAddCourierModal;
    window.showAddMenuModal = showAddMenuModal;
    window.showAddBranchModal = showAddBranchModal;
    window.closeModal = closeModal;

    // Password reset funksiyalarini global qilish
    window.resetStaffPassword = resetStaffPassword;
    window.resetCourierPassword = resetCourierPassword;
    window.resetUserPassword = resetUserPassword;
}

// Super Admin Dashboard tab functions
function showTab(tabName) {
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.remove('active'));

    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => button.classList.remove('active'));

    document.getElementById(tabName).classList.add('active');

    // Find and activate the correct button
    buttons.forEach(button => {
        // Assuming button text or data attribute can identify the tab
        // This part might need adjustment based on actual HTML structure
        if (button.dataset.tabTarget === tabName) {
            button.classList.add('active');
        }
    });

    if (tabName === 'orders') {
        loadOrders();
    } else if (tabName === 'menu') {
        loadMenu();
    } else if (tabName === 'receipts') {
        loadReceipts();
    } else if (tabName === 'ratings') {
        loadRatings();
    }
}

// Buyurtmalarni yuklash
function loadOrders() {
    console.log('Buyurtmalarni yuklash boshlandi');

    const ordersContainer = document.getElementById('orders-data');
    if (!ordersContainer) {
        console.error('Orders container topilmadi');
        return;
    }

    ordersContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Buyurtmalar yuklanmoqda...</p></div>';

    fetch('/super-admin/get-orders')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Buyurtmalar muvaffaqiyatli yuklandi:', data.length);
            displayOrders(data);
        })
        .catch(error => {
            console.error('Buyurtmalarni yuklashda xatolik:', error);
            ordersContainer.innerHTML = '<div class="alert alert-danger">Buyurtmalarni yuklashda xatolik yuz berdi.</div>';
        });
}

// Buyurtmalarni ko'rsatish
function displayOrders(orders) {
    const ordersContainer = document.getElementById('orders-data');
    if (!ordersContainer) return;

    if (!orders || orders.length === 0) {
        ordersContainer.innerHTML = '<div class="alert alert-info">Hozircha buyurtmalar yo\'q.</div>';
        return;
    }

    let html = '<div class="table-container"><table class="admin-table"><thead><tr>';
    html += '<th>ID</th><th>Mijoz</th><th>Tiket</th><th>Turi</th><th>Status</th><th>Manzil</th><th>Kuryer</th><th>Vaqt</th>';
    html += '</tr></thead><tbody>';

    orders.forEach(order => {
        html += '<tr>';
        html += `<td>${order.id}</td>`;
        html += `<td>${order.customer_name || 'N/A'}</td>`;
        html += `<td><strong>#${order.ticket_no}</strong></td>`;
        html += `<td>${order.order_type || 'dine_in'}</td>`;
        html += `<td><span class="badge ${getStatusClass(order.status)}">${getStatusText(order.status)}</span></td>`;
        html += `<td>${order.delivery_address || 'N/A'}</td>`;
        html += `<td>${order.courier_id || 'N/A'}</td>`;
        html += `<td>${order.created_at ? order.created_at.substring(0, 16).replace('T', ' ') : 'N/A'}</td>`;
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    ordersContainer.innerHTML = html;
}

// Status class olish
function getStatusClass(status) {
    const statusClasses = {
        'waiting': 'bg-warning',
        'ready': 'bg-info',
        'served': 'bg-success',
        'cancelled': 'bg-danger',
        'on_way': 'bg-primary',
        'delivered': 'bg-success'
    };
    return statusClasses[status] || 'bg-secondary';
}

// Status text olish
function getStatusText(status) {
    const statusTexts = {
        'waiting': 'Kutilmoqda',
        'ready': 'Tayyor',
        'served': 'Berildi',
        'cancelled': 'Bekor qilindi',
        'on_way': 'Yo\'lda',
        'delivered': 'Yetkazildi'
    };
    return statusTexts[status] || status;
}

// Menyuni yuklash
function loadMenu() {
    console.log('Menyu yuklanmoqda');
    const menuContainer = document.getElementById('menu-data');
    if (!menuContainer) return;

    menuContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Menyu yuklanmoqda...</p></div>';

    fetch('/super-admin/get-menu')
        .then(response => response.json())
        .then(data => {
            console.log('Menyu muvaffaqiyatli yuklandi:', data.length);
            displayMenu(data);
        })
        .catch(error => {
            console.error('Menyuni yuklashda xatolik:', error);
            menuContainer.innerHTML = '<div class="alert alert-danger">Menyuni yuklashda xatolik yuz berdi.</div>';
        });
}

// Menyuni ko'rsatish
function displayMenu(menuItems) {
    const menuContainer = document.getElementById('menu-data');
    if (!menuContainer) return;

    if (!menuItems || menuItems.length === 0) {
        menuContainer.innerHTML = '<div class="alert alert-info">Menyu bo\'sh.</div>';
        return;
    }

    let html = '<div class="table-container"><table class="admin-table"><thead><tr>';
    html += '<th>ID</th><th>Nomi</th><th>Narxi</th><th>Kategoriya</th><th>Tavsif</th><th>Mavjud</th><th>Rasm</th>';
    html += '</tr></thead><tbody>';

    menuItems.forEach(item => {
        html += '<tr>';
        html += `<td>${item.id}</td>`;
        html += `<td>${item.name}</td>`;
        html += `<td>${item.price} so'm</td>`;
        html += `<td>${item.category}</td>`;
        html += `<td>${item.description || 'N/A'}</td>`;
        html += `<td>${item.available ? '✅' : '❌'}</td>`;
        html += `<td>${item.image_url ? '<img src="' + item.image_url + '" width="50">' : 'N/A'}</td>`;
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    menuContainer.innerHTML = html;
}

// Cheklar yuklash
function loadReceipts() {
    console.log('Cheklar yuklanmoqda');
    const receiptsContainer = document.getElementById('receipts-data');
    if (!receiptsContainer) return;

    receiptsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Cheklar yuklanmoqda...</p></div>';

    fetch('/super-admin/get-receipts')
        .then(response => response.json())
        .then(data => {
            console.log('Cheklar muvaffaqiyatli yuklandi:', data.length);
            displayReceipts(data);
        })
        .catch(error => {
            console.error('Cheklarni yuklashda xatolik:', error);
            receiptsContainer.innerHTML = '<div class="alert alert-danger">Cheklarni yuklashda xatolik yuz berdi.</div>';
        });
}

// Cheklarni ko'rsatish
function displayReceipts(receipts) {
    const receiptsContainer = document.getElementById('receipts-data');
    if (!receiptsContainer) return;

    if (!receipts || receipts.length === 0) {
        receiptsContainer.innerHTML = '<div class="alert alert-info">Hozircha cheklar yo\'q.</div>';
        return;
    }

    let html = '<div class="table-container"><table class="admin-table"><thead><tr>';
    html += '<th>Chek raqami</th><th>Buyurtma ID</th><th>Summa</th><th>Cashback</th><th>Vaqt</th>';
    html += '</tr></thead><tbody>';

    receipts.forEach(receipt => {
        html += '<tr>';
        html += `<td><strong>${receipt.receipt_number}</strong></td>`;
        html += `<td>${receipt.order_id}</td>`;
        html += `<td>${receipt.total_amount} so'm</td>`;
        html += `<td>${receipt.cashback_amount} so'm</td>`;
        html += `<td>${receipt.created_at ? receipt.created_at.substring(0, 16).replace('T', ' ') : 'N/A'}</td>`;
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    receiptsContainer.innerHTML = html;
}

// Baholarni yuklash
function loadRatings() {
    console.log('Baholar yuklanmoqda');
    const ratingsContainer = document.getElementById('ratings-data');
    if (!ratingsContainer) return;

    ratingsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Baholar yuklanmoqda...</p></div>';

    fetch('/super-admin/get-ratings')
        .then(response => response.json())
        .then(data => {
            console.log('Baholar muvaffaqiyatli yuklandi:', data);
            displayRatings(data);
        })
        .catch(error => {
            console.error('Baholarni yuklashda xatolik:', error);
            ratingsContainer.innerHTML = '<div class="alert alert-danger">Baholarni yuklashda xatolik yuz berdi.</div>';
        });
}

// Baholarni ko'rsatish
function displayRatings(data) {
    const ratingsContainer = document.getElementById('ratings-data');
    if (!ratingsContainer) return;

    let html = '<div class="ratings-container">';

    // Mahsulot baholari
    html += '<div class="ratings-section"><h4>📋 Mahsulot baholari</h4>';
    if (data.menu_ratings && data.menu_ratings.length > 0) {
        html += '<div class="table-container"><table class="admin-table"><thead><tr>';
        html += '<th>Mahsulot</th><th>Foydalanuvchi</th><th>Baho</th><th>Sharh</th><th>Vaqt</th>';
        html += '</tr></thead><tbody>';

        data.menu_ratings.forEach(rating => {
            html += '<tr>';
            html += `<td><strong>${rating.menu_item_name}</strong></td>`;
            html += `<td>${rating.user_name}</td>`;
            html += `<td>${'⭐'.repeat(rating.rating)}${'☆'.repeat(5 - rating.rating)} (${rating.rating}/5)</td>`;
            html += `<td>${rating.comment || 'Sharh yo\'q'}</td>`;
            html += `<td>${rating.created_at ? rating.created_at.substring(0, 16).replace('T', ' ') : 'N/A'}</td>`;
            html += '</tr>';
        });

        html += '</tbody></table></div>';
    } else {
        html += '<p class="text-center">Hali mahsulot baholari yo\'q.</p>';
    }
    html += '</div>';

    // Filial baholari
    html += '<div class="ratings-section"><h4>🏢 Filial baholari</h4>';
    if (data.branch_ratings && data.branch_ratings.length > 0) {
        html += '<div class="table-container"><table class="admin-table"><thead><tr>';
        html += '<th>Filial</th><th>Foydalanuvchi</th><th>Baho</th><th>Sharh</th><th>Vaqt</th>';
        html += '</tr></thead><tbody>';

        data.branch_ratings.forEach(rating => {
            html += '<tr>';
            html += `<td><strong>${rating.branch_name}</strong></td>`;
            html += `<td>${rating.user_name}</td>`;
            html += `<td>${'⭐'.repeat(rating.rating)}${'☆'.repeat(5 - rating.rating)} (${rating.rating}/5)</td>`;
            html += `<td>${rating.comment || 'Sharh yo\'q'}</td>`;
            html += `<td>${rating.created_at ? rating.created_at.substring(0, 16).replace('T', ' ') : 'N/A'}</td>`;
            html += '</tr>';
        });

        html += '</tbody></table></div>';
    } else {
        html += '<p class="text-center">Hali filial baholari yo\'q.</p>';
    }
    html += '</div>';

    html += '</div>';
    ratingsContainer.innerHTML = html;
}

// Modal funksiyalari
function showAddStaffModal() {
    const modal = document.getElementById('addStaffModal');
    if (modal) modal.style.display = 'block';
}

function showAddCourierModal() {
    const modal = document.getElementById('addCourierModal');
    if (modal) modal.style.display = 'block';
}

function showAddMenuModal() {
    const modal = document.getElementById('addMenuModal');
    if (modal) modal.style.display = 'block';
}

function showAddBranchModal() {
    const modal = document.getElementById('addBranchModal');
    if (modal) modal.style.display = 'block';
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
}

// Parol reset funksiyalari
function resetStaffPassword(staffId) {
    const newPassword = prompt('Yangi parolni kiriting:');
    if (newPassword) {
        fetch('/super-admin/reset-staff-password', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({staff_id: staffId, new_password: newPassword})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Parol muvaffaqiyatli yangilandi!');
            } else {
                alert('Xatolik: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Parol yangilashda xatolik:', error);
            alert('Parol yangilashda xatolik yuz berdi.');
        });
    }
}

function resetCourierPassword(courierId) {
    const newPassword = prompt('Yangi parolni kiriting:');
    if (newPassword) {
        fetch('/super-admin/reset-courier-password', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({courier_id: courierId, new_password: newPassword})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Parol muvaffaqiyatli yangilandi!');
            } else {
                alert('Xatolik: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Parol yangilashda xatolik:', error);
            alert('Parol yangilashda xatolik yuz berdi.');
        });
    }
}

function resetUserPassword(userId) {
    const newPassword = prompt('Yangi parolni kiriting:');
    if (newPassword) {
        fetch('/super-admin/reset-user-password', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: userId, new_password: newPassword})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Parol muvaffaqiyatli yangilandi!');
            } else {
                alert('Xatolik: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Parol yangilashda xatolik:', error);
            alert('Parol yangilashda xatolik yuz berdi.');
        });
    }
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
    .catch(error => console.error('Til saqlashda xatolik:', error));
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

// Xatoliklarni serverga yuborish
window.addEventListener('error', function(e) {
    console.log('JavaScript xatosi:', {
        message: e.message || 'Unknown error',
        source: e.filename || 'Unknown source',
        line: e.lineno || 0,
        column: e.colno || 0
    });

    fetch('/api/log-error', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: e.message || 'Unknown error',
            source: e.filename || 'Unknown source',
            line: e.lineno || 0,
            column: e.colno || 0
        })
    }).catch(err => console.log('Error logging failed:', err));
});

// DOMContentLoaded event
document.addEventListener('DOMContentLoaded', function() {
    // currentPath ni yangilash
    currentPath = window.location.pathname || '/';

    // Sozlamalarni yuklash
    loadSettings();

    // Savatcha sonini yangilash
    updateCartCount();

    // Super admin sahifasi ekanligini tekshirish
    const isSuperAdminPage = currentPath.includes('super-admin-dashboard');

    if (isSuperAdminPage) {
        console.log('Super admin dashboard yuklandi');
        // Super admin uchun maxsus JavaScript
        initializeSuperAdminDashboard();
    }

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