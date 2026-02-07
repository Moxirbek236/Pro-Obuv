import React, { useState } from 'react';
import { Minus, Plus, Trash2 } from 'lucide-react';
import { CartItem as CartItemType } from '@/types/cart.types';
import { formatCurrency } from '@/utils/formatters';
import { useCart } from '@/hooks/useCart';

interface CartItemProps {
    item: CartItemType;
}

const CartItem: React.FC<CartItemProps> = ({ item }) => {
    const { updateQuantity, removeFromCart } = useCart();
    const [isUpdating, setIsUpdating] = useState(false);

    const handleUpdateQuantity = async (newQuantity: number) => {
        if (newQuantity < 1) return;
        setIsUpdating(true);
        await updateQuantity(item.id, newQuantity);
        setIsUpdating(false);
    };

    const handleRemove = async () => {
        setIsUpdating(true);
        await removeFromCart(item.id);
        setIsUpdating(false);
    };

    return (
        <div className={`flex flex-col sm:flex-row items-center gap-4 bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 ${isUpdating ? 'opacity-50 pointer-events-none' : ''}`}>
            {/* Image */}
            <div className="w-24 h-24 flex-shrink-0 bg-gray-100 dark:bg-gray-700 rounded-md overflow-hidden">
                <img
                    src={item.product_image || 'https://placehold.co/100x100?text=Product'}
                    alt={item.product_name}
                    className="w-full h-full object-cover"
                />
            </div>

            {/* Info */}
            <div className="flex-1 text-center sm:text-left">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                    {item.product_name || 'Nomsiz Mahsulot'}
                </h3>
                <p className="text-primary-600 font-medium font-mono">
                    {formatCurrency(item.product_price || 0)}
                </p>
            </div>

            {/* Quantity */}
            <div className="flex items-center border border-gray-200 dark:border-gray-600 rounded-lg">
                <button
                    onClick={() => handleUpdateQuantity(item.quantity - 1)}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
                >
                    <Minus className="w-4 h-4" />
                </button>
                <div className="w-10 text-center font-medium">
                    {item.quantity}
                </div>
                <button
                    onClick={() => handleUpdateQuantity(item.quantity + 1)}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
                >
                    <Plus className="w-4 h-4" />
                </button>
            </div>

            {/* Total & Remove */}
            <div className="text-right flex flex-col items-center sm:items-end gap-2 min-w-[100px]">
                <span className="font-bold text-lg text-gray-900 dark:text-gray-100">
                    {formatCurrency((item.product_price || 0) * item.quantity)}
                </span>
                <button
                    onClick={handleRemove}
                    className="text-red-500 hover:text-red-700 p-1 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    title="O'chirish"
                >
                    <Trash2 className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
};

export default CartItem;
