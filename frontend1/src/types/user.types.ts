export interface UserPreferences {
    interface_language: 'uz' | 'ru' | 'en' | 'kz';
    font_size: 'small' | 'medium' | 'large';
    dark_theme: boolean;
}

export interface UserSession {
    id: string;
    device: string;
    ip_address: string;
    last_activity: string;
    is_current: boolean;
}

export interface Notification {
    id: number;
    user_id: number;
    title: string;
    message: string;
    type: string;
    is_read: boolean;
    created_at: string;
}

export interface Branch {
    id: number;
    name: string;
    address: string;
    latitude: number;
    longitude: number;
    phone: string;
    working_hours: string;
    is_active: boolean;
    delivery_radius: number;
    created_at?: string;
}

export interface News {
    id: number;
    title: string;
    content: string;
    type: 'news' | 'advertisement';
    image_url?: string;
    is_active: boolean;
    created_at: string;
}
