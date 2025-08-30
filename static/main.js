// Savatcha sonini yangilash funksiyasi - API orqali
function updateCartCount() {
    fetch('/get_cart_count')
        .then(response => response.json())
        .then(data => {
            const cartCountElement = document.getElementById('cart-count');
            if (cartCountElement) {
                cartCountElement.textContent = data.count;
            }
        })
        .catch(error => {
            console.log('Cart count yuklashda xatolik:', error);
        });
}

// Sahifa yuklanganda ishga tushirish
document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();
});

// Savatcha qo'shish formalarini yuborishdan keyin count ni yangilash
document.addEventListener('submit', function(e) {
    if (e.target.action && e.target.action.includes('add_to_cart')) {
        setTimeout(updateCartCount, 100);
    }
});

// Savatchadan olib tashlash tugmasi bosilganda ham yangilash
document.addEventListener('click', function(e) {
    if (e.target.textContent && e.target.textContent.includes('O\'chirish')) {
        setTimeout(updateCartCount, 100);
    }
});