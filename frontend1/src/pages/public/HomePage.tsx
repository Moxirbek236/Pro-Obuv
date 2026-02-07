import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Truck, Award, HeadphonesIcon } from 'lucide-react';

const HomePage: React.FC = () => {
    return (
        <div className="min-h-screen">
            {/* Hero Section */}
            <section className="bg-gradient-to-r from-primary-600 to-primary-800 text-white py-20">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center">
                        <h1 className="text-4xl md:text-6xl font-heading font-bold mb-6 animate-fade-in">
                            Professional Xavfsizlik Jihozlari
                        </h1>
                        <p className="text-xl md:text-2xl mb-8 text-primary-100 animate-slide-up">
                            Ishchi poyabzallari, xavfsizlik kiyimlari va sanoat jihozlari
                        </p>
                        <Link
                            to="/menu"
                            className="inline-block bg-white text-primary-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-primary-50 transition-all duration-200 hover:scale-105"
                        >
                            Mahsulotlarni ko'rish
                        </Link>
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="py-16 bg-gray-50 dark:bg-gray-900">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                        <div className="text-center">
                            <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mx-auto mb-4">
                                <ShieldCheck className="w-8 h-8 text-primary-600 dark:text-primary-400" />
                            </div>
                            <h3 className="font-semibold text-lg mb-2">Sifat kafolati</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Barcha mahsulotlar sertifikatlangan
                            </p>
                        </div>

                        <div className="text-center">
                            <div className="w-16 h-16 bg-secondary-100 dark:bg-secondary-900 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Truck className="w-8 h-8 text-secondary-600 dark:text-secondary-400" />
                            </div>
                            <h3 className="font-semibold text-lg mb-2">Tez yetkazib berish</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Butun O'zbekiston bo'ylab yetkazib berish
                            </p>
                        </div>

                        <div className="text-center">
                            <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Award className="w-8 h-8 text-green-600 dark:text-green-400" />
                            </div>
                            <h3 className="font-semibold text-lg mb-2">Eng yaxshi narxlar</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Raqobatbardosh narxlar va chegirmalar
                            </p>
                        </div>

                        <div className="text-center">
                            <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                                <HeadphonesIcon className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                            </div>
                            <h3 className="font-semibold text-lg mb-2">24/7 Qo'llab-quvvatlash</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Doimo sizning xizmatingizda
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h2 className="text-3xl md:text-4xl font-heading font-bold mb-4">
                        Bizning mahsulotlarimiz bilan xavfsizlikni ta'minlang
                    </h2>
                    <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
                        Yuqori sifatli xavfsizlik jihozlari va professional xizmat
                    </p>
                    <Link
                        to="/menu"
                        className="btn btn-primary btn-lg"
                    >
                        Hoziroq xarid qiling
                    </Link>
                </div>
            </section>
        </div>
    );
};

export default HomePage;
