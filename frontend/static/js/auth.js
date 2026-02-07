// Authentication & User Management
class Auth {
    static STORAGE_KEY = 'safety_uz_user';

    static getCurrentUser() {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        if (stored) {
            try {
                return JSON.parse(stored);
            } catch (e) {
                return null;
            }
        }
        return null;
    }

    static setCurrentUser(userData) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(userData));
        currentUser = userData;
        this.updateUI();
    }

    static clearCurrentUser() {
        localStorage.removeItem(this.STORAGE_KEY);
        currentUser = { role: USER_ROLES.GUEST, data: null };
        this.updateUI();
    }

    static getUserRole() {
        const user = this.getCurrentUser();
        if (!user) return USER_ROLES.GUEST;

        if (user.super_admin) return USER_ROLES.SUPERADMIN;
        if (user.staff_id) return USER_ROLES.STAFF;
        if (user.courier_id) return USER_ROLES.COURIER;
        if (user.user_id) return USER_ROLES.USER;

        return USER_ROLES.GUEST;
    }

    static isLoggedIn() {
        return this.getUserRole() !== USER_ROLES.GUEST;
    }

    static hasRole(role) {
        return this.getUserRole() === role;
    }

    static async login(username, password) {
        try {
            const response = await API.login(username, password);
            if (response.success) {
                this.setCurrentUser(response.user);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Login error:', error);
            return false;
        }
    }

    static async logout() {
        try {
            await API.logout();
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.clearCurrentUser();
            window.location.href = '/';
        }
    }

    static updateUI() {
        // Update navbar based on user role
        const role = this.getUserRole();
        Components.renderNavbar(role);
        Components.renderFooter(role);
    }

    static requireAuth(role = null) {
        const currentRole = this.getUserRole();

        if (currentRole === USER_ROLES.GUEST) {
            window.location.href = '/login.html';
            return false;
        }

        if (role && currentRole !== role) {
            window.location.href = '/';
            return false;
        }

        return true;
    }
}

// Initialize user on page load
document.addEventListener('DOMContentLoaded', () => {
    const user = Auth.getCurrentUser();
    if (user) {
        currentUser = user;
        currentUser.role = Auth.getUserRole();
    }
});
