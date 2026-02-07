const fs = require('fs');
const https = require('https');

// API settings
const API_TOKEN = "K5jmUckABrq9L6sS9iAvMtUgrspCbvJZpK3rUnDFauA=";
// Test different shop IDs
const SHOP_IDS = ["88415", "88414", "88413", "88416", "88417"];
const BASE_URL = "api-seller.uzum.uz";

// Function to make API request
function makeRequest(page, shopId) {
    return new Promise((resolve, reject) => {
        const url = `https://${BASE_URL}/api/seller-openapi/v1/product/shop/${shopId}?sortBy=DEFAULT&order=ASC&size=1&page=${page}&filter=ALL`;
        
        const options = {
            headers: {
                'Authorization': API_TOKEN,
                'Accept': '*/*',
                'Content-Type': 'application/json'
            }
        };

        console.log(`So'rov yuborilmoqda: ${url}`);
        console.log(`Authorization: ${API_TOKEN.substring(0, 20)}...`);

        const req = https.request(url, options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                console.log(`HTTP Status: ${res.statusCode}`);
                try {
                    const jsonData = JSON.parse(data);
                    resolve(jsonData);
                } catch (error) {
                    console.log('Raw response:', data);
                    reject(error);
                }
            });
        }).on('error', (error) => {
            reject(error);
        });
        
        req.end();
    });
}

// Main function to fetch all products
async function fetchAllProducts() {
    console.log('Barcha mahsulotlarni yuklash boshlandi...');
    
    for (let shopIndex = 0; shopIndex < SHOP_IDS.length; shopIndex++) {
        const shopId = SHOP_IDS[shopIndex];
        console.log(`\n=== Shop ID: ${shopId} ni tekshirish ===`);
        
        let allProducts = [];
        let page = 1;
        let hasMore = true;
        
        while (hasMore) {
            try {
                console.log(`${page}-sahifa yuklanmoqda...`);
                
                const response = await makeRequest(page, shopId);
                
                console.log('API javobi:', JSON.stringify(response, null, 2));
                
                if (response && response.productList) {
                    const products = response.productList;
                    
                    if (products.length === 0) {
                        hasMore = false;
                        console.log('Barcha mahsulotlar yuklandi.');
                    } else {
                        allProducts = allProducts.concat(products);
                        console.log(`${products.length} ta mahsulot qo'shildi. Jami: ${allProducts.length}`);
                        
                        // Check if there are more products
                        const totalProducts = response.totalProductsAmount || 0;
                        if (allProducts.length >= totalProducts) {
                            hasMore = false;
                            console.log('Barcha mahsulotlar yuklandi.');
                        }
                    }
                    
                    page++;
                } else {
                    hasMore = false;
                    console.log('Mahsulotlar topilmadi yoki API javobi noto\'g\'ri.');
                    console.log('Javob tuzilmasi:', JSON.stringify(response, null, 2));
                }
                
                // Small delay to avoid rate limiting
                await new Promise(resolve => setTimeout(resolve, 100));
                
            } catch (error) {
                console.error(`Xatolik yuz berdi (sahifa ${page}):`, error.message);
                hasMore = false;
            }
        }
        
        // If we found products, save and exit
        if (allProducts.length > 0) {
            console.log(`\n✅ Shop ${shopId} da mahsulotlar topildi!`);
            
            // Save to JSON file
            const output = {
                timestamp: new Date().toISOString(),
                totalProducts: allProducts.length,
                shopId: shopId,
                products: allProducts
            };
            
            const fileName = `uzum_products_${shopId}_${new Date().getTime()}.json`;
            
            fs.writeFileSync(fileName, JSON.stringify(output, null, 2), 'utf8');
            
            console.log(`\n✅ Barcha mahsulotlar muvaffaqiyatli saqlandi!`);
            console.log(`📁 Fayl nomi: ${fileName}`);
            console.log(`📊 Jami mahsulotlar soni: ${allProducts.length}`);
            
            return output;
        } else {
            console.log(`Shop ${shopId} da mahsulotlar topilmadi.`);
        }
    }
    
    console.log('\n❌ Hech qanday shop da mahsulotlar topilmadi.');
    return null;
}

// Run the function
fetchAllProducts().catch(console.error);
