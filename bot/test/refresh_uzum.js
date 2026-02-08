const fs = require('fs');

// Function to refresh Uzum products from market API
async function refreshUzumProducts() {
    console.log('🔄 Uzum market dan mahsulotlarni yangilash...');
    
    try {
        // Fetch products from seller API
        const response = await fetch('https://api-seller.uzum.uz/api/seller-openapi/v1/product/shop/88415?filter=ALL&size=1', {
            method: 'GET',
            headers: {
                'Authorization': 'K5jmUckABrq9L6sS9iAvMtUgrspCbvJZpK3rUnDFauA=',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`📊 API dan ${data.totalProductsAmount || 0} ta mahsulot topildi`);
        
        // Process each SKU as separate product with color/size variants
        const allProducts = [];
        
        if (data.productList && data.productList.length > 0) {
            for (const product of data.productList) {
                if (product.skuList && product.skuList.length > 0) {
                    // Group SKUs by characteristics
                    const skuGroups = {};
                    
                    for (const sku of product.skuList) {
                        const characteristics = {};
                        
                        if (sku.characteristicsList) {
                            for (const char of sku.characteristicsList) {
                                const title = char.characteristicTitle?.uz || char.characteristicTitle?.ru || '';
                                const value = char.characteristicValue?.uz || char.characteristicValue?.ru || '';
                                
                                if (title && value) {
                                    characteristics[title] = value;
                                }
                            }
                        }
                        
                        // Create group key based on characteristics
                        const color = characteristics['Rang'] || characteristics['Цвет'] || 'Standart';
                        const size = characteristics['O\'lcham'] || characteristics['Размер'] || 'Standart';
                        const groupKey = `${color}_${size}`;
                        
                        if (!skuGroups[groupKey]) {
                            skuGroups[groupKey] = {
                                baseProduct: product,
                                skus: [],
                                characteristics: characteristics,
                                color: color,
                                size: size
                            };
                        }
                        
                        skuGroups[groupKey].skus.push(sku);
                    }
                    
                    // Create separate products for each group
                    for (const [groupKey, group] of Object.entries(skuGroups)) {
                        const totalQuantity = group.skus.reduce((sum, sku) => sum + (sku.quantityActive || 0), 0);
                        const totalSold = group.skus.reduce((sum, sku) => sum + (sku.quantitySold || 0), 0);
                        
                        // Get price range
                        const prices = group.skus.map(sku => sku.price || 0).filter(p => p > 0);
                        const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
                        const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;
                        
                        const newProduct = {
                            id: product.productId,
                            title: `${product.title} - ${group.color}`,
                            description: `${product.title} - ${group.color} rangli, ${group.size} o\'lchamli`,
                            price: minPrice,
                            priceRange: minPrice !== maxPrice ? `${minPrice} - ${maxPrice} so'm` : `${minPrice} so'm`,
                            image: product.image || product.previewImage,
                            previewImage: product.previewImage,
                            category: product.category,
                            brand: group.color, // Use color as brand variant
                            availability: totalQuantity > 0 ? '✅ Mavjud' : '❌ Mavjud emas',
                            totalQuantity: totalQuantity,
                            soldQuantity: totalSold,
                            characteristics: Object.entries(group.characteristics).map(([k, v]) => `${k}: ${v}`),
                            sizes: [group.size],
                            colors: [group.color],
                            uzumMarketUrl: `https://uzum.uz/product/${product.productId}`,
                            sellerData: product,
                            variantInfo: {
                                color: group.color,
                                size: group.size,
                                skuCount: group.skus.length,
                                availableSkus: group.skus.filter(sku => sku.quantityActive > 0).length
                            },
                            createdAt: new Date().toISOString()
                        };
                        
                        allProducts.push(newProduct);
                    }
                }
            }
        }
        
        // Save updated products
        const output = {
            timestamp: new Date().toISOString(),
            totalProducts: allProducts.length,
            shopId: "88415",
            products: allProducts,
            summary: {
                totalProducts: allProducts.length,
                availableProducts: allProducts.filter(p => p.availability.includes('✅')).length,
                totalQuantity: allProducts.reduce((sum, p) => sum + p.totalQuantity, 0),
                totalSold: allProducts.reduce((sum, p) => sum + p.soldQuantity, 0),
                colors: [...new Set(allProducts.flatMap(p => p.colors))],
                sizes: [...new Set(allProducts.flatMap(p => p.sizes))],
                priceRange: {
                    min: Math.min(...allProducts.map(p => p.price).filter(p => p > 0)),
                    max: Math.max(...allProducts.map(p => p.price).filter(p => p > 0))
                }
            }
        };
        
        const fileName = `uzum_products_variants_${new Date().getTime()}.json`;
        fs.writeFileSync(fileName, JSON.stringify(output, null, 2), 'utf8');
        
        console.log(`✅ Mahsulotlar yangilandi: ${fileName}`);
        console.log(`📊 Jami mahsulotlar: ${output.summary.totalProducts}`);
        console.log(`🟢 Mavjud mahsulotlar: ${output.summary.availableProducts}`);
        console.log(`📦 Jami soni: ${output.summary.totalQuantity} dona`);
        console.log(`🎨 Ranglar: ${output.summary.colors.join(', ')}`);
        console.log(`📏 O\'lchamlar: ${output.summary.sizes.join(', ')}`);
        
        // Show examples
        console.log('\n--- Misol mahsulotlar ---');
        allProducts.slice(0, 3).forEach((product, i) => {
            console.log(`${i+1}. ${product.title}`);
            console.log(`   Rang: ${product.colors.join(', ')}`);
            console.log(`   O\'lcham: ${product.sizes.join(', ')}`);
            console.log(`   Narx: ${product.priceRange}`);
            console.log(`   Mavjud: ${product.totalQuantity} dona`);
            console.log('');
        });
        
        return output;
        
    } catch (error) {
        console.error('❌ Xatolik yuz berdi:', error);
        return null;
    }
}

// Auto-refresh function
async function autoRefresh() {
    console.log('🔄 Avto-refresh rejimi boshlandi...');
    
    while (true) {
        try {
            console.log('⏰ Yangilash boshlandi...');
            const result = await refreshUzumProducts();
            
            if (result) {
                console.log(`✅ Yangilandi: ${result.summary.totalProducts} mahsulot, ${result.summary.availableProducts} ta mavjud`);
            }
            
            // Wait 5 minutes before next refresh
            console.log('⏳ 5 daqiqadan keyin yangilanadi...');
            await new Promise(resolve => setTimeout(resolve, 5 * 60 * 1000));
            
        } catch (error) {
            console.error('❌ Xatolik:', error);
            // Wait 1 minute before retry
            console.log('⏳ 1 daqiqadan keyin qayta uriniladi...');
            await new Promise(resolve => setTimeout(resolve, 60 * 1000));
        }
    }
}

// Run based on command line arguments
const command = process.argv[2];

if (command === 'refresh') {
    refreshUzumProducts();
} else if (command === 'auto') {
    autoRefresh();
} else {
    console.log('📋 Foydalanish:');
    console.log('  node refresh_uzum.js refresh  - Mahsulotlarni bir marta yangilash');
    console.log('  node refresh_uzum.js auto     - Avto-refresh rejimi (har 5 daqiqada)');
}
