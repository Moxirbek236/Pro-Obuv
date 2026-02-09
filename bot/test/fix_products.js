const fs = require('fs');

// Function to fix bot products data from original seller data
function fixBotProductsData() {
    console.log('Mahsulot ma\'lumotlarini tuzatish...');
    
    // Read the original Uzum products data
    const originalData = JSON.parse(fs.readFileSync('uzum_products_88415_1770628318163.json', 'utf8'));
    const sellerProducts = originalData.products || [];
    
    console.log(`${sellerProducts.length} ta mahsulot topildi.`);
    
    const fixedProducts = sellerProducts.map((product, index) => {
        // Calculate total quantity from SKU list
        const skuList = product.skuList || [];
        const totalQuantity = skuList.reduce((sum, sku) => sum + (sku.quantityActive || 0), 0);
        const totalSold = skuList.reduce((sum, sku) => sum + (sku.quantitySold || 0), 0);
        
        // Get price range from SKUs
        const prices = skuList.map(sku => sku.price || 0).filter(price => price > 0);
        const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
        const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;
        
        // Extract sizes and colors
        const sizes = [];
        const colors = [];
        const characteristics = [];
        
        skuList.forEach(sku => {
            if (sku.characteristicsList) {
                sku.characteristicsList.forEach(char => {
                    if (char.characteristicTitle && char.characteristicValue) {
                        const title = char.characteristicTitle.uz || char.characteristicTitle.ru || '';
                        const value = char.characteristicValue.uz || char.characteristicValue.ru || '';
                        
                        if (title.toLowerCase().includes('olcham') || title.toLowerCase().includes('размер')) {
                            if (!sizes.includes(value)) sizes.push(value);
                        } else if (title.toLowerCase().includes('rang') || title.toLowerCase().includes('цвет')) {
                            if (!colors.includes(value)) colors.push(value);
                        } else {
                            characteristics.push(`${title}: ${value}`);
                        }
                    }
                });
            }
        });
        
        // Create fixed product
        const fixedProduct = {
            id: product.productId || index + 1,
            title: product.title,
            description: product.description || `${product.title} - Sifatli va qulay poyabzal`,
            price: minPrice,
            priceRange: minPrice !== maxPrice ? `${minPrice} - ${maxPrice} so'm` : `${minPrice} so'm`,
            image: product.image || product.previewImage,
            previewImage: product.previewImg,
            category: product.category || 'Poyabzal',
            brand: product.skuTitle || product.brand || 'Noma\'lum',
            availability: totalQuantity > 0 ? '✅ Mavjud' : '❌ Mavjud emas',
            totalQuantity: totalQuantity,
            soldQuantity: totalSold,
            characteristics: characteristics,
            sizes: sizes.sort((a, b) => {
                // Sort sizes numerically
                const numA = parseInt(a);
                const numB = parseInt(b);
                if (!isNaN(numA) && !isNaN(numB)) {
                    return numA - numB;
                }
                return a.localeCompare(b);
            }),
            colors: colors,
            uzumMarketUrl: `https://uzum.uz/product/${product.productId}`,
            sellerData: product,
            createdAt: new Date().toISOString()
        };
        
        console.log(`✅ Mahsulot tuzatildi: ${fixedProduct.title} - ${fixedProduct.totalQuantity} dona`);
        
        return fixedProduct;
    });
    
    // Save fixed products
    const output = {
        timestamp: new Date().toISOString(),
        totalProducts: fixedProducts.length,
        shopId: originalData.shopId,
        products: fixedProducts,
        summary: {
            totalProducts: fixedProducts.length,
            availableProducts: fixedProducts.filter(p => p.availability.includes('✅')).length,
            totalQuantity: fixedProducts.reduce((sum, p) => sum + p.totalQuantity, 0),
            totalSold: fixedProducts.reduce((sum, p) => sum + p.soldQuantity, 0),
            brands: [...new Set(fixedProducts.map(p => p.brand))],
            priceRange: {
                min: Math.min(...fixedProducts.map(p => p.price).filter(p => p > 0)),
                max: Math.max(...fixedProducts.map(p => p.price).filter(p => p > 0))
            }
        }
    };
    
    const fileName = `bot_products_fixed_${new Date().getTime()}.json`;
    fs.writeFileSync(fileName, JSON.stringify(output, null, 2), 'utf8');
    
    console.log(`\n✅ Tuzatilgan mahsulotlar saqlandi: ${fileName}`);
    console.log(`📊 Jami mahsulotlar: ${output.summary.totalProducts}`);
    console.log(`🟢 Mavjud mahsulotlar: ${output.summary.availableProducts}`);
    console.log(`📦 Jami soni: ${output.summary.totalQuantity} dona`);
    console.log(`💰 Narxlar oralig'i: ${output.summary.priceRange.min} - ${output.summary.priceRange.max} so'm`);
    
    // Show first few products as example
    console.log('\n--- Misol mahsulotlar ---');
    fixedProducts.slice(0, 3).forEach((product, i) => {
        console.log(`${i+1}. ${product.title}`);
        console.log(`   Narx: ${product.priceRange}`);
        console.log(`   Mavjud: ${product.totalQuantity} dona`);
        console.log(`   O\'lchamlar: ${product.sizes.join(', ')}`);
        console.log(`   URL: ${product.uzumMarketUrl}`);
        console.log('');
    });
    
    return output;
}

// Run the function
fixBotProductsData();
