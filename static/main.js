
// Savatcha sonini yangilash funksiyasi
function updateCartCount() {
    // Sahifadagi barcha miqdor inputlarini olish
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    let totalCount = 0;
    
    // Har bir input qiymatini qo'shish
    quantityInputs.forEach(input => {
        const quantity = parseInt(input.value) || 0;
        totalCount += quantity;
    });
    
    // Cart count elementini yangilash
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = totalCount;
    }
}

// Sahifa yuklanganda ishga tushirish
document.addEventListener('DOMContentLoaded', function() {
    // Barcha miqdor inputlariga event listener qo'shish
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    quantityInputs.forEach(input => {
        input.addEventListener('input', updateCartCount);
        input.addEventListener('change', updateCartCount);
    });
    
    // Boshlang'ich hisobni yangilash
    updateCartCount();
});

// Savatcha qo'shish formalarini yuborishdan oldin count ni yangilash
document.addEventListener('submit', function(e) {
    if (e.target.action && e.target.action.includes('add_to_cart')) {
        // Form yuborilgandan keyin bir oz kutib count ni yangilash
        setTimeout(updateCartCount, 100);
    }
});
