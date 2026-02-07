import apiClient from './client';
import { ApiResponse, PaginatedResponse } from '@/types/api.types';
import { Product, ProductMedia, ProductRating, ProductFilters } from '@/types/product.types';

export const productsApi = {
    // Get all products with filters
    getProducts: async (filters?: ProductFilters & { page?: number; limit?: number }): Promise<ApiResponse<Product[]>> => {
        const params = new URLSearchParams();

        if (filters?.page) params.append('page', filters.page.toString());
        if (filters?.limit) params.append('limit', filters.limit.toString());
        if (filters?.category) params.append('category', filters.category);
        if (filters?.search) params.append('search', filters.search);

        const response = await apiClient.get(`/menu?${params.toString()}`);
        return response.data;
    },

    // Search products
    searchProducts: async (query: string): Promise<ApiResponse<Product[]>> => {
        const response = await apiClient.get(`/api/menu-search?q=${encodeURIComponent(query)}`);
        return response.data;
    },

    // Get single product
    getProduct: async (id: number): Promise<ApiResponse<Product>> => {
        const response = await apiClient.get(`/product/${id}`);
        return response.data;
    },

    // Get product media
    getProductMedia: async (id: number): Promise<ApiResponse<ProductMedia[]>> => {
        const response = await apiClient.get(`/api/product-media/${id}`);
        return response.data;
    },

    // Get product ratings
    getProductRatings: async (id: number): Promise<ApiResponse<{ ratings: ProductRating[]; average: number }>> => {
        const response = await apiClient.get(`/api/get-menu-ratings/${id}`);
        return response.data;
    },

    // Submit rating
    submitRating: async (data: { menu_item_id: number; rating: number; comment: string }): Promise<ApiResponse> => {
        const response = await apiClient.post('/api/submit-rating', data);
        return response.data;
    },

    // Get categories
    getCategories: async (): Promise<ApiResponse<{ id: number; name: string }[]>> => {
        const response = await apiClient.get('/api/categories');
        return response.data;
    },
};
