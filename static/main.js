
// Savatcha sonini yangilash funksiyasi - API orqali
function updateCartCount() {
    fetch('/get_cart_count')
        .then(response => response.json())
        .then(data => {
            const cartBadge = document.querySelector('.cart-badge');
            if (cartBadge) {
                cartBadge.textContent = data.count;
                // Agar savatcha bo'sh bo'lsa, badge ni yashirish
                if (data.count === 0) {
                    cartBadge.style.display = 'none';
                } else {
                    cartBadge.style.display = 'flex';
                }
            }
        })
        .catch(error => {
            console.error('Savatcha sonini olishda xato:', error);
        });
}

// Miqdor o'zgartirish funksiyasi
function changeQuantity(button, change) {
    const input = button.parentElement.querySelector('input[name="quantity"]');
    let currentValue = parseInt(input.value) || 1;
    let newValue = currentValue + change;

    if (newValue < 1) newValue = 1;
    if (newValue > 99) newValue = 99;

    input.value = newValue;

    // Savatcha sonini yangilash
    setTimeout(updateCartCount, 100);
}

// Sahifa yuklanganda savatcha sonini yangilash
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();

    // Har 5 soniyada savatcha sonini tekshirish
    setInterval(updateCartCount, 5000);

    // Miqdor o'zgarganda ham yangilash
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            // Kichik kechikish bilan yangilash
            setTimeout(updateCartCount, 500);
        });
    });

    // + va - tugmalar uchun
    document.querySelectorAll('.quantity-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            setTimeout(updateCartCount, 500);
        });
    });
});

// Xodim dashboard uchun avtomatik yangilanish
if (window.location.pathname === '/staff') {
    setInterval(function() {
        location.reload();
    }, 10000); // 10 soniyada bir marta yangilanadi
}

// Foydalanuvchi holati uchun avtomatik yangilanish
if (window.location.pathname.includes('/user/success/')) {
    const ticketNo = window.location.pathname.split('/').pop();

    setInterval(function() {
        fetch(`/user/status/${ticketNo}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'given') {
                    const statusElement = document.querySelector('.status');
                    if (statusElement) {
                        statusElement.innerHTML = '<span style="color: green; font-weight: bold;">✅ Buyurtmangiz tayyor! Olib ketishingiz mumkin.</span>';
                    }
                }
            })
            .catch(error => {
                console.error('Holat tekshirishda xato:', error);
            });
    }, 5000); // 5 soniyada bir marta tekshirish
}
