const fs = require('fs');
const https = require('https');

// Function to make request with proper headers
function makeRequest(url) {
    return new Promise((resolve, reject) => {
        const options = {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'uz-UZ,uz;q=0.9,en;q=0.8',
                'Referer': 'https://uzum.uz/',
                'X-Requested-With': 'XMLHttpRequest'
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
                    resolve({rawData: data, status: res.statusCode});
                }
            });
        }).on('error', (error) => {
            reject(error);
        });
        
        req.end();
    });
}

// Test different API endpoints
async function testUzumAPIs() {
    console.log('Uzum API endpointlarini test qilish...');
    
    const testQueries = [
        'krossovka',
        'etik',
        'poyabzal',
        'skechers'
    ];
    
    const endpoints = [
        'https://uzum.uz/api/v1/search',
        'https://uzum.uz/api/search',
        'https://uzum.uz/api/v2/search',
        'https://uzum.uz/api/products/search',
        'https://uzum.uz/uz/api/v1/search'
    ];
    
    for (const endpoint of endpoints) {
        console.log(`\n=== Test: ${endpoint} ===`);
        
        for (const query of testQueries) {
            try {
                const url = `${endpoint}?query=${encodeURIComponent(query)}&limit=5`;
                console.log(`So'rov: ${url}`);
                
                const response = await makeRequest(url);
                
                if (response.payload || response.items || response.products) {
                    console.log(`✅ Ishlaydi! Javob:`, {
                        hasPayload: !!response.payload,
                        hasItems: !!response.items,
                        hasProducts: !!response.products,
                        itemCount: response.payload?.items?.length || response.items?.length || response.products?.length || 0
                    });
                    
                    // Save working endpoint
                    fs.writeFileSync('working_uzum_api.json', JSON.stringify({
                        endpoint: endpoint,
                        query: query,
                        response: response,
                        timestamp: new Date().toISOString()
                    }, null, 2));
                    
                    return endpoint;
                } else {
                    console.log(`❌ Ishlamaydi. Status: ${response.status || 'unknown'}`);
                }
            } catch (error) {
                console.log(`❌ Xatolik: ${error.message}`);
            }
        }
    }
    
    console.log('\n❌ Hech qanday ishlaydigan endpoint topilmadi.');
    return null;
}

// Test specific product page
async function testProductPage() {
    console.log('\n=== Mahsulot sahifasini test qilish ===');
    
    const productUrl = 'https://uzum.uz/uz/product/erkaklar-uchun-qulay-skechers-sport-poyabzal-qora---1-2326112?skuId=8335884';
    
    try {
        // Try to get product data
        const apiUrl = `https://uzum.uz/api/v1/products/2326112?skuId=8335884`;
        console.log(`API so'rovi: ${apiUrl}`);
        
        const response = await makeRequest(apiUrl);
        
        console.log('Mahsulot javobi:', JSON.stringify(response, null, 2));
        
        fs.writeFileSync('product_test.json', JSON.stringify({
            url: apiUrl,
            response: response,
            timestamp: new Date().toISOString()
        }, null, 2));
        
    } catch (error) {
        console.error(`Mahsulot testida xatolik: ${error.message}`);
    }
}

// Run tests
async function runTests() {
    await testUzumAPIs();
    await testProductPage();
}

runTests().catch(console.error);
