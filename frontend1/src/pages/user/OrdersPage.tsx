import React from 'react';
import { Link } from 'react-router-dom';
import { Package, Clock, CheckCircle, XCircle, Truck, ArrowRight, ChevronRight } from 'lucide-react';
import { formatDate, formatCurrency } from '@/utils/formatters';

// Mock data
const mockOrders = [
    {
        id: 1023,
        ticket_no: 8932,
        date: '2024-02-01T14:30:00',
        status: 'in_delivery',
        total_price: 1350000,
        items: [
            { name: 'Xavfsizlik Poyabzali S3', quantity: 2, image: 'https://placehold.co/100x100' },
            { name: 'Himoya kaskasi', quantity: 1, image: 'https://placehold.co/100x100' }
        ]
    },
    {
        id: 985,
        ticket_no: 8421,
        date: '2024-01-25T09:15:00',
        status: 'delivered',
        total_price: 450000,
        items: [
            { name: 'Ishchi qo\'lqoplari', quantity: 10, image: 'https://placehold.co/100x100' }
        ]
    },
    {
        id: 980,
        ticket_no: 8400,
        date: '2024-01-20T11:20:00',
        status: 'cancelled',
        total_price: 890000,
        items: [
            { name: 'Maxsus kiyim', quantity: 1, image: 'https://placehold.co/100x100' }
        ]
    }
];

const getStatusColor = (status: string) => {
    switch (status) {
        case 'delivered': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
        case 'in_delivery': return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400';
        case 'cancelled': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
        default: return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
    }
};

const getStatusLabel = (status: string) => {
    switch (status) {
        case 'delivered': return 'Yetkazildi';
        case 'in_delivery': return 'Yo\'lda';
        case 'cancelled': return 'Bekor qilindi';
        case 'pending': return 'Kutilmoqda';
        default: return status;
    }
};

const getStatusIcon = (status: string) => {
    switch (status) {
        case 'delivered': return <CheckCircle className="w-5 h-5" />;
        case 'in_delivery': return <Truck className="w-5 h-5" />;
        case 'cancelled': return <XCircle className="w-5 h-5" />;
        default: return <Clock className="w-5 h-5" />;
    }
}

const OrdersPage: React.FC = () => {
    return (
        <div className="bg-gray-50 dark:bg-gray-900 min-h-screen py-10">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl font-heading font-bold mb-8">Buyurtmalar tarixi</h1>

                <div className="space-y-6">
                    {mockOrders.length > 0 ? (
                        mockOrders.map((order) => (
                            <div key={order.id} className="card overflow-hidden">
                                {/* Header */}
                                <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            <span className="font-bold text-lg">#{order.ticket_no}</span>
                                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium flex items-center gap-1.5 ${getStatusColor(order.status)}`}>
                                                {getStatusIcon(order.status)}
                                                {getStatusLabel(order.status)}
                                            </span>
                                        </div>
                                        <div className="text-sm text-gray-500">
                                            {formatDate(order.date)}
                                        </div>
                                    </div>
                                    <div className="font-bold text-xl text-primary-600">
                                        {formatCurrency(order.total_price)}
                                    </div>
                                </div>

                                {/* Items */}
                                <div className="p-6 bg-gray-50 dark:bg-gray-800/50">
                                    <div className="space-y-4">
                                        {order.items.map((item, idx) => (
                                            <div key={idx} className="flex items-center gap-4">
                                                <div className="w-16 h-16 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden flex-shrink-0">
                                                    <img src={item.image} alt={item.name} className="w-full h-full object-cover" />
                                                </div>
                                                <div className="flex-1">
                                                    <h4 className="font-medium text-gray-900 dark:text-white">{item.name}</h4>
                                                    <p className="text-sm text-gray-500">x{item.quantity} dona</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Footer */}
                                <div className="px-6 py-4 bg-white dark:bg-gray-800 border-t border-gray-100 dark:border-gray-700 flex justify-end">
                                    <button className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center gap-1 group">
                                        Batafsil ma'lumot
                                        <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                    </button>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-20 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Buyurtmalar mavjud emas</h3>
                            <p className="text-gray-500 mb-6">Siz hali hech qanday buyurtma bermagansiz</p>
                            <Link to="/menu" className="btn btn-primary">Xarid qilishni boshlash</Link>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default OrdersPage;
