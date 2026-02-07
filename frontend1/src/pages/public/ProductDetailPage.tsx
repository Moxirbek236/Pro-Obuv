import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Star, Shield, Truck, RotateCcw, Minus, Plus, ShoppingCart, Heart, Share2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { formatCurrency } from '@/utils/formatters';
import { useCart } from '@/hooks/useCart';
import { useAuth } from '@/hooks/useAuth';
import ProductCard from '@/components/product/ProductCard';
import { Product } from '@/types/product.types';
import toast from 'react-hot-toast';

// Mock function to simulate API call
const fetchProduct = async (id: string) => {
    await new Promise(resolve => setTimeout(resolve, 600));
    return {
        id: Number(id),
        name: 'Jzzx Himoya Poyabzali S3', // Mock Product Name
        price: 450000,
        category: 'tufli',
        description: `Yuqori sifatli charm va po'lat burunli himoya poyabzali. 
    
    Xususiyatlari:
    - Suv o'tkazmaydigan tabiiy charm
    - 200J zarbaga chidamli po'lat burun
    - Sirpanishga qarshi (SRC) poliuretan taglik
    - Antistatik xususiyatlar
    - Yog' va kislotalarga chidamli
    - EN ISO 20345:2011 standarti
    
    Qulaylik:
    - Havo o'tkazuvchan ichki astar
    - Yumshoq ichki taglik
    - Yengil vazn dizayni`,
        image_url: 'https://placehold.co/600x600?text=Main+Image',
        available: true,
        stock_quantity: 50,
        rating: 4.5,
        discount_percentage: 10,
        sizes: '39,40,41,42,43,44,45',
        colors: 'black,brown',
        images: [
            'https://placehold.co/600x600?text=Image+1',
            'https://placehold.co/600x600?text=Image+2',
            'https://placehold.co/600x600?text=Image+3',
            'https://placehold.co/600x600?text=Image+4',
        ]
    };
};

const ProductDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [selectedSize, setSelectedSize] = useState<string>('');
    const [quantity, setQuantity] = useState(1);
    const [activeImage, setActiveImage] = useState(0);
    const { addToCart } = useCart();
    const { isAuthenticated } = useAuth();

    const { data: product, isLoading } = useQuery({
        queryKey: ['product', id],
        queryFn: () => fetchProduct(id!),
        enabled: !!id,
    });

    const handleAddToCart = () => {
        if (!product) return;
        if (!selectedSize) {
            toast.error('Iltimos, o\'lchamni tanlang');
            return;
        }

        addToCart(product.id, quantity);
    };

    if (isLoading) {
        return (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 animate-pulse">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div className="bg-gray-200 dark:bg-gray-700 h-96 rounded-lg"></div>
                    <div className="space-y-4">
                        <div className="bg-gray-200 dark:bg-gray-700 h-8 w-3/4 rounded"></div>
                        <div className="bg-gray-200 dark:bg-gray-700 h-4 w-1/4 rounded"></div>
                        <div className="bg-gray-200 dark:bg-gray-700 h-24 w-full rounded"></div>
                        <div className="bg-gray-200 dark:bg-gray-700 h-12 w-1/2 rounded"></div>
                    </div>
                </div>
            </div>
        );
    }

    if (!product) {
        return (
            <div className="text-center py-20">
                <h2 className="text-2xl font-bold">Mahsulot topilmadi</h2>
                <Link to="/menu" className="text-primary-600 hover:underline mt-4 inline-block">
                    Katalogga qaytish
                </Link>
            </div>
        );
    }

    const sizes = product.sizes?.split(',') || [];
    const discountedPrice = product.price * (1 - (product.discount_percentage || 0) / 100);

    return (
        <div className="bg-white dark:bg-gray-900 min-h-screen pb-12">
            {/* Breadcrumbs */}
            <div className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 py-4">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                        <Link to="/" className="hover:text-primary-600">Bosh sahifa</Link>
                        <span className="mx-2">/</span>
                        <Link to="/menu" className="hover:text-primary-600">Katalog</Link>
                        <span className="mx-2">/</span>
                        <span className="text-gray-900 dark:text-white font-medium">{product.name}</span>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    {/* Gallery */}
                    <div className="space-y-4">
                        <div className="aspect-square bg-gray-100 dark:bg-gray-800 rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-700 relative">
                            {product.discount_percentage && product.discount_percentage > 0 && (
                                <span className="absolute top-4 left-4 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold z-10">
                                    -{product.discount_percentage}% Cheers
                                </span>
                            )}
                            <img
                                src={product.images?.[activeImage] || product.image_url}
                                alt={product.name}
                                className="w-full h-full object-cover"
                            />
                        </div>
                        <div className="grid grid-cols-4 gap-4">
                            {product.images?.map((img: string, index: number) => (
                                <button
                                    key={index}
                                    onClick={() => setActiveImage(index)}
                                    className={`aspect-square rounded-lg overflow-hidden border-2 transition-colors ${activeImage === index ? 'border-primary-600' : 'border-transparent hover:border-gray-300'
                                        }`}
                                >
                                    <img src={img} alt={`${product.name} view ${index + 1}`} className="w-full h-full object-cover" />
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Product Details */}
                    <div>
                        <div className="mb-2 text-sm text-primary-600 font-medium uppercase tracking-wider">
                            {product.category}
                        </div>
                        <h1 className="text-3xl md:text-4xl font-heading font-bold text-gray-900 dark:text-white mb-4">
                            {product.name}
                        </h1>

                        {/* Rating */}
                        <div className="flex items-center mb-6">
                            <div className="flex text-yellow-400">
                                {[...Array(5)].map((_, i) => (
                                    <Star
                                        key={i}
                                        className={`w-5 h-5 ${i < Math.round(product.rating || 0) ? 'fill-current' : 'text-gray-300 dark:text-gray-600'}`}
                                    />
                                ))}
                            </div>
                            <span className="text-gray-500 ml-2 text-sm">({product.rating} reyting)</span>
                            <span className="mx-2 text-gray-300">|</span>
                            <span className="text-green-600 font-medium text-sm">Omborda mavjud</span>
                        </div>

                        {/* Price */}
                        <div className="mb-8">
                            {product.discount_percentage && product.discount_percentage > 0 ? (
                                <div className="flex items-end gap-3">
                                    <span className="text-4xl font-bold text-primary-600">
                                        {formatCurrency(discountedPrice)}
                                    </span>
                                    <span className="text-xl text-gray-400 line-through mb-1">
                                        {formatCurrency(product.price)}
                                    </span>
                                </div>
                            ) : (
                                <div className="text-4xl font-bold text-primary-600">
                                    {formatCurrency(product.price)}
                                </div>
                            )}
                        </div>

                        {/* Size Selector */}
                        <div className="mb-8">
                            <div className="flex justify-between items-center mb-3">
                                <label className="font-semibold text-gray-900 dark:text-white">
                                    O'lchamni tanlang:
                                </label>
                                <button className="text-primary-600 text-sm hover:underline">
                                    O'lchamlar jadvali
                                </button>
                            </div>
                            <div className="grid grid-cols-4 sm:grid-cols-6 gap-3">
                                {sizes.map((size) => (
                                    <button
                                        key={size}
                                        onClick={() => setSelectedSize(size)}
                                        className={`py-2 rounded-lg font-medium transition-all ${selectedSize === size
                                                ? 'bg-primary-600 text-white shadow-lg shadow-primary-500/30'
                                                : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-primary-500'
                                            }`}
                                    >
                                        {size}
                                    </button>
                                ))}
                            </div>
                            {!selectedSize && (
                                <p className="text-red-500 text-sm mt-2">Iltimos, xarid qilish uchun o'lchamni tanlang</p>
                            )}
                        </div>

                        {/* Quantity & Actions */}
                        <div className="flex flex-col sm:flex-row gap-4 mb-8">
                            <div className="flex items-center border border-gray-300 dark:border-gray-600 rounded-lg">
                                <button
                                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                                    className="p-3 hover:text-primary-600"
                                >
                                    <Minus className="w-5 h-5" />
                                </button>
                                <div className="w-12 text-center font-semibold text-lg">{quantity}</div>
                                <button
                                    onClick={() => setQuantity(quantity + 1)}
                                    className="p-3 hover:text-primary-600"
                                >
                                    <Plus className="w-5 h-5" />
                                </button>
                            </div>

                            <button
                                onClick={handleAddToCart}
                                disabled={!product.available}
                                className="flex-1 btn btn-primary flex items-center justify-center gap-2 py-3 text-lg"
                            >
                                <ShoppingCart className="w-5 h-5" />
                                Savatchaga qo'shish
                            </button>

                            <button
                                className="p-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                                title="Sevimlilarga qo'shish"
                            >
                                <Heart className="w-6 h-6" />
                            </button>
                        </div>

                        {/* Features Info */}
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 py-6 border-t border-gray-200 dark:border-gray-700">
                            <div className="flex items-center gap-3">
                                <Shield className="w-6 h-6 text-primary-600" />
                                <span className="text-sm font-medium">1 Yil Kafolat</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <Truck className="w-6 h-6 text-primary-600" />
                                <span className="text-sm font-medium">Tez Yetkazib Berish</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <RotateCcw className="w-6 h-6 text-primary-600" />
                                <span className="text-sm font-medium">7 Kunda Qaytarish</span>
                            </div>
                        </div>

                        {/* Description */}
                        <div className="prose dark:prose-invert max-w-none mt-8">
                            <h3 className="text-xl font-bold mb-4">Mahsulot haqida</h3>
                            <p className="whitespace-pre-line text-gray-600 dark:text-gray-300 leading-relaxed">
                                {product.description}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProductDetailPage;
