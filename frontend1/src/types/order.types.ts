export type OrderStatus = 'pending' | 'approved' | 'ready' | 'in_delivery' | 'delivered' | 'cancelled';
export type OrderType = 'dine_in' | 'delivery';

export interface Order {
    id: number;
    user_id: number;
    customer_name: string;
    ticket_no: number;
    order_type: OrderType;
    status: OrderStatus;
    delivery_address?: string;
    delivery_distance?: number;
    delivery_price?: number;
    delivery_latitude?: number;
    delivery_longitude?: number;
    customer_note?: string;
    customer_phone: string;
    card_number?: string;
    courier_id?: number;
    courier_price?: number;
    courier_delivery_minutes?: number;
    branch_id?: number;
    created_at: string;
    eta_time?: string;
    items?: OrderDetail[];
    total_price?: number;
}

export interface OrderDetail {
    id: number;
    order_id: number;
    menu_item_id: number;
    quantity: number;
    price: number;
    product_name?: string;
    product_image?: string;
}

export interface PlaceOrderData {
    order_type: OrderType;
    delivery_address?: string;
    delivery_latitude?: number;
    delivery_longitude?: number;
    customer_phone: string;
    customer_note?: string;
    card_number?: string;
}
