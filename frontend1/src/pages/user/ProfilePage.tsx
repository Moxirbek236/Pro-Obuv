import React, { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { User, MapPin, Smartphone, Mail, Edit2, LogOut, Package } from 'lucide-react';
import { Link } from 'react-router-dom';

const ProfilePage: React.FC = () => {
    const { user, logout } = useAuth();
    const [isEditing, setIsEditing] = useState(false);

    // Local state for editing form
    const [formData, setFormData] = useState({
        first_name: user?.first_name || '',
        last_name: user?.last_name || '',
        phone: user?.phone || '',
        address: user?.address || '',
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSave = () => {
        // TODO: Implement API update
        console.log('Saved:', formData);
        setIsEditing(false);
    };

    return (
        <div className="bg-gray-50 dark:bg-gray-900 min-h-screen py-10">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl font-heading font-bold mb-8">Mening Profilim</h1>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* User Info Card */}
                    <div className="md:col-span-2 space-y-6">
                        <div className="card p-6">
                            <div className="flex justify-between items-start mb-6">
                                <div className="flex items-center space-x-4">
                                    <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center text-primary-600 dark:text-primary-400">
                                        <User className="w-8 h-8" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold font-heading">
                                            {user?.first_name} {user?.last_name}
                                        </h2>
                                        <p className="text-gray-500 text-sm">Foydalanuvchi</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setIsEditing(!isEditing)}
                                    className={`p-2 rounded-lg transition-colors ${isEditing ? 'bg-primary-600 text-white' : 'text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20'
                                        }`}
                                >
                                    <Edit2 className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm text-gray-500 block mb-1">Ism</label>
                                        {isEditing ? (
                                            <input
                                                name="first_name"
                                                value={formData.first_name}
                                                onChange={handleChange}
                                                className="input"
                                            />
                                        ) : (
                                            <p className="font-medium flex items-center gap-2">
                                                <User className="w-4 h-4 text-gray-400" />
                                                {user?.first_name}
                                            </p>
                                        )}
                                    </div>
                                    <div>
                                        <label className="text-sm text-gray-500 block mb-1">Familiya</label>
                                        {isEditing ? (
                                            <input
                                                name="last_name"
                                                value={formData.last_name}
                                                onChange={handleChange}
                                                className="input"
                                            />
                                        ) : (
                                            <p className="font-medium flex items-center gap-2">
                                                {user?.last_name}
                                            </p>
                                        )}
                                    </div>
                                    <div>
                                        <label className="text-sm text-gray-500 block mb-1">Telefon</label>
                                        {isEditing ? (
                                            <input
                                                name="phone"
                                                value={formData.phone}
                                                onChange={handleChange}
                                                className="input"
                                            />
                                        ) : (
                                            <p className="font-medium flex items-center gap-2">
                                                <Smartphone className="w-4 h-4 text-gray-400" />
                                                {user?.phone}
                                            </p>
                                        )}
                                    </div>
                                    <div>
                                        <label className="text-sm text-gray-500 block mb-1">Email</label>
                                        <p className="font-medium flex items-center gap-2 text-gray-700 dark:text-gray-300">
                                            <Mail className="w-4 h-4 text-gray-400" />
                                            {user?.email}
                                        </p>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
                                    <label className="text-sm text-gray-500 block mb-1">Manzil</label>
                                    {isEditing ? (
                                        <div className="space-y-2">
                                            <input
                                                name="address"
                                                value={formData.address}
                                                onChange={handleChange}
                                                className="input w-full"
                                                placeholder="Manzilni kiriting..."
                                            />
                                            <div className="flex justify-end gap-2">
                                                <button onClick={() => setIsEditing(false)} className="btn btn-ghost text-sm">Bekor qilish</button>
                                                <button onClick={handleSave} className="btn btn-primary text-sm">Saqlash</button>
                                            </div>
                                        </div>
                                    ) : (
                                        <p className="font-medium flex items-start gap-2">
                                            <MapPin className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                                            {user?.address || "Manzil kiritilmagan"}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Recent Orders Preview */}
                        <div className="card p-6">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-bold font-heading">So'nggi buyurtmalar</h3>
                                <Link to="/user" className="text-primary-600 hover:text-primary-700 text-sm font-medium">Barchasini ko'rish</Link>
                            </div>
                            <div className="text-center py-8 text-gray-500">
                                <Package className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                                <p>Buyurtmalar tarixi bo'sh</p>
                            </div>
                        </div>
                    </div>

                    {/* Sidebar Menu */}
                    <div className="space-y-4">
                        <div className="card p-4">
                            <nav className="space-y-1">
                                <Link to="/profile" className="flex items-center gap-3 px-3 py-2 text-primary-600 bg-primary-50 dark:bg-primary-900/20 rounded-lg font-medium">
                                    <User className="w-5 h-5" />
                                    Shaxsiy ma'lumotlar
                                </Link>
                                <Link to="/user" className="flex items-center gap-3 px-3 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                                    <Package className="w-5 h-5" />
                                    Buyurtmalar tarixi
                                </Link>
                                <Link to="/favorites" className="flex items-center gap-3 px-3 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                                    <div className="w-5 h-5">❤️</div>
                                    Sevimlilar
                                </Link>
                                <Link to="/settings" className="flex items-center gap-3 px-3 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
                                    <div className="w-5 h-5">⚙️</div>
                                    Sozlamalar
                                </Link>
                            </nav>

                            <div className="mt-6 pt-6 border-t border-gray-100 dark:border-gray-700">
                                <button onClick={() => logout()} className="flex items-center gap-3 px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg w-full transition-colors">
                                    <LogOut className="w-5 h-5" />
                                    Chiqish
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;
