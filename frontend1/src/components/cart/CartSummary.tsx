import React, { useState } from 'react';
import { formatCurrency } from '@/utils/formatters';
import { useCart } from '@/hooks/useCart';
import CheckoutModal from './CheckoutModal'; // Import modal

const CartSummary: React.FC = () => {
    const { items, clearCart } = useCart();
    const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);

    const subtotal = items.reduce((sum, item) => sum + (item.product_price || 0) * item.quantity, 0);
    const delivery = subtotal > 500000 ? 0 : 30000;
    const total = subtotal + delivery;

    return (
        <>
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 sticky top-24">
                <h2 className="text-lg font-bold font-heading mb-6 border-b border-gray-100 dark:border-gray-700 pb-4">
                    Buyurtma ma'lumotlari
                </h2>

                <div className="space-y-4 mb-6">
                    <div className="flex justify-between text-gray-600 dark:text-gray-400">
                        <span>Jami mahsulotlar ({items.length}):</span>
                        <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(subtotal)}</span>
                    </div>
                    <div className="flex justify-between text-gray-600 dark:text-gray-400">
                        <span>Yetkazib berish:</span>
                        {delivery === 0 ? (
                            <span className="text-green-500 font-medium">Bepul</span>
                        ) : (
                            <span className="font-medium text-gray-900 dark:text-white">{formatCurrency(delivery)}</span>
                        )}
                    </div>
                    <div className="pt-4 border-t border-gray-100 dark:border-gray-700 flex justify-between items-center">
                        <span className="text-lg font-bold">Jami:</span>
                        <span className="text-xl font-bold text-primary-600">{formatCurrency(total)}</span>
                    </div>
                </div>

                <button
                    onClick={() => setIsCheckoutOpen(true)}
                    className="btn btn-primary w-full py-3 mb-3 text-lg font-semibold shadow-lg shadow-primary-500/30"
                >
                    Rasmiylashtirish
                </button>

                <button
                    onClick={clearCart}
                    className="w-full text-center text-sm text-gray-500 hover:text-red-500 transition-colors"
                >
                    Savatchani tozalash
                </button>

                {subtotal < 500000 && (
                    <div className="mt-6 p-3 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-sm rounded-lg text-center">
                        Yana {formatCurrency(500000 - subtotal)} xarid qiling va <strong>bepul</strong> yetkazib berishga ega bo'ling!
                    </div>
                )}
            </div>

            <CheckoutModal
                isOpen={isCheckoutOpen}
                onClose={() => setIsCheckoutOpen(false)}
            />
        </>
    );
};

export default CartSummary;
