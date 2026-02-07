// API Helper Functions
class API {
    static async request(endpoint, options = {}) {
        const url = `${API_CONFIG.BASE_URL}${endpoint}`;

        const defaultOptions = {
            credentials: 'include', // Include cookies for session
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);

            // Handle different response types
            const contentType = response.headers.get('content-type');
            let data;

            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                throw new Error(data.error || data.message || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    static async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // Specific API methods
    static async getMenu(category = null) {
        const url = category
            ? `${API_CONFIG.ENDPOINTS.MENU}?category=${category}`
            : API_CONFIG.ENDPOINTS.MENU;
        return this.get(url);
    }

    static async getProduct(id) {
        return this.get(`${API_CONFIG.ENDPOINTS.PRODUCT}/${id}`);
    }

    static async searchProducts(query) {
        return this.get(`${API_CONFIG.ENDPOINTS.SEARCH}?q=${encodeURIComponent(query)}`);
    }

    static async getCart() {
        return this.get(API_CONFIG.ENDPOINTS.CART);
    }

    static async addToCart(productId, quantity = 1) {
        return this.post(API_CONFIG.ENDPOINTS.ADD_TO_CART, {
            item_id: productId,
            quantity: quantity
        });
    }

    static async login(username, password) {
        return this.post(API_CONFIG.ENDPOINTS.LOGIN, {
            username,
            password
        });
    }

    static async register(userData) {
        return this.post(API_CONFIG.ENDPOINTS.REGISTER, userData);
    }

    static async logout() {
        return this.post(API_CONFIG.ENDPOINTS.LOGOUT);
    }

    static async getOrders() {
        return this.get(API_CONFIG.ENDPOINTS.ORDERS);
    }

    static async getProfile() {
        return this.get(API_CONFIG.ENDPOINTS.PROFILE);
    }
}
