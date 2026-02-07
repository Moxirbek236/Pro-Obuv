import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '@/api/auth';
import { AuthContextType, AuthState, LoginCredentials, RegisterData, User, Staff, UserRole } from '@/types/auth.types';
import toast from 'react-hot-toast';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [state, setState] = useState<AuthState>({
        isAuthenticated: false,
        user: null,
        role: 'guest',
        loading: true,
    });

    // Check authentication status on mount
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const response = await authApi.checkAuth();

            if (response.success && response.data?.logged_in) {
                setState({
                    isAuthenticated: true,
                    user: response.data.user,
                    role: response.data.role as UserRole,
                    loading: false,
                });
            } else {
                setState({
                    isAuthenticated: false,
                    user: null,
                    role: 'guest',
                    loading: false,
                });
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            setState({
                isAuthenticated: false,
                user: null,
                role: 'guest',
                loading: false,
            });
        }
    };

    const login = async (credentials: LoginCredentials, roleType: 'user' | 'staff' | 'superadmin') => {
        try {
            let response;

            if (roleType === 'user' && credentials.email) {
                response = await authApi.loginUser({
                    email: credentials.email,
                    password: credentials.password,
                });
            } else if (roleType === 'staff' && credentials.staff_id) {
                response = await authApi.loginStaff({
                    staff_id: credentials.staff_id,
                    password: credentials.password,
                });
            } else if (roleType === 'superadmin' && credentials.username) {
                response = await authApi.loginSuperadmin({
                    username: credentials.username,
                    password: credentials.password,
                });
            } else {
                throw new Error('Invalid credentials for role type');
            }

            if (response.success) {
                toast.success('Muvaffaqiyatli kirdingiz!');
                await checkAuth(); // Refresh auth state
            } else {
                toast.error(response.message || 'Login xatolik yuz berdi');
            }
        } catch (error: any) {
            console.error('Login error:', error);
            toast.error(error.response?.data?.message || 'Login xatolik yuz berdi');
            throw error;
        }
    };

    const logout = async () => {
        try {
            if (state.role === 'user') {
                await authApi.logoutUser();
            } else if (state.role === 'staff') {
                await authApi.logoutStaff();
            } else if (state.role === 'superadmin') {
                await authApi.logoutSuperadmin();
            }

            setState({
                isAuthenticated: false,
                user: null,
                role: 'guest',
                loading: false,
            });

            toast.success('Tizimdan chiqdingiz');
        } catch (error) {
            console.error('Logout error:', error);
            toast.error('Chiqishda xatolik yuz berdi');
        }
    };

    const register = async (data: RegisterData) => {
        try {
            const response = await authApi.register(data);

            if (response.success) {
                toast.success('Ro\'yxatdan o\'tdingiz! Iltimos, tizimga kiring.');
            } else {
                toast.error(response.message || 'Ro\'yxatdan o\'tishda xatolik');
            }
        } catch (error: any) {
            console.error('Registration error:', error);
            toast.error(error.response?.data?.message || 'Ro\'yxatdan o\'tishda xatolik');
            throw error;
        }
    };

    const value: AuthContextType = {
        ...state,
        login,
        logout,
        register,
        checkAuth,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
