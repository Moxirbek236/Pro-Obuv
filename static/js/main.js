// Main application JavaScript
(function() {
    'use strict';
    
    // Initialize application
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Safety.uz application initialized');
        
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
        
        // Handle form submissions
        const forms = document.querySelectorAll('form');
        forms.forEach(function(form) {
            form.addEventListener('submit', function(e) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Yuborilmoqda...';
                    
                    // Re-enable after 5 seconds in case of error
                    setTimeout(function() {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || 'Yuborish';
                    }, 5000);
                }
            });
        });
        
        // Handle navigation
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href && href !== '#') {
                    // Add loading state
                    this.style.opacity = '0.6';
                    this.style.pointerEvents = 'none';
                }
            });
        });
        
        // Auto-hide alerts after 5 seconds
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 5000);
        });
    });
    
    // Global error handler
    window.addEventListener('error', function(e) {
        console.error('Application error:', e.error);
    });
    
    // Global unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Unhandled promise rejection:', e.reason);
    });
})();
