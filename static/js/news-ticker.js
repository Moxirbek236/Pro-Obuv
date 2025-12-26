/**
 * News Ticker Functionality (Optimized with Swiper.js)
 * Handles fetching, displaying, and cycling through news items with universal touch/mouse support.
 */

class NewsTicker {
    constructor() {
        this.container = document.getElementById('newsTickerContent');
        this.swiperEl = document.getElementById('newsTickerSwiper');
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
            const response = await fetch('/api/news?active=1&limit=5');
            const data = await response.json();
            if (data && data.success) {
                this.items = data.news || [];
            }
        } catch (error) {
            console.error('Failed to fetch news:', error);
            this.items = [];
        }
    }

    render() {
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
        if (this.items.length <= 1) {
            // Disable navigation if only one item
            const nav = this.swiperEl.querySelectorAll('.news-nav-btn');
            nav.forEach(n => n.style.display = 'none');
            return;
        }

        this.swiper = new Swiper('#newsTickerSwiper', {
            loop: true,
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
                // Adaptive settings if needed
                320: { spaceBetween: 10 },
                1024: { spaceBetween: 20 }
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.newsTicker = new NewsTicker();
});
