export interface CartItem {
    id: number;
    user_id?: number;
    session_id?: string;
    menu_item_id: number;
    quantity: number;
    created_at?: string;
    // Populated from product
    product_name?: string;
    product_price?: number;
    product_image?: string;
    product_available?: boolean;
}

export interface CartSummary {
    items: CartItem[];
    subtotal: number;
    delivery_price: number;
    total: number;
    item_count: number;
}
