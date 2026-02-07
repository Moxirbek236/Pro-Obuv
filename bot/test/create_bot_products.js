const fs = require('fs');
const https = require('https');

// Function to get HTML content
function getHTML(url) {
    return new Promise((resolve, reject) => {
        const options = {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'uz-UZ,uz;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        };

        const req = https.get(url, options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                resolve(data);
            });
        }).on('error', (error) => {
            reject(error);
        });
        
        req.end();
    });
}

// Function to extract product data from HTML
function extractProductData(html, productTitle) {
    const products = [];
    
    // Try to find JSON data in script tags
    const scriptRegex = /window\.__INITIAL_STATE__\s*=\s*({.*?});/g;
    const matches = scriptRegex.exec(html);
    
    if (matches && matches[1]) {
        try {
            const initialState = JSON.parse(matches[1]);
            
            // Look for product data in different possible locations
            if (initialState.products) {
                products.push(...initialState.products);
            }
            if (initialState.product) {
                products.push(initialState.product);
            }
            if (initialState.search && initialState.search.products) {
                products.push(...initialState.search.products);
            }
        } catch (error) {
            console.log('JSON parse error:', error.message);
        }
    }
    
    // Try other patterns
    const jsonRegex = /"products":\s*\[({.*?})\]/g;
    const productMatches = jsonRegex.exec(html);
    
    if (productMatches) {
        try {
            const productData = JSON.parse(`{"products": [${productMatches[1]}]}`);
            products.push(...productData.products);
        } catch (error) {
            console.log('Product JSON parse error:', error.message);
        }
    }
    
    return products;
}

// Function to search products and extract data
async function searchAndExtractProducts(query) {
    console.log(`Qidiruv: ${query}`);
    
    try {
        // Search page
        const searchUrl = `https://uzum.uz/uz/search?query=${encodeURIComponent(query)}`;
        console.log(`So'rov: ${searchUrl}`);
        
        const html = await getHTML(searchUrl);
        
        // Extract product data
        const products = extractProductData(html, query);
        
        console.log(`${products.length} ta mahsulot topildi.`);
        
        return products;
    } catch (error) {
        console.error(`Qidiruvda xatolik: ${error.message}`);
        return [];
    }
}

// Function to get product details
async function getProductDetails(productId, skuId) {
    try {
        const productUrl = `https://uzum.uz/uz/product/${productId}?skuId=${skuId}`;
        console.log(`Mahsulot ma'lumotlari: ${productUrl}`);
        
        const html = await getHTML(productUrl);
        
        // Extract product details
        const products = extractProductData(html, '');
        
        if (products.length > 0) {
            return products[0];
        }
        
        return null;
    } catch (error) {
        console.error(`Mahsulot ma'lumotlarini olishda xatolik: ${error.message}`);
        return null;
    }
}

// Main function to create bot-ready product data
async function createBotProductData() {
    console.log('Bot uchun mahsulot ma\'lumotlarini yaratish...');
    
    // Read existing seller products
    const existingData = JSON.parse(fs.readFileSync('uzum_products_88415_1770478620771.json', 'utf8'));
    const sellerProducts = existingData.products || [];
    
    console.log(`${sellerProducts.length} ta mahsulot topildi.`);
    
    const botProducts = [];
    
    for (let i = 0; i < Math.min(5, sellerProducts.length); i++) { // Test with first 5 products
        const product = sellerProducts[i];
        
        console.log(`\n${i + 1}/5: ${product.title}`);
        
        // Extract keywords from title
        const keywords = product.title.toLowerCase().split(' ').slice(0, 3).join(' ');
        
        // Search on Uzum market
        const searchResults = await searchAndExtractProducts(keywords);
        
        let uzumProduct = null;
        let productUrl = null;
        
        if (searchResults.length > 0) {
            // Find best match
            uzumProduct = searchResults.find(p => 
                p.title && p.title.toLowerCase().includes(keywords)
            ) || searchResults[0];
            
            // Generate URL
            if (uzumProduct.slug || uzumProduct.id) {
                productUrl = `https://uzum.uz/uz/product/${uzumProduct.slug || uzumProduct.id}`;
                if (uzumProduct.skuId) {
                    productUrl += `?skuId=${uzumProduct.skuId}`;
                }
            }
        }
        
        // Create bot-ready product
        const botProduct = {
            id: product.productId || product.skuId,
            title: product.title,
            description: product.description || '',
            price: product.price,
            image: product.image || product.previewImage,
            category: product.category || 'Poyabzal',
            availability: product.quantityActive > 0 ? '✅ Mavjud' : '❌ Mavjud emas',
            characteristics: product.characteristics || '',
            uzumMarketUrl: productUrl,
            uzumMarketData: uzumProduct,
            sellerData: product,
            createdAt: new Date().toISOString()
        };
        
        botProducts.push(botProduct);
        
        console.log(`✅ Qo'shildi: ${botProduct.title}`);
        
        // Delay
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Save bot products
    const output = {
        timestamp: new Date().toISOString(),
        totalProducts: botProducts.length,
        shopId: existingData.shopId,
        products: botProducts
    };
    
    const fileName = `bot_products_${new Date().getTime()}.json`;
    fs.writeFileSync(fileName, JSON.stringify(output, null, 2), 'utf8');
    
    console.log(`\n✅ Bot mahsulotlari saqlandi: ${fileName}`);
    console.log(`📊 Jami mahsulotlar: ${botProducts.length}`);
    console.log(`🔗 Uzum marketda topilgan: ${botProducts.filter(p => p.uzumMarketUrl).length}`);
    
    return output;
}

// Run the function
createBotProductData().catch(console.error);
