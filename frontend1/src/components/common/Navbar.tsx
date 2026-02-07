import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ShoppingCart, User, Menu, X, Search, LogOut, Heart, Package } from 'lucide-react';

const Navbar: React.FC = () => {
    const { isAuthenticated, user, role, logout } = useAuth();
    const navigate = useNavigate();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [userMenuOpen, setUserMenuOpen] = useState(false);

    const handleLogout = async () => {
        await logout();
        navigate('/');
    };

    return (
        <nav className="bg-white dark:bg-gray-900 shadow-md sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                    {/* Logo */}
                    <Link to="/" className="flex items-center space-x-2">
                        <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                            <span className="text-white font-bold text-xl">S</span>
                        </div>
                        <span className="font-heading font-bold text-xl text-gray-900 dark:text-white">
                            Safety.uz
                        </span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center space-x-8">
                        <Link to="/menu" className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                            Mahsulotlar
                        </Link>
                        <Link to="/about" className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                            Biz haqimizda
                        </Link>
                        <Link to="/contact" className="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                            Aloqa
                        </Link>
                    </div>

                    {/* Right Side Icons */}
                    <div className="flex items-center space-x-4">
                        {/* Search */}
                        <button className="p-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                            <Search className="w-5 h-5" />
                        </button>

                        {/* Cart */}
                        {(role === 'user' || role === 'guest') && (
                            <Link
                                to="/cart"
                                className="p-2 text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors relative"
                            >
                                <ShoppingCart className="w-5 h-5" />
                                <span className="absolute -top-1 -right-1 bg-secondary-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                                    0
                                </span>
                            </Link>
                        )}

                        {/* User Menu */}
                        {isAuthenticated ? (
                            <div className="relative">
                                <button
                                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                                    className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                                >
                                    <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                                        <span className="text-white text-sm font-medium">
                                            {user?.first_name?.[0] || 'U'}
                                        </span>
                                    </div>
                                </button>

                                {userMenuOpen && (
                                    <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg py-2 border border-gray-200 dark:border-gray-700">
                                        {role === 'user' && (
                                            <>
                                                <Link
                                                    to="/profile"
                                                    className="flex items-center space-x-2 px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                                                    onClick={() => setUserMenuOpen(false)}
                                                >
                                                    <User className="w-4 h-4" />
                                                    <span>Profil</span>
                                                </Link>
                                                <Link
                                                    to="/user"
                                                    className="flex items-center space-x-2 px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                                                    onClick={() => setUserMenuOpen(false)}
                                                >
                                                    <Package className="w-4 h-4" />
                                                    <span>Buyurtmalar</span>
                                                </Link>
                                                <Link
                                                    to="/favorites"
                                                    className="flex items-center space-x-2 px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                                                    onClick={() => setUserMenuOpen(false)}
                                                >
                                                    <Heart className="w-4 h-4" />
                                                    <span>Sevimlilar</span>
                                                </Link>
                                            </>
                                        )}
                                        <button
                                            onClick={handleLogout}
                                            className="flex items-center space-x-2 px-4 py-2 text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700 w-full text-left"
                                        >
                                            <LogOut className="w-4 h-4" />
                                            <span>Chiqish</span>
                                        </button>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <Link
                                to="/login"
                                className="btn btn-primary hidden md:block"
                            >
                                Kirish
                            </Link>
                        )}

                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2 text-gray-700 dark:text-gray-300"
                        >
                            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                        </button>
                    </div>
                </div>

                {/* Mobile Menu */}
                {mobileMenuOpen && (
                    <div className="md:hidden py-4 border-t border-gray-200 dark:border-gray-700">
                        <Link
                            to="/menu"
                            className="block py-2 text-gray-700 dark:text-gray-300 hover:text-primary-600"
                            onClick={() => setMobileMenuOpen(false)}
                        >
                            Mahsulotlar
                        </Link>
                        <Link
                            to="/about"
                            className="block py-2 text-gray-700 dark:text-gray-300 hover:text-primary-600"
                            onClick={() => setMobileMenuOpen(false)}
                        >
                            Biz haqimizda
                        </Link>
                        <Link
                            to="/contact"
                            className="block py-2 text-gray-700 dark:text-gray-300 hover:text-primary-600"
                            onClick={() => setMobileMenuOpen(false)}
                        >
                            Aloqa
                        </Link>
                        {!isAuthenticated && (
                            <Link
                                to="/login"
                                className="block py-2 text-primary-600 font-medium"
                                onClick={() => setMobileMenuOpen(false)}
                            >
                                Kirish
                            </Link>
                        )}
                    </div>
                )}
            </div>
        </nav>
    );
};

export default Navbar;
