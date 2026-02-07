// Main application entry point
(function () {
    'use strict';

    // Initialize application when DOM is ready
    document.addEventListener('DOMContentLoaded', async () => {
        console.log('Safety.uz application starting...');

        // Initialize Bootstrap components if they exist
        initBootstrapComponents();

        // Auto-hide alerts after 4 seconds
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) bsAlert.close();
            }, 4000);
        });

        console.log('Application ready.');
    });

    // Helper to initialize Bootstrap tooltips and popovers
    function initBootstrapComponents() {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });

            const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
            popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
        }
    }

    // Global error handlers
    window.addEventListener('error', function (e) {
        console.error('Application error:', e.error);
    });

    window.addEventListener('unhandledrejection', function (e) {
        console.error('Unhandled promise rejection:', e.reason);
    });
})();
