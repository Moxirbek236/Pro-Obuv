import apiClient from './client';
import { ApiResponse } from '@/types/api.types';
import { User, UserPreferences, UserSession, Notification } from '@/types/user.types';

export const usersApi = {
    // Get user profile
    getProfile: async (): Promise<ApiResponse<User>> => {
        const response = await apiClient.get('/profile');
        return response.data;
    },

    // Update profile
    updateProfile: async (data: Partial<User>): Promise<ApiResponse> => {
        const response = await apiClient.post('/update_profile', data);
        return response.data;
    },

    // Update address
    updateAddress: async (data: { address: string; address_latitude?: number; address_longitude?: number }): Promise<ApiResponse> => {
        const response = await apiClient.post('/update_address', data);
        return response.data;
    },

    // Change password
    changePassword: async (oldPassword: string, newPassword: string): Promise<ApiResponse> => {
        const response = await apiClient.post('/change_password', { old_password: oldPassword, new_password: newPassword });
        return response.data;
    },

    // Favorites
    getFavorites: async (): Promise<ApiResponse> => {
        const response = await apiClient.get('/favorites');
        return response.data;
    },

    addToFavorites: async (menuItemId: number): Promise<ApiResponse> => {
        const response = await apiClient.post(`/add-to-favorites/${menuItemId}`);
        return response.data;
    },

    removeFromFavorites: async (menuItemId: number): Promise<ApiResponse> => {
        const response = await apiClient.post(`/remove-from-favorites/${menuItemId}`);
        return response.data;
    },

    // User preferences
    setLanguage: async (language: 'uz' | 'ru' | 'en' | 'kz'): Promise<ApiResponse> => {
        const response = await apiClient.post('/api/set-language', { language });
        return response.data;
    },

    setTheme: async (theme: 'dark' | 'light'): Promise<ApiResponse> => {
        const response = await apiClient.post('/api/set-theme', { theme });
        return response.data;
    },

    setFontSize: async (fontSize: 'small' | 'medium' | 'large'): Promise<ApiResponse> => {
        const response = await apiClient.post('/api/set-font-size', { font_size: fontSize });
        return response.data;
    },

    // Sessions
    getSessions: async (): Promise<ApiResponse<UserSession[]>> => {
        const response = await apiClient.get('/api/user-sessions');
        return response.data;
    },

    terminateSession: async (sessionId: string): Promise<ApiResponse> => {
        const response = await apiClient.post('/api/terminate-session', { session_id: sessionId });
        return response.data;
    },

    terminateAllSessions: async (): Promise<ApiResponse> => {
        const response = await apiClient.post('/api/terminate-all-sessions');
        return response.data;
    },

    // Notifications
    getNotifications: async (): Promise<ApiResponse<Notification[]>> => {
        const response = await apiClient.get('/api/notifications');
        return response.data;
    },

    markNotificationRead: async (notificationId: number): Promise<ApiResponse> => {
        const response = await apiClient.post(`/api/notifications/${notificationId}/read`);
        return response.data;
    },
};
