(function () {
  // Enhanced news ticker loader with better slider functionality
  async function loadNewsTicker() {
    const container = document.getElementById('news-ticker-content');
    if (!container) return;
    try {
      const res = await fetch('/api/news');
      if (!res.ok) throw new Error('Network');
      const data = await res.json();
      const items = (data && data.news) || data || [];
      container.innerHTML = '';
      if (!items || items.length === 0) {
        const slide = document.createElement('div');
        slide.className = 'swiper-slide news-item';
        slide.innerHTML = '<div class="news-text-content"><div class="news-title">Yangiliklar topilmadi</div></div>';
        container.appendChild(slide);
        return;
      }

      // Create slides with centered content
      items.slice(0, 12).forEach(it => {
        const slide = document.createElement('div');
        slide.className = 'swiper-slide news-item';
        const rawTitle = it.localized_title || it.title_local || it.title || '';
        let title = '';
        if (typeof rawTitle === 'string') {
          title = rawTitle;
        } else if (typeof rawTitle === 'object' && rawTitle !== null) {
          // If title is a translation object, try current language
          const currentLang = document.body.getAttribute('data-language') || 'uz';
          title = rawTitle[currentLang] || Object.values(rawTitle)[0] || '';
        }
        title = String(title).substring(0, 120);
        const imageHtml = (it.image_url) ? ('<img src="' + it.image_url + '" alt="' + (title.replace(/"/g, '') || '') + '" loading="lazy"/>') : '<div class="news-image-wrapper placeholder-glow"></div>';
        slide.innerHTML = '<a class="news-slide-link" href="/news/' + (it.id || '') + '" style="display:block; width:100%; height:100%">' + imageHtml + '<div class="news-title-overlay">' + title + '</div></a>';
        container.appendChild(slide);
      });

      // Duplicate slides if there are fewer items for seamless loop
      if (items.length < 6) {
        const slidesToDuplicate = Math.ceil(6 / items.length);
        for (let i = 0; i < slidesToDuplicate; i++) {
          items.slice(0, 12).forEach(it => {
            const slide = document.createElement('div');
            slide.className = 'swiper-slide news-item';
            const rawTitle = it.localized_title || it.title_local || it.title || '';
            let title = '';
            if (typeof rawTitle === 'string') {
              title = rawTitle;
            } else if (typeof rawTitle === 'object' && rawTitle !== null) {
              const currentLang = document.body.getAttribute('data-language') || 'uz';
              title = rawTitle[currentLang] || Object.values(rawTitle)[0] || '';
            }
            title = String(title).substring(0, 120);
            const imageHtml = (it.image_url) ? ('<img src="' + it.image_url + '" alt="' + (title.replace(/"/g, '') || '') + '" loading="lazy"/>') : '<div class="news-image-wrapper placeholder-glow"></div>';
            slide.innerHTML = '<a class="news-slide-link" href="/news/' + (it.id || '') + '" style="display:block; width:100%; height:100%">' + imageHtml + '<div class="news-title-overlay">' + title + '</div></a>';
            container.appendChild(slide);
          });
        }
      }

      // Initialize enhanced swiper if available
      if (typeof Swiper !== 'undefined') {
        try {
          if (window._newsTickerSwiper) window._newsTickerSwiper.destroy(true, true);
          window._newsTickerSwiper = new Swiper('#news-ticker-swiper', {
            loop: true,
            loopedSlides: Math.max(items.length * 2, 6),
            slidesPerView: 1.2,
            spaceBetween: 16,
            centeredSlides: true,
            autoplay: {
              delay: 4000,
              disableOnInteraction: false,
              pauseOnMouseEnter: true
            },
            breakpoints: {
              480: { slidesPerView: 1.5, spaceBetween: 20 },
              768: { slidesPerView: 2.5, spaceBetween: 24 },
              1024: { slidesPerView: 3.5, spaceBetween: 30 },
              1400: { slidesPerView: 4.5, spaceBetween: 40, centeredSlides: false }
            },
            pagination: false,
            navigation: {
              nextEl: '.news-ticker-nav.next',
              prevEl: '.news-ticker-nav.prev'
            },
            effect: 'slide',
            speed: 800,
            grabCursor: true,
            slideToClickedSlide: true
          });
        } catch (e) { console.warn('Swiper init failed', e) }
      }
    } catch (e) {
      console.warn('News ticker load failed', e);
    }
  }

  // Load on DOM ready and refresh on demand
  window.addEventListener('DOMContentLoaded', loadNewsTicker);
  window.addEventListener('refreshNewsTicker', loadNewsTicker);

  // Refresh ticker every 30 seconds for fresh content
  setInterval(() => {
    if (document.visibilityState === 'visible') {
      loadNewsTicker();
    }
  }, 30000);
})();
