// Client-side Router for SPA-like navigation
class Router {
    static routes = {
        '/': 'home',
        '/menu.html': 'menu',
        '/product.html': 'product',
        '/cart.html': 'cart',
        '/login.html': 'login',
        '/register.html': 'register',
        '/profile.html': 'profile',
        '/staff': 'staff_dashboard',
        '/courier': 'courier_dashboard',
        '/superadmin': 'superadmin_dashboard'
    };

    static init() {
        // Handle browser back/forward
        window.addEventListener('popstate', () => {
            this.loadPage(window.location.pathname);
        });

        // Intercept link clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link && link.href && link.href.startsWith(window.location.origin) && !link.hasAttribute('data-no-router')) {
                e.preventDefault();
                const path = new URL(link.href).pathname;
                this.navigate(path);
            }
        });
    }

    static navigate(path) {
        window.history.pushState({}, '', path);
        this.loadPage(path);
    }

    static async loadPage(path) {
        const mainContainer = document.getElementById('main-content');
        if (!mainContainer) return;

        // 0. Role-based route protection
        const role = Auth.getUserRole();
        if (path.startsWith('/superadmin') && role !== USER_ROLES.SUPERADMIN) {
            console.warn('Unauthorized access attempt to superadmin');
            this.navigate('/');
            return;
        }
        if (path.startsWith('/staff') && role !== USER_ROLES.STAFF && role !== USER_ROLES.SUPERADMIN) {
            this.navigate('/');
            return;
        }
        if (path.startsWith('/courier') && role !== USER_ROLES.COURIER && role !== USER_ROLES.SUPERADMIN) {
            this.navigate('/');
            return;
        }

        // Show loading
        mainContainer.innerHTML = '<div class="loading-spinner text-center my-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Yuklanmoqda...</p></div>';

        try {
            const role = Auth.getUserRole();
            const needsSidebar = ['/superadmin', '/staff', '/courier'].some(p => path.startsWith(p));

            if (needsSidebar) {
                mainContainer.classList.add('has-sidebar');
                if (!document.getElementById('sidebar-container')) {
                    const sidebarWrapper = document.createElement('div');
                    sidebarWrapper.id = 'sidebar-container';
                    mainContainer.parentElement.insertBefore(sidebarWrapper, mainContainer);
                }
                Components.renderSidebar(role);
            } else {
                mainContainer.classList.remove('has-sidebar');
                const sidebar = document.getElementById('sidebar-container');
                if (sidebar) sidebar.remove();
            }

            // Fetch HTML content from backend via fragment proxy
            let apiPath = path === '/' ? '/menu' : path;
            const fragmentUrl = `/fragment${apiPath}`;

            const content = await API.get(fragmentUrl, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            // Inject content
            mainContainer.innerHTML = content;

            // Update title if fragment provided one
            const fragTitle = mainContainer.querySelector('#fragment-title');
            if (fragTitle && fragTitle.textContent.trim()) {
                document.title = fragTitle.textContent.trim();
            }

            // Clean up metadata from DOM
            const metaDiv = mainContainer.querySelector('#fragment-metadata');
            if (metaDiv) metaDiv.remove();

            // Re-init scripts for the new content
            this.reinitPageScripts();

        } catch (error) {
            console.error('Failed to load page:', error);
            mainContainer.innerHTML = `<div class="alert alert-danger">Sahifani yuklashda xatolik yuz berdi: ${error.message}</div>`;
        }
    }

    static reinitPageScripts() {
        const scripts = document.getElementById('main-content').querySelectorAll('script');
        scripts.forEach(oldScript => {
            const newScript = document.createElement('script');
            Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
            if (oldScript.innerHTML) {
                newScript.appendChild(document.createTextNode(oldScript.innerHTML));
            }
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
    }
}
