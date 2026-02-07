import React from 'react';
import { Shield, Users, Trophy, Target } from 'lucide-react';

const AboutPage: React.FC = () => {
    return (
        <div className="bg-gray-50 dark:bg-gray-900 min-h-screen py-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

                {/* Header */}
                <div className="text-center mb-16">
                    <h1 className="text-4xl md:text-5xl font-heading font-bold mb-6 text-gray-900 dark:text-white">
                        Safety.uz Haqida
                    </h1>
                    <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto leading-relaxed">
                        Biz O'zbekistonda sanoat xavfsizligi va ishchi poyabzallari bo'yicha yetakchi yetkazib beruvchilardanmiz.
                        Bizning maqsadimiz - har bir ishchining xavfsizligi va qulayligini ta'minlashdir.
                    </p>
                </div>

                {/* Mission & Vision */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-20">
                    <div className="card p-8 bg-white dark:bg-gray-800 border-l-4 border-primary-600">
                        <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center mb-6 text-primary-600">
                            <Target className="w-6 h-6" />
                        </div>
                        <h3 className="text-2xl font-bold font-heading mb-4">Bizning Missiyamiz</h3>
                        <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                            Sanoat korxonalari va qurilish tashkilotlarini xalqaro standartlarga javob beradigan,
                            yuqori sifatli va ishonchli himoya vositalari bilan ta'minlash orqali
                            mehnat xavfsizligini yangi bosqichga olib chiqish.
                        </p>
                    </div>

                    <div className="card p-8 bg-white dark:bg-gray-800 border-l-4 border-secondary-600">
                        <div className="w-12 h-12 bg-secondary-100 dark:bg-secondary-900 rounded-lg flex items-center justify-center mb-6 text-secondary-600">
                            <Trophy className="w-6 h-6" />
                        </div>
                        <h3 className="text-2xl font-bold font-heading mb-4">Bizning Maqsadimiz</h3>
                        <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                            O'zbekistondagi eng ishonchli va innovatsion xavfsizlik poyabzallari brendiga aylanish.
                            Mijozlarimizga nafaqat mahsulot, balki to'liq xavfsizlik yechimlarini taqdim etish.
                        </p>
                    </div>
                </div>

                {/* Values */}
                <div className="mb-20">
                    <h2 className="text-3xl font-bold font-heading text-center mb-12">Bizning Qadriyatlarimiz</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="text-center p-6">
                            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4 text-blue-600">
                                <Shield className="w-8 h-8" />
                            </div>
                            <h3 className="text-xl font-bold mb-3">Xavfsizlik Birinchi O'rinda</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Biz hech qachon xavfsizlik standartlaridan murosaga bormaymiz.
                                Har bir mahsulot qattiq sinovdan o'tgan.
                            </p>
                        </div>
                        <div className="text-center p-6">
                            <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4 text-green-600">
                                <Users className="w-8 h-8" />
                            </div>
                            <h3 className="text-xl font-bold mb-3">Mijozga Yo'naltirilganlik</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Har bir mijoz biz uchun qadrli. Biz individual yondashuv va
                                tezkor xizmat ko'rsatishni kafolatlaymiz.
                            </p>
                        </div>
                        <div className="text-center p-6">
                            <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4 text-purple-600">
                                <Trophy className="w-8 h-8" />
                            </div>
                            <h3 className="text-xl font-bold mb-3">Sifat va Innovatsiya</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Biz doimo eng yangi texnologiyalar va materiallardan foydalanib,
                                mahsulotlarimiz sifatini oshirib boramiz.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Stats */}
                <div className="bg-primary-600 rounded-2xl p-12 text-center text-white">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        <div>
                            <div className="text-4xl font-bold mb-2">5+</div>
                            <div className="text-primary-200">Yillik Tajriba</div>
                        </div>
                        <div>
                            <div className="text-4xl font-bold mb-2">10k+</div>
                            <div className="text-primary-200">Mamnun Mijozlar</div>
                        </div>
                        <div>
                            <div className="text-4xl font-bold mb-2">500+</div>
                            <div className="text-primary-200">Mahsulot Turlari</div>
                        </div>
                        <div>
                            <div className="text-4xl font-bold mb-2">24/7</div>
                            <div className="text-primary-200">Qo'llab-quvvatlash</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AboutPage;
