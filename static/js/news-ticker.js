/**
 * News Ticker Functionality (Optimized with Swiper.js)
 * Handles fetching, displaying, and cycling through news items with universal touch/mouse support.
 */

if (typeof window.NewsTicker === 'undefined') {
    window.NewsTicker = class NewsTicker {
        constructor() {
            this.container = document.getElementById('newsTickerContent');
            // Locate primary DOM nodes with fallbacks for older templates
            this.container = document.getElementById('news-ticker-content') || document.getElementById('newsTickerContent') || (document.querySelector('.news-ticker .swiper-wrapper')) || null;
            this.swiperEl = document.getElementById('news-ticker-swiper') || document.getElementById('newsTickerSwiper') || (this.container ? this.container.closest('.news-ticker') : null);
            // If we found a swiper container but not the inner wrapper, prefer querying the wrapper
            if (this.swiperEl && !this.container) {
                this.container = this.swiperEl.querySelector('.swiper-wrapper') || this.container;
            }
            this.swiper = null;
            this.items = [];

            this.init();
        }

        async init() {
            if (!this.swiperEl) return;

            await this.fetchNews();
            
            if (this.items.length > 0) {
                this.render();
                this.initSwiper();
            } else {
                this.container.innerHTML = '<div class="swiper-slide news-item">Hozircha yangiliklar yo\'q</div>';
            }
        }

        async fetchNews() {
            try {
                // Request ticker-only items so server can filter by `show_in_ticker` flag
                // MODIFIED: Removed ticker=1 to show all latest news if ticker specific news are missing
                const response = await fetch('/api/news?limit=5');
                if (!response.ok) {
                    console.warn('news-ticker: /api/news responded with', response.status);
                    this.items = [];
                    return;
                }
                let data = null;
                try {
                    data = await response.json();
                } catch (e) {
                    console.error('news-ticker: failed to parse JSON response', e);
                }
                console.debug('news-ticker: fetched', response.status, data);
                if (data && data.success) {
                    this.items = data.news || [];
                }
            } catch (error) {
                console.error('Failed to fetch news:', error);
                this.items = [];
            }
        }

        render() {
            if (!this.container) {
                console.warn('news-ticker: container not found, aborting render');
                return;
            }

            this.container.innerHTML = this.items.map((item) => {
                const title = item.title_local || item.title || '';
                const imageUrl = item.image_url || '/static/defoult.webp';
                
                return `
                    <div class="swiper-slide">
                        <a href="/news/${item.id}" 
                           class="news-item" 
                           aria-label="${title}" 
                           role="article">
                            <div class="news-image-wrapper">
                                <img src="${imageUrl}" alt="" onerror="this.src='/static/defoult.webp'">
                            </div>
                            <div class="news-text-content">
                                <span class="news-title">${title}</span>
                            </div>
                            <div class="news-link-hint">
                                <i class="bi bi-arrow-right-short"></i>
                            </div>
                        </a>
                    </div>
                `;
            }).join('');
        }

        initSwiper() {
            if (!this.swiperEl) {
                console.warn('news-ticker: swiper element not found, skipping swiper init');
                return;
            }

            if (this.items.length <= 1) {
                // Disable navigation if only one item
                const nav = this.swiperEl ? this.swiperEl.querySelectorAll('.news-nav-btn') : [];
                nav.forEach(n => n.style.display = 'none');
                return;
            }

            // Determine loop compatibility
            const maxSlidesPerView = 4; // Max configured in breakpoints
            const enableLoop = this.items.length >= maxSlidesPerView;

            this.swiper = new Swiper('#news-ticker-swiper', {
                loop: enableLoop,
                grabCursor: true,
                speed: 800,
                autoplay: {
                    delay: 5000,
                    disableOnInteraction: false,
                    pauseOnMouseEnter: true
                },
                pagination: {
                    el: '.swiper-pagination',
                    clickable: true,
                },
                navigation: {
                    nextEl: '.swiper-button-next',
                    prevEl: '.swiper-button-prev',
                },
                // Universal interaction settings
                touchEventsTarget: 'container',
                touchRatio: 1,
                touchAngle: 45,
                simulateTouch: true,
                shortSwipes: true,
                longSwipes: true,
                followFinger: true,
                preventClicks: true,
                preventClicksPropagation: true,
                
                breakpoints: {
                    // Mobile: 1 item
                    320: { 
                        slidesPerView: 1,
                        spaceBetween: 10
                    },
                    // Tablet: 2 items
                    640: { 
                        slidesPerView: 2,
                        spaceBetween: 15
                    },
                    // Desktop: 3 items
                    1024: { 
                        slidesPerView: 3,
                        spaceBetween: 20
                    },
                    // Wide: 4 items
                    1400: {
                        slidesPerView: 4,
                        spaceBetween: 25
                    }
                }
            });
        }
    };
}

document.addEventListener('DOMContentLoaded', () => {
    // If the NewsTicker class is defined in this scope, instantiate it.
    function tryInitTicker(){
        if (typeof NewsTicker === 'undefined' || typeof NewsTicker !== 'function') return;
        if (!window.Swiper) {
            // wait for Swiper lib to arrive
            console.debug('news-ticker: waiting for Swiper');
            return false;
        }
        try {
            console.debug('news-ticker: initializing NewsTicker');
            window.newsTicker = new NewsTicker();
            return true;
        } catch (e) {
            console.error('Failed to initialize NewsTicker:', e);
            return false;
        }
    }

    // Try immediately, otherwise poll until Swiper ready (5s)
    if (!tryInitTicker()) {
        const start = Date.now();
        const poll = setInterval(() => {
            if (tryInitTicker() || Date.now() - start > 5000) {
                clearInterval(poll);
            }
        }, 200);
    }
    // Retry once after a short delay if initialization failed (some scripts may error early)
    setTimeout(() => {
        if (!window.newsTicker && typeof NewsTicker === 'function') {
            try {
                console.debug('news-ticker: retry init after delay');
                window.newsTicker = new NewsTicker();
            } catch (e) {
                console.error('news-ticker: retry failed', e);
            }
        }
    }, 600);
});
