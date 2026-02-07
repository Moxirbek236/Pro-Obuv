import React from 'react';
import { Link } from 'react-router-dom';
import { Facebook, Instagram, Send, Youtube } from 'lucide-react';

const Footer: React.FC = () => {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="bg-gray-900 text-gray-300">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                    {/* Company Info */}
                    <div>
                        <h3 className="text-white font-heading font-bold text-lg mb-4">Safety.uz</h3>
                        <p className="text-sm mb-4">
                            Professional xavfsizlik poyabzallari, ishchi kiyimlari va sanoat jihozlari
                        </p>
                        <div className="flex space-x-4">
                            <a href="#" className="hover:text-primary-400 transition-colors">
                                <Facebook className="w-5 h-5" />
                            </a>
                            <a href="#" className="hover:text-primary-400 transition-colors">
                                <Instagram className="w-5 h-5" />
                            </a>
                            <a href="#" className="hover:text-primary-400 transition-colors">
                                <Send className="w-5 h-5" />
                            </a>
                            <a href="#" className="hover:text-primary-400 transition-colors">
                                <Youtube className="w-5 h-5" />
                            </a>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h4 className="text-white font-semibold mb-4">Tezkor havolalar</h4>
                        <ul className="space-y-2">
                            <li>
                                <Link to="/menu" className="hover:text-primary-400 transition-colors">
                                    Mahsulotlar
                                </Link>
                            </li>
                            <li>
                                <Link to="/about" className="hover:text-primary-400 transition-colors">
                                    Biz haqimizda
                                </Link>
                            </li>
                            <li>
                                <Link to="/contact" className="hover:text-primary-400 transition-colors">
                                    Aloqa
                                </Link>
                            </li>
                            <li>
                                <Link to="/news" className="hover:text-primary-400 transition-colors">
                                    Yangiliklar
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Customer Service */}
                    <div>
                        <h4 className="text-white font-semibold mb-4">Mijozlar uchun</h4>
                        <ul className="space-y-2">
                            <li>
                                <Link to="/user" className="hover:text-primary-400 transition-colors">
                                    Buyurtmalarim
                                </Link>
                            </li>
                            <li>
                                <Link to="/favorites" className="hover:text-primary-400 transition-colors">
                                    Sevimlilar
                                </Link>
                            </li>
                            <li>
                                <Link to="/settings" className="hover:text-primary-400 transition-colors">
                                    Sozlamalar
                                </Link>
                            </li>
                            <li>
                                <Link to="/downloads" className="hover:text-primary-400 transition-colors">
                                    Yuklab olish
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Contact Info */}
                    <div>
                        <h4 className="text-white font-semibold mb-4">Aloqa</h4>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <span className="block text-gray-400">Telefon:</span>
                                <a href="tel:+998901234567" className="hover:text-primary-400 transition-colors">
                                    +998 90 123 45 67
                                </a>
                            </li>
                            <li>
                                <span className="block text-gray-400">Email:</span>
                                <a href="mailto:info@safety.uz" className="hover:text-primary-400 transition-colors">
                                    info@safety.uz
                                </a>
                            </li>
                            <li>
                                <span className="block text-gray-400">Manzil:</span>
                                <span>Toshkent, O'zbekiston</span>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-center">
                    <p>&copy; {currentYear} Safety.uz. Barcha huquqlar himoyalangan.</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
