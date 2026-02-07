import { ProductCategory } from '@/types/product.types';
import { OrderStatus } from '@/types/order.types';
import { UserRole } from '@/types/auth.types';

// App constants
export const APP_NAME = 'Safety.uz';
export const APP_VERSION = '1.0.0';

// API constants
export const API_TIMEOUT = 30000; // 30 seconds
export const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// Product categories
export const PRODUCT_CATEGORIES: Record<ProductCategory, string> = {
    tufli: 'Tufli',
    etik: 'Etik',
    krosovka: 'Krosovka',
    mokasima: 'Mokasima',
    botik: 'Botik',
    tapochka: 'Tapochka',
};

// Order statuses
export const ORDER_STATUSES: Record<OrderStatus, { label: string; color: string }> = {
    pending: { label: 'Kutilmoqda', color: 'yellow' },
    approved: { label: 'Tasdiqlangan', color: 'blue' },
    ready: { label: 'Tayyor', color: 'purple' },
    in_delivery: { label: 'Yetkazilmoqda', color: 'indigo' },
    delivered: { label: 'Yetkazildi', color: 'green' },
    cancelled: { label: 'Bekor qilindi', color: 'red' },
};

// User roles
export const USER_ROLES: Record<UserRole, string> = {
    guest: 'Mehmon',
    user: 'Foydalanuvchi',
    staff: 'Xodim',
    superadmin: 'Superadmin',
};

// Languages
export const LANGUAGES = [
    { code: 'uz', name: 'O\'zbekcha', flag: '🇺🇿' },
    { code: 'ru', name: 'Русский', flag: '🇷🇺' },
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'kz', name: 'Қазақша', flag: '🇰🇿' },
];

// Font sizes
export const FONT_SIZES = [
    { value: 'small', label: 'Kichik' },
    { value: 'medium', label: 'O\'rta' },
    { value: 'large', label: 'Katta' },
];

// Theme options
export const THEMES = [
    { value: 'light', label: 'Yorug\'', icon: '☀️' },
    { value: 'dark', label: 'Qorong\'i', icon: '🌙' },
];

// Payment methods
export const PAYMENT_METHODS = [
    { id: 'click', name: 'Click', icon: '/icons/click.png' },
    { id: 'payme', name: 'Payme', icon: '/icons/payme.png' },
    { id: 'cash', name: 'Naqd pul', icon: '💵' },
];

// Social media links
export const SOCIAL_LINKS = {
    telegram: 'https://t.me/safetyuz',
    instagram: 'https://instagram.com/safety.uz',
    facebook: 'https://facebook.com/safety.uz',
    youtube: 'https://youtube.com/@safetyuz',
};

// Contact info
export const CONTACT_INFO = {
    phone: '+998 90 123 45 67',
    email: 'info@safety.uz',
    address: 'Toshkent, O\'zbekiston',
};

// Routes
export const ROUTES = {
    HOME: '/',
    MENU: '/menu',
    PRODUCT: '/product',
    ABOUT: '/about',
    CONTACT: '/contact',
    NEWS: '/news',
    DOWNLOADS: '/downloads',
    LOGIN: '/login',
    REGISTER: '/register',
    FORGOT_PASSWORD: '/forgot',

    // User routes
    PROFILE: '/profile',
    CART: '/cart',
    FAVORITES: '/favorites',
    USER_DASHBOARD: '/user',
    SETTINGS: '/settings',

    // Staff routes
    STAFF_LOGIN: '/staff-secure-login-w7m2k',
    STAFF_DASHBOARD: '/staff/dashboard',
    STAFF_MENU: '/staff/menu',
    STAFF_CHAT: '/staff/chat',

    // Superadmin routes
    SUPERADMIN_LOGIN: '/super-admin-master-login-z9x4m',
    SUPERADMIN_DASHBOARD: '/super-admin-control-panel-master-z8x9k',
    SUPERADMIN_ANALYTICS: '/super-admin/analytics',
    SUPERADMIN_REPORTS: '/super-admin/reports',
    SUPERADMIN_SYSTEM: '/super-admin/system',
    SUPERADMIN_LOGS: '/super-admin/logs',
};

// Local storage keys
export const STORAGE_KEYS = {
    LANGUAGE: 'safety_uz_language',
    THEME: 'safety_uz_theme',
    FONT_SIZE: 'safety_uz_font_size',
    CART: 'safety_uz_cart',
    AUTH_CHECKED: 'auth_checked',
};

// Regex patterns
export const REGEX = {
    EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    PHONE: /^(\+998|998)?[0-9]{9}$/,
    CARD_NUMBER: /^\d{16}$/,
};
