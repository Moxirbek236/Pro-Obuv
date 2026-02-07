const fs = require('fs');
const https = require('https');

// Uzum market public API settings
const BASE_URL = "uzum.uz";

// Function to make request to Uzum market
function makeUzumRequest(url) {
    return new Promise((resolve, reject) => {
        const options = {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'uz-UZ,uz;q=0.9,en;q=0.8',
                'Referer': 'https://uzum.uz/'
            }
        };

        const req = https.get(url, options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(data);
                    resolve(jsonData);
                } catch (error) {
                    // If not JSON, return raw data
                    resolve({rawData: data});
                }
            });
        }).on('error', (error) => {
            reject(error);
        });
        
        req.end();
    });
}

// Function to get product details from Uzum market
async function getUzumProductDetails(productId, skuId) {
    try {
        const url = `https://uzum.uz/api/v1/products/${productId}?skuId=${skuId}`;
        console.log(`Mahsulot ma'lumotlari yuklanmoqda: ${productId} (sku: ${skuId})`);
        
        const response = await makeUzumRequest(url);
        return response;
    } catch (error) {
        console.error(`Mahsulot ma'lumotlarini olishda xatolik: ${error.message}`);
        return null;
    }
}

// Function to search products on Uzum market
async function searchUzumProducts(query, limit = 20) {
    try {
        const url = `https://uzum.uz/api/v1/search?query=${encodeURIComponent(query)}&limit=${limit}`;
        console.log(`Qidiruv: ${query}`);
        
        const response = await makeUzumRequest(url);
        return response;
    } catch (error) {
        console.error(`Qidiruvda xatolik: ${error.message}`);
        return null;
    }
}

// Main function to get products from existing data and enrich with Uzum market data
async function enrichProductsWithUzumData() {
    console.log('Uzum market ma\'lumotlari bilan boyitish boshlandi...');
    
    // Read existing products from seller API
    const existingData = JSON.parse(fs.readFileSync('uzum_products_88415_1770478620771.json', 'utf8'));
    const sellerProducts = existingData.products || [];
    
    console.log(`${sellerProducts.length} ta mahsulot topildi.`);
    
    const enrichedProducts = [];
    
    for (let i = 0; i < sellerProducts.length; i++) {
        const product = sellerProducts[i];
        
        console.log(`\n${i + 1}/${sellerProducts.length}: ${product.title}`);
        
        // Try to find product on Uzum market
        const searchResult = await searchUzumProducts(product.title, 5);
        
        if (searchResult && searchResult.payload && searchResult.payload.items) {
            const foundProduct = searchResult.payload.items.find(item => 
                item.title && item.title.toLowerCase().includes(product.title.toLowerCase().split(' ').slice(0, 3).join(' '))
            );
            
            if (foundProduct) {
                console.log(`✅ Mahsulot topildi: ${foundProduct.title}`);
                
                // Get detailed product info
                const detailedProduct = await getUzumProductDetails(foundProduct.productId, foundProduct.skuId);
                
                // Merge seller data with Uzum market data
                const enrichedProduct = {
                    sellerData: product,
                    uzumMarketData: {
                        ...foundProduct,
                        details: detailedProduct
                    },
                    productUrl: `https://uzum.uz/uz/product/${foundProduct.slug || foundProduct.productId}?skuId=${foundProduct.skuId}`,
                    enrichedAt: new Date().toISOString()
                };
                
                enrichedProducts.push(enrichedProduct);
            } else {
                console.log(`❌ Mahsulot topilmadi: ${product.title}`);
                enrichedProducts.push({
                    sellerData: product,
                    uzumMarketData: null,
                    enrichedAt: new Date().toISOString()
                });
            }
        } else {
            enrichedProducts.push({
                sellerData: product,
                uzumMarketData: null,
                enrichedAt: new Date().toISOString()
            });
        }
        
        // Delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Save enriched data
    const output = {
        timestamp: new Date().toISOString(),
        totalProducts: enrichedProducts.length,
        shopId: existingData.shopId,
        products: enrichedProducts
    };
    
    const fileName = `uzum_products_enriched_${new Date().getTime()}.json`;
    fs.writeFileSync(fileName, JSON.stringify(output, null, 2), 'utf8');
    
    console.log(`\n✅ Boyitilgan ma'lumotlar saqlandi: ${fileName}`);
    console.log(`📊 Jami mahsulotlar: ${enrichedProducts.length}`);
    console.log(`🔗 Uzum marketda topilgan: ${enrichedProducts.filter(p => p.uzumMarketData).length}`);
    
    return output;
}

// Run the function
enrichProductsWithUzumData().catch(console.error);
