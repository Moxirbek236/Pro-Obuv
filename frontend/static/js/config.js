// API Configuration
const API_CONFIG = {
    // Backend URL - change based on environment
    BASE_URL: '', // Relative paths for monolithic setup

    // API endpoints
    ENDPOINTS: {
        // Auth
        LOGIN: '/api/login',
        REGISTER: '/api/register',
        LOGOUT: '/api/logout',

        // Menu/Products
        MENU: '/api/menu',
        PRODUCT: '/api/product',
        SEARCH: '/api/menu-search',

        // Cart
        CART: '/api/cart',
        ADD_TO_CART: '/add_to_cart',

        // Orders
        ORDERS: '/api/orders',

        // User
        PROFILE: '/api/profile',

        // Admin/Staff
        ADMIN_STATS: '/api/super-admin/reports',
        STAFF_ORDERS: '/api/staff/orders',

        // Courier
        COURIER_DELIVERIES: '/api/courier/deliveries',

        // News & Notifications
        NEWS: '/api/news',
        NOTIFICATIONS: '/api/notifications'
    }
};

// User roles
const USER_ROLES = {
    GUEST: 'guest',
    USER: 'user',
    STAFF: 'staff',
    COURIER: 'courier',
    SUPERADMIN: 'superadmin'
};

// Current user state (will be populated from session/localStorage)
let currentUser = {
    role: USER_ROLES.GUEST,
    data: null
};
