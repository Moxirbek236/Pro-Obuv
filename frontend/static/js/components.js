// UI Components - Role-based rendering
class Components {
    // Render Navbar based on user role
    static renderNavbar(role = USER_ROLES.GUEST) {
        const container = document.getElementById('navbar-container');
        if (!container) return;

        let navHTML = '';

        switch (role) {
            case USER_ROLES.SUPERADMIN:
                navHTML = this.getSuperadminNavbar();
                break;
            case USER_ROLES.STAFF:
                navHTML = this.getStaffNavbar();
                break;
            case USER_ROLES.COURIER:
                navHTML = this.getCourierNavbar();
                break;
            case USER_ROLES.USER:
                navHTML = this.getUserNavbar();
                break;
            default:
                navHTML = this.getGuestNavbar();
        }

        container.innerHTML = navHTML;
        this.attachNavbarEvents();
    }

    // Guest Navbar
    static getGuestNavbar() {
        return `
            <nav class="navbar">
                <div class="container">
                    <a href="/" class="logo">Safety.uz</a>
                    <ul class="nav-menu">
                        <li><a href="/">Bosh sahifa</a></li>
                        <li><a href="/menu.html">Mahsulotlar</a></li>
                        <li><a href="/about.html">Biz haqimizda</a></li>
                        <li><a href="/contact.html">Aloqa</a></li>
                        <li><a href="/login.html" class="btn-primary">Kirish</a></li>
                    </ul>
                </div>
            </nav>
        `;
    }

    // User Navbar
    static getUserNavbar() {
        const user = Auth.getCurrentUser();
        return `
            <nav class="navbar">
                <div class="container">
                    <a href="/" class="logo">Safety.uz</a>
                    <ul class="nav-menu">
                        <li><a href="/">Bosh sahifa</a></li>
                        <li><a href="/menu.html">Mahsulotlar</a></li>
                        <li><a href="/cart.html">Savat</a></li>
                        <li><a href="/profile.html">Profil</a></li>
                        <li><a href="#" onclick="Auth.logout()">Chiqish</a></li>
                    </ul>
                </div>
            </nav>
        `;
    }

    // Staff Navbar
    static getStaffNavbar() {
        return `
            <nav class="navbar navbar-staff">
                <div class="container">
                    <a href="/staff" class="logo">Safety.uz - Xodim</a>
                    <ul class="nav-menu">
                        <li><a href="/staff">Dashboard</a></li>
                        <li><a href="/staff/orders.html">Buyurtmalar</a></li>
                        <li><a href="/staff/menu.html">Menyu</a></li>
                        <li><a href="#" onclick="Auth.logout()">Chiqish</a></li>
                    </ul>
                </div>
            </nav>
        `;
    }

    // Courier Navbar
    static getCourierNavbar() {
        return `
            <nav class="navbar navbar-courier">
                <div class="container">
                    <a href="/courier" class="logo">Safety.uz - Kuryer</a>
                    <ul class="nav-menu">
                        <li><a href="/courier">Dashboard</a></li>
                        <li><a href="/courier/deliveries.html">Yetkazishlar</a></li>
                        <li><a href="#" onclick="Auth.logout()">Chiqish</a></li>
                    </ul>
                </div>
            </nav>
        `;
    }

    // Superadmin Navbar (NO FOOTER!)
    static getSuperadminNavbar() {
        return `
            <nav class="navbar navbar-admin">
                <div class="container">
                    <a href="/superadmin" class="logo">Safety.uz - Admin Panel</a>
                    <ul class="nav-menu">
                        <li><a href="/superadmin">Dashboard</a></li>
                        <li><a href="/superadmin/reports.html">Hisobotlar</a></li>
                        <li><a href="/superadmin/staff.html">Xodimlar</a></li>
                        <li><a href="/superadmin/settings.html">Sozlamalar</a></li>
                        <li><a href="#" onclick="Auth.logout()">Chiqish</a></li>
                    </ul>
                </div>
            </nav>
        `;
    }

    // Render Footer based on user role
    static renderFooter(role = USER_ROLES.GUEST) {
        const container = document.getElementById('footer-container');
        if (!container) return;

        // SUPERADMIN DOES NOT GET FOOTER!
        if (role === USER_ROLES.SUPERADMIN) {
            container.innerHTML = '';
            return;
        }

        // Staff and Courier get minimal footer
        if (role === USER_ROLES.STAFF || role === USER_ROLES.COURIER) {
            container.innerHTML = this.getMinimalFooter();
            return;
        }

        // Guest and User get full footer
        container.innerHTML = this.getFullFooter();
    }

    static getFullFooter() {
        return `
            <footer class="footer">
                <div class="container">
                    <div class="footer-content">
                        <div class="footer-section">
                            <h3>Safety.uz</h3>
                            <p>Sifatli spetsobuv va ish kiyimlari</p>
                        </div>
                        <div class="footer-section">
                            <h4>Havolalar</h4>
                            <ul>
                                <li><a href="/menu.html">Mahsulotlar</a></li>
                                <li><a href="/about.html">Biz haqimizda</a></li>
                                <li><a href="/contact.html">Aloqa</a></li>
                            </ul>
                        </div>
                        <div class="footer-section">
                            <h4>Aloqa</h4>
                            <p>Tel: +998 90 123 45 67</p>
                            <p>Email: info@safety.uz</p>
                        </div>
                    </div>
                    <div class="footer-bottom">
                        <p>&copy; 2026 Safety.uz. Barcha huquqlar himoyalangan.</p>
                    </div>
                </div>
            </footer>
        `;
    }

    static getMinimalFooter() {
        return `
            <footer class="footer footer-minimal">
                <div class="container">
                    <p>&copy; 2026 Safety.uz</p>
                </div>
            </footer>
        `;
    }

    static attachNavbarEvents() {
        // Add any interactive navbar functionality here
    }

    // Sidebar for admin/staff/courier
    static renderSidebar(role) {
        const container = document.getElementById('sidebar-container');
        if (!container) return;

        let sidebarHTML = '';

        switch (role) {
            case USER_ROLES.SUPERADMIN:
                sidebarHTML = this.getSuperadminSidebar();
                break;
            case USER_ROLES.STAFF:
                sidebarHTML = this.getStaffSidebar();
                break;
            case USER_ROLES.COURIER:
                sidebarHTML = this.getCourierSidebar();
                break;
        }

        container.innerHTML = sidebarHTML;
    }

    static getSuperadminSidebar() {
        return `
            <aside class="sidebar sidebar-admin">
                <ul class="sidebar-menu">
                    <li><a href="/superadmin"><i class="icon-dashboard"></i> Dashboard</a></li>
                    <li><a href="/superadmin/orders.html"><i class="icon-orders"></i> Buyurtmalar</a></li>
                    <li><a href="/superadmin/products.html"><i class="icon-products"></i> Mahsulotlar</a></li>
                    <li><a href="/superadmin/staff.html"><i class="icon-staff"></i> Xodimlar</a></li>
                    <li><a href="/superadmin/couriers.html"><i class="icon-courier"></i> Kuryerlar</a></li>
                    <li><a href="/superadmin/reports.html"><i class="icon-reports"></i> Hisobotlar</a></li>
                    <li><a href="/superadmin/settings.html"><i class="icon-settings"></i> Sozlamalar</a></li>
                </ul>
            </aside>
        `;
    }

    static getStaffSidebar() {
        return `
            <aside class="sidebar sidebar-staff">
                <ul class="sidebar-menu">
                    <li><a href="/staff"><i class="icon-dashboard"></i> Dashboard</a></li>
                    <li><a href="/staff/orders.html"><i class="icon-orders"></i> Buyurtmalar</a></li>
                    <li><a href="/staff/menu.html"><i class="icon-menu"></i> Menyu</a></li>
                </ul>
            </aside>
        `;
    }

    static getCourierSidebar() {
        return `
            <aside class="sidebar sidebar-courier">
                <ul class="sidebar-menu">
                    <li><a href="/courier"><i class="icon-dashboard"></i> Dashboard</a></li>
                    <li><a href="/courier/deliveries.html"><i class="icon-delivery"></i> Yetkazishlar</a></li>
                </ul>
            </aside>
        `;
    }
}
