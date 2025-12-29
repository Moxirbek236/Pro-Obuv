/**
 * STRICT: Loop Protection and Anti-Auto-Reload System
 * This script MUST be loaded as early as possible (top of head).
 */

(function() {
    // 1. Disable all automatic reloads globally
    window.ALLOW_PAGE_RELOAD = false;
    window.DISABLE_AUTO_UPDATES = true;

    try {
        const originalReload = window.location.reload && window.location.reload.bind(window.location);

        // Safely attempt to wrap/replace window.location.reload only when allowed
        try {
            const desc = Object.getOwnPropertyDescriptor(window.location, 'reload');
            if (desc && desc.configurable === false) {
                // Cannot redefine non-configurable property in this environment.
                // Provide a fallback hook but do not throw.
                window._originalReload = originalReload;
                console.warn('[LoopProtection] reload property is non-configurable; skipping redefine.');
            } else {
                Object.defineProperty(window.location, 'reload', {
                    configurable: true,
                    writable: false,
                    value: function(forceGet) {
                        if (window.ALLOW_PAGE_RELOAD === true) {
                            console.warn('[LoopProtection] Manual reload allowed by flag.');
                            return originalReload && originalReload(forceGet);
                        }
                        console.error('[LoopProtection] CRITICAL: Blocked automatic window.location.reload() to prevent infinite loop.');
                        // Track reload attempts to detect if we're in a "ghost" loop
                        window._reloadAttempts = (window._reloadAttempts || 0) + 1;
                        if (window.showToast) {
                            window.showToast('Avtomatik yangilash to\'xtatildi (Loop proteksiyasi)', 'warning');
                        }
                    }
                });
            }
        } catch (innerErr) {
            // Defensive: don't allow redefine failures to break page initialization
            window._originalReload = originalReload;
            console.warn('[LoopProtection] Could not redefine reload, continuing safely:', innerErr);
        }

        // 2. Patch fetch to handle backend unavailability gracefully
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            return originalFetch(...args).catch(err => {
                // Check if it's a network error
                if (err instanceof TypeError && (err.message === 'Failed to fetch' || err.message.includes('network error'))) {
                    console.error('[LoopProtection] Backend Service Unavailable:', args[0]);
                    
                    if (window.showToast) {
                        window.showToast('Servis vaqtincha mavjud emas. Iltimos, keyinroq harakat qilib ko\'ring.', 'error');
                    }
                    
                    // Return a "fake" successful but empty response for some critical endpoints to prevent broken UI
                    if (args[0].includes('/api/auth/status')) {
                        return new Response(JSON.stringify({ logged_in: false, error: 'service_unavailable' }), {
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    }
                    if (args[0].includes('/api/cart-count')) {
                        return new Response(JSON.stringify({ count: 0 }), { status: 200 });
                    }
                }
                throw err;
            });
        };

        // 3. Patch setInterval/setTimeout to prevent aggressive polling when offline
        const originalSetInterval = window.setInterval;
        window.setInterval = function(fn, delay, ...args) {
            const wrappedFn = (...fnArgs) => {
                if (window.DISABLE_AUTO_UPDATES && delay < 10000) {
                     // Slow down aggressive intervals when updates are disabled
                     return;
                }
                if (!navigator.onLine && delay < 60000) {
                    return; // Stop polling when offline
                }
                return fn(...fnArgs);
            };
            return originalSetInterval(wrappedFn, delay, ...args);
        };

    } catch (e) {
        console.warn('[LoopProtection] Initialization failed:', e);
    }
})();
