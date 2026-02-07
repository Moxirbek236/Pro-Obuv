export type ProductCategory = 'tufli' | 'etik' | 'krosovka' | 'mokasima' | 'botik' | 'tapochka';

export interface Product {
    id: number;
    name: string;
    price: number;
    category: ProductCategory;
    description: string;
    image_url: string;
    available: boolean;
    stock_quantity: number;
    orders_count?: number;
    rating: number;
    discount_percentage?: number;
    sizes?: string; // comma-separated: "38,39,40,41"
    colors?: string; // comma-separated: "black,brown,white"
    is_new?: boolean;
    created_at?: string;
}

export interface ProductMedia {
    id: number;
    menu_item_id: number;
    media_type: 'image' | 'video';
    media_url: string;
    display_order: number;
    is_main: boolean;
    created_at?: string;
}

export interface ProductRating {
    id: number;
    user_id: number;
    menu_item_id: number;
    rating: number; // 1-5
    comment: string;
    created_at: string;
    user_name?: string;
}

export interface ProductFilters {
    category?: ProductCategory;
    minPrice?: number;
    maxPrice?: number;
    sizes?: string[];
    colors?: string[];
    search?: string;
    sortBy?: 'price_asc' | 'price_desc' | 'rating' | 'newest';
}
