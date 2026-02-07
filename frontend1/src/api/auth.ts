import apiClient from './client';
import { ApiResponse } from '@/types/api.types';
import { LoginCredentials, RegisterData, User, Staff } from '@/types/auth.types';

export const authApi = {
    // Check authentication status
    checkAuth: async (): Promise<ApiResponse<{ logged_in: boolean; user: User | Staff; role: string }>> => {
        const response = await apiClient.get('/api/auth/status');
        return response.data;
    },

    // User login
    loginUser: async (credentials: { email: string; password: string }): Promise<ApiResponse> => {
        const response = await apiClient.post('/login_page', credentials);
        return response.data;
    },

    // Staff login
    loginStaff: async (credentials: { staff_id: number; password: string }): Promise<ApiResponse> => {
        const response = await apiClient.post('/staff-secure-login-w7m2k', credentials);
        return response.data;
    },

    // Superadmin login
    loginSuperadmin: async (credentials: { username: string; password: string }): Promise<ApiResponse> => {
        const response = await apiClient.post('/super-admin-master-login-z9x4m', credentials);
        return response.data;
    },

    // User registration
    register: async (data: RegisterData): Promise<ApiResponse> => {
        const response = await apiClient.post('/register', data);
        return response.data;
    },

    // Logout
    logoutUser: async (): Promise<ApiResponse> => {
        const response = await apiClient.get('/logout');
        return response.data;
    },

    logoutStaff: async (): Promise<ApiResponse> => {
        const response = await apiClient.get('/staff/logout');
        return response.data;
    },

    logoutSuperadmin: async (): Promise<ApiResponse> => {
        const response = await apiClient.get('/super-admin/logout');
        return response.data;
    },

    // Password reset
    forgotPassword: async (email: string): Promise<ApiResponse> => {
        const response = await apiClient.post('/forgot-password', { email });
        return response.data;
    },

    resetPassword: async (token: string, newPassword: string): Promise<ApiResponse> => {
        const response = await apiClient.post('/reset-password', { token, new_password: newPassword });
        return response.data;
    },
};
