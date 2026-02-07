import React from 'react';
import { Link } from 'react-router-dom';
import { Heart } from 'lucide-react';
import ProductCard from '@/components/product/ProductCard';

// Reuse mock generator for now
const generateMockFavorites = (count: number) => {
    return Array.from({ length: count }).map((_, index) => ({
        id: index + 100,
        name: `Sevimli Mahsulot ${index + 1}`,
        price: Math.floor(Math.random() * 500000) + 100000,
        category: ['tufli', 'etik'][Math.floor(Math.random() * 2)] as any,
        description: 'Ajoyib sifat.',
        image_url: `https://placehold.co/400x400?text=Favorite+${index + 1}`,
        available: true,
        stock_quantity: 10,
        rating: 5,
        is_new: false,
    }));
};

const FavoritesPage: React.FC = () => {
    const favorites = generateMockFavorites(4); // Mock data

    return (
        <div className="bg-gray-50 dark:bg-gray-900 min-h-screen py-10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center gap-3 mb-8">
                    <Heart className="w-8 h-8 text-red-500 fill-current" />
                    <h1 className="text-3xl font-heading font-bold">Sevimlilar</h1>
                </div>

                {favorites.length > 0 ? (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                        {favorites.map((product) => (
                            <ProductCard key={product.id} product={product} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
                        <Heart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                            Sevimlilar ro'yxati bo'sh
                        </h3>
                        <p className="text-gray-500 mb-6">
                            Sizga yoqqan mahsulotlarni yurakcha tugmasini bosib saqlab qo'yishingiz mumkin.
                        </p>
                        <Link to="/menu" className="btn btn-primary">
                            Katalogga o'tish
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
};

export default FavoritesPage;
