import React, { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Moon, Sun, Monitor, Type, Globe, Volume2, Bell } from 'lucide-react';
import { toast } from 'react-hot-toast';

const SettingsPage: React.FC = () => {
    const [language, setLanguage] = useState<'uz' | 'ru' | 'en'>('uz');
    const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
    const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('medium');
    const [notifications, setNotifications] = useState(true);

    const handleSave = () => {
        // Logic to save preferences (e.g., to localStorage or API)
        toast.success('Sozlamalar saqlandi');
    };

    return (
        <div className="bg-gray-50 dark:bg-gray-900 min-h-screen py-10">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl font-heading font-bold mb-8">Sozlamalar</h1>

                <div className="space-y-6">
                    {/* Appearance */}
                    <div className="card p-6">
                        <h2 className="text-xl font-bold font-heading mb-6 flex items-center gap-2">
                            <Monitor className="w-5 h-5 text-primary-600" />
                            Ko'rinish
                        </h2>
                        <div className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Mavzu</label>
                                <div className="grid grid-cols-3 gap-4">
                                    <button
                                        onClick={() => setTheme('light')}
                                        className={`p-4 border rounded-lg flex flex-col items-center gap-2 transition-all ${theme === 'light' ? 'border-primary-600 bg-primary-50 text-primary-700' : 'border-gray-200 hover:bg-gray-50'}`}
                                    >
                                        <Sun className="w-6 h-6" />
                                        <span className="text-sm font-medium">Yorug'</span>
                                    </button>
                                    <button
                                        onClick={() => setTheme('dark')}
                                        className={`p-4 border rounded-lg flex flex-col items-center gap-2 transition-all ${theme === 'dark' ? 'border-primary-600 bg-gray-800 text-white' : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'}`}
                                    >
                                        <Moon className="w-6 h-6" />
                                        <span className="text-sm font-medium">Qorong'u</span>
                                    </button>
                                    <button
                                        onClick={() => setTheme('system')}
                                        className={`p-4 border rounded-lg flex flex-col items-center gap-2 transition-all ${theme === 'system' ? 'border-primary-600 bg-primary-50 text-primary-700' : 'border-gray-200 hover:bg-gray-50'}`}
                                    >
                                        <Monitor className="w-6 h-6" />
                                        <span className="text-sm font-medium">Tizim</span>
                                    </button>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    <div className="flex items-center gap-2">
                                        <Type className="w-4 h-4" />
                                        Shrift o'lchami
                                    </div>
                                </label>
                                <div className="flex items-center gap-4 bg-gray-100 dark:bg-gray-800 p-2 rounded-lg">
                                    <button
                                        onClick={() => setFontSize('small')}
                                        className={`flex-1 py-1.5 text-sm rounded-md transition-colors ${fontSize === 'small' ? 'bg-white dark:bg-gray-600 shadow-sm font-medium' : 'text-gray-500'}`}
                                    >
                                        Kichik
                                    </button>
                                    <button
                                        onClick={() => setFontSize('medium')}
                                        className={`flex-1 py-1.5 text-base rounded-md transition-colors ${fontSize === 'medium' ? 'bg-white dark:bg-gray-600 shadow-sm font-medium' : 'text-gray-500'}`}
                                    >
                                        O'rta
                                    </button>
                                    <button
                                        onClick={() => setFontSize('large')}
                                        className={`flex-1 py-1.5 text-lg rounded-md transition-colors ${fontSize === 'large' ? 'bg-white dark:bg-gray-600 shadow-sm font-medium' : 'text-gray-500'}`}
                                    >
                                        Katta
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Language & Region */}
                    <div className="card p-6">
                        <h2 className="text-xl font-bold font-heading mb-6 flex items-center gap-2">
                            <Globe className="w-5 h-5 text-primary-600" />
                            Til va Mintaqa
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Til</label>
                                <select
                                    value={language}
                                    onChange={(e) => setLanguage(e.target.value as any)}
                                    className="input"
                                >
                                    <option value="uz">O'zbekcha</option>
                                    <option value="ru">Русский</option>
                                    <option value="en">English</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Notifications */}
                    <div className="card p-6">
                        <h2 className="text-xl font-bold font-heading mb-6 flex items-center gap-2">
                            <Bell className="w-5 h-5 text-primary-600" />
                            Bildirishnomalar
                        </h2>
                        <div className="flex items-center justify-between py-2">
                            <div>
                                <div className="font-medium">Buyurtma holati</div>
                                <div className="text-sm text-gray-500">Buyurtma o'zgarishi haqida xabar olish</div>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" checked={notifications} onChange={() => setNotifications(!notifications)} className="sr-only peer" />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                            </label>
                        </div>
                    </div>

                    <div className="flex justify-end">
                        <button onClick={handleSave} className="btn btn-primary px-8">
                            Saqlash
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SettingsPage;
