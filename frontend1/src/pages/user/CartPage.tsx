import React from 'react';
import { Link } from 'react-router-dom';
import { ShoppingCart } from 'lucide-react';
import CartItem from '@/components/cart/CartItem';
import CartSummary from '@/components/cart/CartSummary';
import { useCart } from '@/hooks/useCart';

const CartPage: React.FC = () => {
    const { items, isLoading } = useCart();

    if (isLoading) {
        return (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="animate-pulse space-y-4">
                    {[...Array(3)].map((_, i) => (
                        <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                    ))}
                </div>
            </div>
        );
    }

    if (items.length === 0) {
        return (
            <div className="min-h-[60vh] flex flex-col items-center justify-center p-4">
                <div className="w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-6">
                    <ShoppingCart className="w-10 h-10 text-gray-400" />
                </div>
                <h2 className="text-2xl font-bold font-heading mb-2">Savatchangiz bo'sh</h2>
                <p className="text-gray-500 dark:text-gray-400 mb-8 text-center max-w-md">
                    Siz hali hech narsa tanlamadingiz. Katalogimizdan o'zingizga yoqqan mahsulotlarni toping.
                </p>
                <Link to="/menu" className="btn btn-primary px-8">
                    Katalogga o'tish
                </Link>
            </div>
        );
    }

    return (
        <div className="bg-gray-50 dark:bg-gray-950 min-h-screen py-10">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl font-heading font-bold mb-8">Savatcha ({items.length})</h1>

                <div className="flex flex-col lg:flex-row gap-8">
                    {/* Cart Items */}
                    <div className="flex-1 space-y-4">
                        {items.map((item) => (
                            <CartItem key={item.id} item={item} />
                        ))}
                    </div>

                    {/* Checkout Summary */}
                    <div className="lg:w-96 flex-shrink-0">
                        <CartSummary />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CartPage;
