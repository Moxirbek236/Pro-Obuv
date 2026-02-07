import React, { useState } from 'react';
import { X, MapPin, Phone, CreditCard, Truck, User } from 'lucide-react';
import { useCart } from '@/hooks/useCart';
import { useAuth } from '@/hooks/useAuth';
import { formatCurrency } from '@/utils/formatters';
import toast from 'react-hot-toast';
import { PAYMENT_METHODS } from '@/utils/constants';

interface CheckoutModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const CheckoutModal: React.FC<CheckoutModalProps> = ({ isOpen, onClose }) => {
    const { items, total, clearCart } = useCart();
    const { user } = useAuth();

    const [formData, setFormData] = useState({
        name: user?.first_name ? `${user.first_name} ${user.last_name || ''}` : '',
        phone: user?.phone || '',
        address: user?.address || '',
        paymentMethod: 'cash',
        notes: '',
    });

    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!isOpen) return null;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);

        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));

        toast.success('Buyurtmangiz qabul qilindi! Tez orada operatorlarimiz bog\'lanishadi.');
        clearCart();
        setIsSubmitting(false);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            {/* Backdrop */}
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" onClick={onClose}></div>

            <div className="flex min-h-screen items-center justify-center p-4">
                <div className="relative w-full max-w-2xl bg-white dark:bg-gray-800 rounded-2xl shadow-xl transform transition-all">

                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-700">
                        <h2 className="text-2xl font-bold font-heading">Buyurtmani rasmiylashtirish</h2>
                        <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors">
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                            {/* Contact Info */}
                            <div className="space-y-4">
                                <h3 className="font-semibold flex items-center gap-2">
                                    <User className="w-5 h-5 text-primary-600" />
                                    Shaxsiy ma'lumotlar
                                </h3>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Ism-familiya</label>
                                    <input
                                        required
                                        name="name"
                                        value={formData.name}
                                        onChange={handleChange}
                                        className="input"
                                        placeholder="Ismingizni kiriting"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Telefon raqam</label>
                                    <div className="relative">
                                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                        <input
                                            required
                                            name="phone"
                                            value={formData.phone}
                                            onChange={handleChange}
                                            className="input pl-10"
                                            placeholder="+998 90 123 45 67"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Delivery Info */}
                            <div className="space-y-4">
                                <h3 className="font-semibold flex items-center gap-2">
                                    <Truck className="w-5 h-5 text-primary-600" />
                                    Yetkazib berish
                                </h3>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Manzil</label>
                                    <div className="relative">
                                        <MapPin className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                                        <textarea
                                            required
                                            name="address"
                                            value={formData.address}
                                            onChange={handleChange}
                                            className="input pl-10 min-h-[100px] py-3"
                                            placeholder="Aniq manzilingizni kiriting (Viloyat, shahar, ko'cha, uy...)"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <hr className="my-6 border-gray-100 dark:border-gray-700" />

                        {/* Payment & Summary */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <h3 className="font-semibold flex items-center gap-2">
                                    <CreditCard className="w-5 h-5 text-primary-600" />
                                    To'lov turi
                                </h3>

                                <div className="grid grid-cols-3 gap-3">
                                    {PAYMENT_METHODS.map((method) => (
                                        <button
                                            key={method.id}
                                            type="button"
                                            onClick={() => setFormData(prev => ({ ...prev, paymentMethod: method.id }))}
                                            className={`p-3 rounded-lg border flex flex-col items-center gap-2 transition-all ${formData.paymentMethod === method.id
                                                    ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                                                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                                                }`}
                                        >
                                            {typeof method.icon === 'string' && method.icon.startsWith('/') ? (
                                                <img src={method.icon} alt={method.name} className="w-6 h-6 object-contain" />
                                            ) : (
                                                <span className="text-2xl">{method.icon}</span>
                                            )}
                                            <span className="text-xs font-medium">{method.name}</span>
                                        </button>
                                    ))}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Izoh (ixtiyoriy)</label>
                                    <textarea
                                        name="notes"
                                        value={formData.notes}
                                        onChange={handleChange}
                                        className="input min-h-[80px]"
                                        placeholder="Buyurtma bo'yicha qo'shimcha izoh..."
                                    />
                                </div>
                            </div>

                            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-6 space-y-4">
                                <h3 className="font-semibold">Buyurtma tarkibi</h3>
                                <div className="space-y-2 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
                                    {items.map((item) => (
                                        <div key={item.id} className="flex justify-between text-sm">
                                            <span className="text-gray-600 dark:text-gray-400 line-clamp-1 flex-1 pr-4">
                                                {item.quantity}x {item.product_name}
                                            </span>
                                            <span className="font-medium">
                                                {formatCurrency((item.product_price || 0) * item.quantity)}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                                    <div className="flex justify-between items-center text-lg font-bold">
                                        <span>Jami:</span>
                                        <span className="text-primary-600">{formatCurrency(total)}</span>
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="btn btn-primary w-full py-3 mt-4 text-lg font-semibold shadow-lg shadow-primary-500/30"
                                >
                                    {isSubmitting ? (
                                        <span className="flex items-center justify-center gap-2">
                                            <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
                                            Yuborilmoqda...
                                        </span>
                                    ) : (
                                        "Buyurtmani tasdiqlash"
                                    )}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default CheckoutModal;
