import apiClient from './client';
import { ApiResponse } from '@/types/api.types';
import { Order, PlaceOrderData } from '@/types/order.types';

export const ordersApi = {
    // Get user orders
    getOrders: async (): Promise<ApiResponse<Order[]>> => {
        const response = await apiClient.get('/api/orders');
        return response.data;
    },

    // Get single order
    getOrder: async (orderId: number): Promise<ApiResponse<Order>> => {
        const response = await apiClient.get(`/api/orders/${orderId}`);
        return response.data;
    },

    // Track order by ticket number
    trackOrder: async (ticketNo: number): Promise<ApiResponse<Order>> => {
        const response = await apiClient.get(`/order/${ticketNo}`);
        return response.data;
    },

    // Place order
    placeOrder: async (data: PlaceOrderData): Promise<ApiResponse<{ ticket_no: number; order_id: number }>> => {
        const response = await apiClient.post('/place_order', data);
        return response.data;
    },

    // Cancel order
    cancelOrder: async (ticketNo: number): Promise<ApiResponse> => {
        const response = await apiClient.post(`/user/cancel/${ticketNo}`);
        return response.data;
    },

    // Get order receipt
    getReceipt: async (ticketNo: number): Promise<ApiResponse> => {
        const response = await apiClient.get(`/receipt/${ticketNo}`);
        return response.data;
    },

    // Check order status
    checkOrderStatus: async (ticketNo: number): Promise<ApiResponse<{ status: string; eta_time?: string }>> => {
        const response = await apiClient.get(`/user/status/${ticketNo}`);
        return response.data;
    },
};
