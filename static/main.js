

// Savatcha sonini yangilash funksiyasi
function updateCartCount() {
    // Faqat savatcha sahifasida mahsulotlar sonini to'g'ridan-to'g'ri hisoblash
    const cartItems = document.querySelectorAll('.cart-item');
    let totalCount = 0;
    
    // Har bir savatcha elementida miqdorni olish
    cartItems.forEach(item => {
        const quantityText = item.querySelector('.item-info p');
        if (quantityText) {
            // "Miqdor: 2" formatidan raqamni ajratib olish
            const match = quantityText.textContent.match(/Miqdor:\s*(\d+)/);
            if (match) {
                totalCount += parseInt(match[1]);
            }
        }
    });
    
    // Agar savatcha sahifasida emas bo'lsak, server tomonidan yuklash
    if (cartItems.length === 0 && !window.location.pathname.includes('/cart')) {
        fetch('/cart')
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const serverCartItems = doc.querySelectorAll('.cart-item');
                let serverTotalCount = 0;
                
                serverCartItems.forEach(item => {
                    const quantityText = item.querySelector('.item-info p');
                    if (quantityText) {
                        const match = quantityText.textContent.match(/Miqdor:\s*(\d+)/);
                        if (match) {
                            serverTotalCount += parseInt(match[1]);
                        }
                    }
                });
                
                // Cart count elementini yangilash
                const cartCountElement = document.getElementById('cart-count');
                if (cartCountElement) {
                    cartCountElement.textContent = serverTotalCount;
                }
            })
            .catch(error => {
                console.log('Cart count yuklashda xatolik:', error);
            });
        return;
    }
    
    // Cart count elementini yangilash
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = totalCount;
    }
}

// Sahifa yuklanganda ishga tushirish
document.addEventListener('DOMContentLoaded', function() {
    // Boshlang'ich hisobni yangilash
    updateCartCount();
});

// Savatcha qo'shish formalarini yuborishdan keyin count ni yangilash
document.addEventListener('submit', function(e) {
    if (e.target.action && e.target.action.includes('add_to_cart')) {
        // Form yuborilgandan keyin bir oz kutib count ni yangilash
        setTimeout(updateCartCount, 500);
    }
});

// Savatchadan olib tashlash tugmasi bosilganda ham yangilash
document.addEventListener('click', function(e) {
    if (e.target.textContent && e.target.textContent.includes('Olib tashlash')) {
        setTimeout(updateCartCount, 500);
    }
});

