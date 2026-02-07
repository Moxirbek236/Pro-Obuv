import apiClient from './client';
import { ApiResponse } from '@/types/api.types';
import { CartItem, CartSummary } from '@/types/cart.types';

export const cartApi = {
    // Get cart
    getCart: async (): Promise<ApiResponse<CartItem[]>> => {
        const response = await apiClient.get('/api/cart');
        return response.data;
    },

    // Get cart count
    getCartCount: async (): Promise<ApiResponse<{ count: number }>> => {
        const response = await apiClient.get('/api/cart-count');
        return response.data;
    },

    // Add to cart
    addToCart: async (menu_item_id: number, quantity: number = 1): Promise<ApiResponse> => {
        const response = await apiClient.post('/add_to_cart', { menu_item_id, quantity });
        return response.data;
    },

    // Remove from cart
    removeFromCart: async (cart_item_id: number): Promise<ApiResponse> => {
        const response = await apiClient.post(`/remove_from_cart/${cart_item_id}`);
        return response.data;
    },

    // Update cart item quantity
    updateCartItem: async (cart_item_id: number, quantity: number): Promise<ApiResponse> => {
        const response = await apiClient.post(`/update_cart_item/${cart_item_id}`, { quantity });
        return response.data;
    },

    // Clear cart
    clearCart: async (): Promise<ApiResponse> => {
        const response = await apiClient.post('/clear_cart');
        return response.data;
    },
};
