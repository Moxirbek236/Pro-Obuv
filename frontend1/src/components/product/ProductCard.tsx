import React from 'react';
import { Link } from 'react-router-dom';
import { Star, ShoppingCart, Heart } from 'lucide-react';
import { Product } from '@/types/product.types';
import { formatCurrency } from '@/utils/formatters';
import { useAuth } from '@/hooks/useAuth';
import { useCart } from '@/hooks/useCart'; // We'll create this later, mocking for now
import { toast } from 'react-hot-toast';

interface ProductCardProps {
    product: Product;
}

const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
    const { isAuthenticated, role } = useAuth();
    // Placeholder for cart functionality
    const addToCart = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        toast.success(`${product.name} savatchaga qo'shildi`);
    };

    const toggleFavorite = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!isAuthenticated) {
            toast.error('Iltimos, avval tizimga kiring');
            return;
        }
        toast.success('Sevimlilarga qo\'shildi');
    };

    return (
        <Link
            to={`/product/${product.id}`}
            className="card card-hover group block h-full flex flex-col relative overflow-hidden"
        >
            {/* Badges */}
            <div className="absolute top-2 left-2 z-10 flex flex-col gap-1">
                {product.is_new && (
                    <span className="badge badge-primary">Yangi</span>
                )}
                {product.discount_percentage && product.discount_percentage > 0 && (
                    <span className="badge badge-error">-{product.discount_percentage}%</span>
                )}
            </div>

            {/* Image */}
            <div className="aspect-square bg-gray-100 dark:bg-gray-800 relative overflow-hidden">
                <img
                    src={product.image_url || '/placeholder-shoe.jpg'}
                    alt={product.name}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                    onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://placehold.co/400x400?text=No+Image';
                    }}
                />

                {/* Quick Actions Overlay (Desktop) */}
                <div className="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/60 to-transparent translate-y-full group-hover:translate-y-0 transition-transform duration-300 flex justify-between items-center opacity-0 group-hover:opacity-100">
                    <button
                        onClick={toggleFavorite}
                        className="p-2 bg-white rounded-full text-gray-700 hover:text-red-500 hover:bg-gray-100 transition-colors shadow-sm"
                        title="Sevimlilarga qo'shish"
                    >
                        <Heart className="w-5 h-5" />
                    </button>
                    <button
                        onClick={addToCart}
                        className="p-2 bg-primary-600 rounded-full text-white hover:bg-primary-700 transition-colors shadow-sm"
                        title="Savatchaga qo'shish"
                    >
                        <ShoppingCart className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="p-4 flex-1 flex flex-col">
                <div className="mb-2 text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {product.category}
                </div>
                <h3 className="font-heading font-semibold text-lg mb-1 group-hover:text-primary-600 transition-colors line-clamp-1">
                    {product.name}
                </h3>

                {/* Rating */}
                <div className="flex items-center mb-3">
                    <div className="flex text-yellow-400">
                        {[...Array(5)].map((_, i) => (
                            <Star
                                key={i}
                                className={`w-4 h-4 ${i < Math.round(product.rating || 0) ? 'fill-current' : 'text-gray-300 dark:text-gray-600'}`}
                            />
                        ))}
                    </div>
                    <span className="text-xs text-gray-500 ml-2">({product.rating || 0})</span>
                </div>

                <div className="mt-auto flex items-center justify-between">
                    <div className="flex flex-col">
                        {product.discount_percentage && product.discount_percentage > 0 ? (
                            <>
                                <span className="text-sm text-gray-500 line-through">
                                    {formatCurrency(product.price)}
                                </span>
                                <span className="text-lg font-bold text-primary-600">
                                    {formatCurrency(product.price * (1 - product.discount_percentage / 100))}
                                </span>
                            </>
                        ) : (
                            <span className="text-lg font-bold text-primary-600">
                                {formatCurrency(product.price)}
                            </span>
                        )}
                    </div>

                    {/* Mobile Add Cart Button */}
                    <button
                        onClick={addToCart}
                        className="md:hidden p-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-primary-600 dark:text-primary-400"
                    >
                        <ShoppingCart className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </Link>
    );
};

export default ProductCard;
