export type UserRole = 'guest' | 'user' | 'staff' | 'superadmin';

export interface User {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    phone: string;
    address?: string;
    address_latitude?: number;
    address_longitude?: number;
    interface_language?: 'uz' | 'ru' | 'en' | 'kz';
    font_size?: 'small' | 'medium' | 'large';
    dark_theme?: boolean;
    avatar?: string;
}

export interface Staff {
    id: number;
    first_name: string;
    last_name: string;
    phone: string;
    total_hours?: number;
    orders_handled?: number;
    last_activity?: string;
}

export interface AuthState {
    isAuthenticated: boolean;
    user: User | Staff | null;
    role: UserRole;
    loading: boolean;
}

export interface LoginCredentials {
    email?: string;
    password: string;
    staff_id?: number;
    username?: string;
}

export interface RegisterData {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone: string;
    address?: string;
    address_latitude?: number;
    address_longitude?: number;
}

export interface AuthContextType extends AuthState {
    login: (credentials: LoginCredentials, roleType: 'user' | 'staff' | 'superadmin') => Promise<void>;
    logout: () => Promise<void>;
    register: (data: RegisterData) => Promise<void>;
    checkAuth: () => Promise<void>;
}
