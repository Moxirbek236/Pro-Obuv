import React, { useState } from 'react';
import { Mail, Phone, MapPin, Send, Instagram, Facebook, Globe } from 'lucide-react';
import { SOCIAL_LINKS, CONTACT_INFO } from '@/utils/constants';

const ContactPage: React.FC = () => {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        subject: '',
        message: '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // Logic to send message
        console.log('Sending message:', formData);
        alert('Habaringiz yuborildi! Tez orada siz bilan bog\'lanamiz.');
        setFormData({ name: '', email: '', subject: '', message: '' });
    };

    return (
        <div className="bg-gray-50 dark:bg-gray-900 min-h-screen py-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-4xl font-heading font-bold text-center mb-16 text-gray-900 dark:text-white">
                    Biz Bilan Bog'laning
                </h1>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Contact Info */}
                    <div className="md:col-span-1 space-y-6">
                        <div className="card p-6 border-l-4 border-primary-600">
                            <h3 className="text-xl font-bold font-heading mb-6">Aloqa Ma'lumotlari</h3>

                            <div className="space-y-6">
                                <div className="flex items-start gap-4">
                                    <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center text-primary-600 flex-shrink-0">
                                        <Phone className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="font-semibold text-gray-900 dark:text-white">Telefon</p>
                                        <a href={`tel:${CONTACT_INFO.phone}`} className="text-gray-600 dark:text-gray-400 hover:text-primary-600">
                                            {CONTACT_INFO.phone}
                                        </a>
                                    </div>
                                </div>

                                <div className="flex items-start gap-4">
                                    <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center text-primary-600 flex-shrink-0">
                                        <Mail className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="font-semibold text-gray-900 dark:text-white">Email</p>
                                        <a href={`mailto:${CONTACT_INFO.email}`} className="text-gray-600 dark:text-gray-400 hover:text-primary-600">
                                            {CONTACT_INFO.email}
                                        </a>
                                    </div>
                                </div>

                                <div className="flex items-start gap-4">
                                    <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center text-primary-600 flex-shrink-0">
                                        <MapPin className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="font-semibold text-gray-900 dark:text-white">Manzil</p>
                                        <p className="text-gray-600 dark:text-gray-400">
                                            {CONTACT_INFO.address}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-8 pt-6 border-t border-gray-100 dark:border-gray-700">
                                <h4 className="font-semibold mb-4">Ijtimoiy Tarmoqlar</h4>
                                <div className="flex space-x-4">
                                    <a href={SOCIAL_LINKS.instagram} target="_blank" rel="noopener noreferrer" className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-primary-100 hover:text-primary-600 transition-colors">
                                        <Instagram className="w-5 h-5" />
                                    </a>
                                    <a href={SOCIAL_LINKS.telegram} target="_blank" rel="noopener noreferrer" className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-primary-100 hover:text-primary-600 transition-colors">
                                        <Send className="w-5 h-5" />
                                    </a>
                                    <a href={SOCIAL_LINKS.facebook} target="_blank" rel="noopener noreferrer" className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-primary-100 hover:text-primary-600 transition-colors">
                                        <Facebook className="w-5 h-5" />
                                    </a>
                                    <a href="#" className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-primary-100 hover:text-primary-600 transition-colors">
                                        <Globe className="w-5 h-5" />
                                    </a>
                                </div>
                            </div>
                        </div>

                        {/* Map */}
                        <div className="card p-2 h-64 md:h-auto overflow-hidden">
                            <iframe
                                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d47934.33230971512!2d69.21634842167969!3d41.3327266!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x38ae8dbb8e1f0349%3A0x1e2a56c429712a86!2sTashkent%2C%20Uzbekistan!5e0!3m2!1sen!2s!4v1691234567890!5m2!1sen!2s"
                                width="100%"
                                height="100%"
                                style={{ border: 0, borderRadius: '0.5rem', minHeight: '250px' }}
                                allowFullScreen={true}
                                loading="lazy"
                                referrerPolicy="no-referrer-when-downgrade"
                            ></iframe>
                        </div>
                    </div>

                    {/* Contact Form */}
                    <div className="md:col-span-2">
                        <div className="card p-8">
                            <h3 className="text-xl font-bold font-heading mb-6">Xabar Yuborish</h3>
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Ismingiz</label>
                                        <input
                                            required
                                            type="text"
                                            className="input"
                                            placeholder="Ismingizni kiriting"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Email</label>
                                        <input
                                            required
                                            type="email"
                                            className="input"
                                            placeholder="email@example.com"
                                            value={formData.email}
                                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Mavzu</label>
                                    <input
                                        required
                                        type="text"
                                        className="input"
                                        placeholder="Xabar mavzusi"
                                        value={formData.subject}
                                        onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Xabar</label>
                                    <textarea
                                        required
                                        className="input min-h-[150px]"
                                        placeholder="Xabaringizni yozing..."
                                        value={formData.message}
                                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                                    />
                                </div>

                                <div className="flex justify-end">
                                    <button type="submit" className="btn btn-primary px-8 py-3 flex items-center gap-2">
                                        <Send className="w-5 h-5" />
                                        Yuborish
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ContactPage;
