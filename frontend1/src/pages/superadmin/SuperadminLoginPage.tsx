import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ShieldAlert, Key } from 'lucide-react';
import toast from 'react-hot-toast';

const SuperadminLoginPage: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            await login({ username, password }, 'superadmin');
            navigate('/super-admin-control-panel-master-z8x9k');
        } catch (error) {
            console.error('Superadmin login failed:', error);
            if (import.meta.env.DEV) {
                toast.success('Demo rejim: Muvaffaqiyatli kirdingiz');
                // In real app, proper auth check is needed
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
            {/* Abstract Background */}
            <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 z-0 pointer-events-none"></div>
            <div className="absolute w-full h-full bg-gradient-to-br from-gray-900 via-black to-gray-900 z-0"></div>

            <div className="max-w-md w-full space-y-8 z-10 bg-gray-900/80 backdrop-blur-xl p-10 rounded-xl shadow-2xl border border-gray-800">
                <div className="text-center">
                    <div className="mx-auto h-20 w-20 bg-gradient-to-b from-red-600 to-red-900 rounded-full flex items-center justify-center shadow-lg shadow-red-900/50 mb-6">
                        <ShieldAlert className="h-10 w-10 text-white" />
                    </div>
                    <h2 className="text-3xl font-heading font-bold text-white tracking-widest uppercase">
                        Master Access
                    </h2>
                    <p className="mt-2 text-xs text-red-500 font-mono tracking-widest uppercase">
                        Restricted Area • Unauthorized Access Prohibited
                    </p>
                </div>

                <form className="mt-10 space-y-6" onSubmit={handleSubmit}>
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="username" className="sr-only">Username</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <ShieldAlert className="h-5 w-5 text-gray-500 group-focus-within:text-red-500 transition-colors" />
                                </div>
                                <input
                                    id="username"
                                    name="username"
                                    type="text"
                                    required
                                    className="block w-full pl-10 pr-3 py-3 border border-gray-700 rounded-lg leading-5 bg-gray-800 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 sm:text-sm transition-colors"
                                    placeholder="Master Username"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                />
                            </div>
                        </div>
                        <div>
                            <label htmlFor="password" className="sr-only">Password</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Key className="h-5 w-5 text-gray-500 group-focus-within:text-red-500 transition-colors" />
                                </div>
                                <input
                                    id="password"
                                    name="password"
                                    type="password"
                                    required
                                    className="block w-full pl-10 pr-3 py-3 border border-gray-700 rounded-lg leading-5 bg-gray-800 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 sm:text-sm transition-colors"
                                    placeholder="Auth Token"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                            </div>
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold uppercase tracking-wider rounded-lg text-white bg-red-700 hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 focus:ring-offset-gray-900 transition-all duration-200 shadow-lg shadow-red-900/30"
                        >
                            {loading ? (
                                <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                            ) : (
                                "Execute Login"
                            )}
                        </button>
                    </div>
                </form>

                <div className="mt-6 flex justify-between text-xs text-gray-600 font-mono">
                    <span>SECURE_CONNECTION: ENCRYPTED</span>
                    <span>V.1.0.0</span>
                </div>
            </div>
        </div>
    );
};

export default SuperadminLoginPage;
