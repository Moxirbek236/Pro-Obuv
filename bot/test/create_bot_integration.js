const fs = require('fs');

// Function to create bot-ready products from seller API data
function createBotProductsFromSellerData() {
    console.log('Seller API ma\'lumotlaridan bot mahsulotlarini yaratish...');
    
    // Read existing seller products
    const existingData = JSON.parse(fs.readFileSync('uzum_products_88415_1770478620771.json', 'utf8'));
    const sellerProducts = existingData.products || [];
    
    console.log(`${sellerProducts.length} ta mahsulot topildi.`);
    
    const botProducts = sellerProducts.map((product, index) => {
        // Extract SKU information
        const skus = product.skus || [];
        const activeSkus = skus.filter(sku => sku.quantityActive > 0);
        
        // Get price range
        const prices = skus.map(sku => sku.price).filter(price => price > 0);
        const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
        const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;
        
        // Create bot product
        const botProduct = {
            id: product.productId || index + 1,
            title: product.title,
            description: product.description || `${product.title} - Sifatli va qulay poyabzal`,
            price: minPrice,
            priceRange: minPrice !== maxPrice ? `${minPrice} - ${maxPrice} so'm` : `${minPrice} so'm`,
            image: product.image || product.previewImage,
            previewImage: product.previewImg,
            category: 'Poyabzal',
            brand: product.skuTitle || product.brand || 'Noma\'lum',
            availability: activeSkus.length > 0 ? '✅ Mavjud' : '❌ Mavjud emas',
            totalQuantity: product.quantityActive || 0,
            soldQuantity: product.quantitySold || 0,
            characteristics: [],
            sizes: [],
            colors: [],
            uzumMarketUrl: `https://uzum.uz/uz/search?query=${encodeURIComponent(product.title.split(' ').slice(0, 3).join(' '))}`,
            sellerData: product,
            createdAt: new Date().toISOString()
        };
        
        // Extract characteristics from SKUs
        const characteristicsSet = new Set();
        const sizesSet = new Set();
        const colorsSet = new Set();
        
        skus.forEach(sku => {
            if (sku.characteristics) {
                characteristicsSet.add(sku.characteristics);
            }
            
            // Extract size from characteristics
            if (sku.characteristicsList) {
                sku.characteristicsList.forEach(char => {
                    if (char.characteristicTitle && char.characteristicTitle.uz) {
                        const title = char.characteristicTitle.uz.toLowerCase();
                        const value = char.characteristicValue ? char.characteristicValue.uz : '';
                        
                        if (title.includes('olcham') || title.includes('размер')) {
                            sizesSet.add(value);
                        } else if (title.includes('rang') || title.includes('цвет')) {
                            colorsSet.add(value);
                        } else {
                            characteristicsSet.add(`${title}: ${value}`);
                        }
                    }
                });
            }
        });
        
        botProduct.characteristics = Array.from(characteristicsSet);
        botProduct.sizes = Array.from(sizesSet).sort((a, b) => {
            // Sort sizes numerically
            const numA = parseInt(a);
            const numB = parseInt(b);
            if (!isNaN(numA) && !isNaN(numB)) {
                return numA - numB;
            }
            return a.localeCompare(b);
        });
        botProduct.colors = Array.from(colorsSet);
        
        return botProduct;
    });
    
    // Save bot products
    const output = {
        timestamp: new Date().toISOString(),
        totalProducts: botProducts.length,
        shopId: existingData.shopId,
        products: botProducts,
        summary: {
            totalProducts: botProducts.length,
            availableProducts: botProducts.filter(p => p.availability.includes('✅')).length,
            totalQuantity: botProducts.reduce((sum, p) => sum + p.totalQuantity, 0),
            totalSold: botProducts.reduce((sum, p) => sum + p.soldQuantity, 0),
            brands: [...new Set(botProducts.map(p => p.brand))],
            priceRange: {
                min: Math.min(...botProducts.map(p => p.price).filter(p => p > 0)),
                max: Math.max(...botProducts.map(p => p.price).filter(p => p > 0))
            }
        }
    };
    
    const fileName = `bot_ready_products_${new Date().getTime()}.json`;
    fs.writeFileSync(fileName, JSON.stringify(output, null, 2), 'utf8');
    
    console.log(`\n✅ Bot uchun mahsulotlar tayyor: ${fileName}`);
    console.log(`📊 Jami mahsulotlar: ${output.summary.totalProducts}`);
    console.log(`🟢 Mavjud mahsulotlar: ${output.summary.availableProducts}`);
    console.log(`📦 Jami soni: ${output.summary.totalQuantity} dona`);
    console.log(`💰 Narxlar oralig'i: ${output.summary.priceRange.min} - ${output.summary.priceRange.max} so'm`);
    console.log(`🏷️ Brendlar: ${output.summary.brands.join(', ')}`);
    
    return output;
}

// Create a simple bot command handler
function createBotCommandHandler() {
    const botData = createBotProductsFromSellerData();
    
    // Create bot command functions
    const botCommands = {
        products: (limit = 10) => {
            const available = botData.products.filter(p => p.availability.includes('✅'));
            const limited = available.slice(0, limit);
            
            return limited.map(product => {
                return `🛍️ *${product.title}*\n` +
                       `💰 ${product.priceRange}\n` +
                       `📊 Mavjud: ${product.totalQuantity} dona\n` +
                       `🏷️ Brend: ${product.brand}\n` +
                       `🔗 [Uzum da ko'rish](${product.uzumMarketUrl})\n` +
                       `📋 Xususiyatlar: ${product.characteristics.slice(0, 2).join(', ')}\n`;
            }).join('\n---\n\n');
        },
        
        product: (productId) => {
            const product = botData.products.find(p => p.id == productId);
            if (!product) {
                return '❌ Mahsulot topilmadi';
            }
            
            return `🛍️ *${product.title}*\n\n` +
                   `📝 *Tavsif:* ${product.description}\n\n` +
                   `💰 *Narx:* ${product.priceRange}\n` +
                   `📊 *Mavjud:* ${product.availability} (${product.totalQuantity} dona)\n` +
                   `🏷️ *Brend:* ${product.brand}\n` +
                   `📦 *Sotilgan:* ${product.soldQuantity} dona\n\n` +
                   `📏 *O\'lchamlar:* ${product.sizes.join(', ') || 'Noma\'lum'}\n` +
                   `🎨 *Ranglar:* ${product.colors.join(', ') || 'Noma\'lum'}\n\n` +
                   `🔗 [Uzum da ko'rish](${product.uzumMarketUrl})`;
        },
        
        search: (query) => {
            const results = botData.products.filter(p => 
                p.title.toLowerCase().includes(query.toLowerCase()) ||
                p.brand.toLowerCase().includes(query.toLowerCase()) ||
                p.characteristics.some(c => c.toLowerCase().includes(query.toLowerCase()))
            );
            
            if (results.length === 0) {
                return `❌ "${query}" bo'yicha mahsulot topilmadi`;
            }
            
            return results.slice(0, 5).map(product => {
                return `🛍️ *${product.title}*\n` +
                       `💰 ${product.priceRange}\n` +
                       `📊 Mavjud: ${product.availability}\n` +
                       `🔗 [Ko'rish](${product.uzumMarketUrl})`;
            }).join('\n\n---\n\n');
        },
        
        categories: () => {
            const brands = [...new Set(botData.products.map(p => p.brand))];
            const priceRanges = {
                '100K gacha': botData.products.filter(p => p.price <= 100000).length,
                '100K-200K': botData.products.filter(p => p.price > 100000 && p.price <= 200000).length,
                '200K-300K': botData.products.filter(p => p.price > 200000 && p.price <= 300000).length,
                '300K+': botData.products.filter(p => p.price > 300000).length
            };
            
            return `📊 *Katalog statistikasi*\n\n` +
                   `🛍️ Jami mahsulotlar: ${botData.summary.totalProducts}\n` +
                   `🟢 Mavjud mahsulotlar: ${botData.summary.availableProducts}\n\n` +
                   `🏷️ *Brendlar:*\n${brands.map(b => `• ${b}`).join('\n')}\n\n` +
                   `💰 *Narx oralig\'i:*\n${Object.entries(priceRanges).map(([range, count]) => `• ${range}: ${count} ta`).join('\n')}`;
        }
    };
    
    // Save bot commands
    const botCode = `
// Bot commands for Uzum products
const botProducts = ${JSON.stringify(botData, null, 2)};

// Command handlers
async function handleProductsCommand(ctx) {
    const products = botProducts.products.filter(p => p.availability.includes('✅')).slice(0, 10);
    const message = products.map(product => 
        \`🛍️ *\${product.title}*\n\` +
        \`💰 \${product.priceRange}\n\` +
        \`📊 Mavjud: \${product.totalQuantity} dona\n\` +
        \`🏷️ Brend: \${product.brand}\n\` +
        \`🔗 [Uzum da ko'rish](\${product.uzumMarketUrl})\`
    ).join('\\n---\\n\\n');
    
    await ctx.replyWithMarkdown(message);
}

async function handleProductCommand(ctx, productId) {
    const product = botProducts.products.find(p => p.id == productId);
    if (!product) {
        await ctx.reply('❌ Mahsulot topilmadi');
        return;
    }
    
    const message = \`🛍️ *\${product.title}*\n\n\` +
                   \`📝 *Tavsif:* \${product.description}\n\n\` +
                   \`💰 *Narx:* \${product.priceRange}\n\` +
                   \`📊 *Mavjud:* \${product.availability} (\${product.totalQuantity} dona)\n\` +
                   \`🏷️ *Brend:* \${product.brand}\n\` +
                   \`📦 *Sotilgan:* \${product.soldQuantity} dona\n\n\` +
                   \`📏 *O'lchamlar:* \${product.sizes.join(', ') || 'Noma\'lum'}\n\` +
                   \`🎨 *Ranglar:* \${product.colors.join(', ') || 'Noma\'lum'}\n\n\` +
                   \`🔗 [Uzum da ko'rish](\${product.uzumMarketUrl})\`;
    
    await ctx.replyWithMarkdown(message);
}

async function handleSearchCommand(ctx, query) {
    const results = botProducts.products.filter(p => 
        p.title.toLowerCase().includes(query.toLowerCase()) ||
        p.brand.toLowerCase().includes(query.toLowerCase())
    );
    
    if (results.length === 0) {
        await ctx.reply(\`❌ "\${query}" bo'yicha mahsulot topilmadi\`);
        return;
    }
    
    const message = results.slice(0, 5).map(product => 
        \`🛍️ *\${product.title}*\n\` +
        \`💰 \${product.priceRange}\n\` +
        \`📊 Mavjud: \${product.availability}\n\` +
        \`🔗 [Ko'rish](\${product.uzumMarketUrl})\`
    ).join('\\n\\n---\\n\\n');
    
    await ctx.replyWithMarkdown(message);
}
`;
    
    fs.writeFileSync('bot_commands.js', botCode);
    console.log('\n✅ Bot komandalari yaratildi: bot_commands.js');
    
    return { botData, botCommands };
}

// Run the function
createBotCommandHandler();
