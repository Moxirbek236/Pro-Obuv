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

// Sahifa yuklanganda ishga tushiradigan funksiyalar
document.addEventListener('DOMContentLoaded', function() {
    // URL role parametrini qo'shish
    addRoleToURL();
    
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