// Loop protection script
(function() {
    'use strict';
    
    // Prevent infinite loops
    let loopCount = 0;
    const maxLoops = 1000;
    
    const originalSetTimeout = window.setTimeout;
    const originalSetInterval = window.setInterval;
    
    window.setTimeout = function(callback, delay) {
        if (typeof callback === 'function') {
            const wrappedCallback = function() {
                loopCount++;
                if (loopCount > maxLoops) {
                    console.warn('Potential infinite loop detected');
                    return;
                }
                return callback.apply(this, arguments);
            };
            return originalSetTimeout.call(window, wrappedCallback, delay);
        }
        return originalSetTimeout.call(window, callback, delay);
    };
    
    window.setInterval = function(callback, delay) {
        if (typeof callback === 'function') {
            const wrappedCallback = function() {
                loopCount++;
                if (loopCount > maxLoops) {
                    console.warn('Potential infinite loop detected');
                    return;
                }
                return callback.apply(this, arguments);
            };
            return originalSetInterval.call(window, wrappedCallback, delay);
        }
        return originalSetInterval.call(window, callback, delay);
    };
    
    // Reset loop count periodically
    originalSetInterval(function() {
        loopCount = Math.max(0, loopCount - 100);
    }, 10000);
})();
