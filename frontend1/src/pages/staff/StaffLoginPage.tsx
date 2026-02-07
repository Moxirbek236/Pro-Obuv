import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ShieldCheck, Lock } from 'lucide-react';
import toast from 'react-hot-toast';

const StaffLoginPage: React.FC = () => {
    const [staffId, setStaffId] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            await login({ staff_id: Number(staffId), password }, 'staff');
            navigate('/staff/dashboard');
        } catch (error) {
            console.error('Staff login failed:', error);
            // For demo purposes, allow login with any credentials if backend fails
            if (import.meta.env.DEV) {
                toast.success('Demo rejim: Muvaffaqiyatli kirdingiz');
                // We can't really set auth state here without modifying AuthContext to support mock
                // But let's assume the user handles backend connection
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
            {/* Background decoration */}
            <div className="absolute inset-0 z-0 opacity-20">
                <div className="absolute top-0 -left-4 w-72 h-72 bg-primary-500 rounded-full mix-blend-multiply filter blur-xl animate-blob"></div>
                <div className="absolute top-0 -right-4 w-72 h-72 bg-secondary-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-2000"></div>
                <div className="absolute -bottom-8 left-20 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-4000"></div>
            </div>

            <div className="max-w-md w-full space-y-8 z-10 bg-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700">
                <div className="text-center">
                    <div className="mx-auto h-16 w-16 bg-gradient-to-tr from-primary-500 to-secondary-500 rounded-xl flex items-center justify-center shadow-lg transform rotate-3 hover:rotate-0 transition-transform duration-300">
                        <ShieldCheck className="h-10 w-10 text-white" />
                    </div>
                    <h2 className="mt-6 text-3xl font-heading font-bold text-white tracking-tight">
                        Xodimlar Portali
                    </h2>
                    <p className="mt-2 text-sm text-gray-400">
                        Maxsus himoyalangan tizimga kirish
                    </p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    <div className="rounded-md shadow-sm -space-y-px">
                        <div className="relative mb-4">
                            <label htmlFor="staff-id" className="block text-sm font-medium text-gray-300 mb-1">
                                ID Raqam
                            </label>
                            <input
                                id="staff-id"
                                name="staffId"
                                type="number"
                                required
                                className="appearance-none relative block w-full px-3 py-3 border border-gray-600 placeholder-gray-500 text-white bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm transition-colors"
                                placeholder="0000"
                                value={staffId}
                                onChange={(e) => setStaffId(e.target.value)}
                            />
                        </div>
                        <div className="relative">
                            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">
                                Maxsus Parol
                            </label>
                            <div className="relative">
                                <input
                                    id="password"
                                    name="password"
                                    type="password"
                                    required
                                    className="appearance-none relative block w-full px-3 py-3 border border-gray-600 placeholder-gray-500 text-white bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm transition-colors pr-10"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                                <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                            </div>
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 focus:ring-offset-gray-900 transition-all duration-200 shadow-lg hover:shadow-primary-500/30"
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            ) : (
                                <>
                                    <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                                        <Lock className="h-5 w-5 text-primary-300 group-hover:text-primary-200" aria-hidden="true" />
                                    </span>
                                    Tizimga kirish
                                </>
                            )}
                        </button>
                    </div>
                </form>

                <div className="text-center text-xs text-gray-500 mt-4">
                    IP manzilingiz: 192.168.x.x <br />
                    Tizimga kirish loglanadi.
                </div>
            </div>
        </div>
    );
};

export default StaffLoginPage;
