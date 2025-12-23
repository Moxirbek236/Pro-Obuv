document.addEventListener('DOMContentLoaded', function () {
  try {
    // Stabilize product images: lazy load, fallback, and consistent sizing
    document.querySelectorAll('.menu-item-card').forEach(function (card) {
      const imgs = Array.from(card.querySelectorAll('img'));
      imgs.forEach(function (img, idx) {
        try {
          // prefer native lazy loading
          if (!img.getAttribute('loading')) img.setAttribute('loading', 'lazy');

          // preserve original src
          if (!img.dataset.origSrc) img.dataset.origSrc = img.src || img.getAttribute('data-src') || '';

          // error fallback
          img.addEventListener('error', function () {
            try {
              if (!img.src || img.src.indexOf('defoult.webp') === -1) img.src = '/static/defoult.webp';
            } catch (e) {}
            img.classList.add('img-error');
          });

          // mark loaded
          img.addEventListener('load', function () {
            try { img.classList.add('img-loaded'); } catch (e) {}
          });

          // Prevent unexpected layout collapse from empty width/height
          if (!img.width && !img.height) {
            img.style.minWidth = img.style.minWidth || '120px';
            img.style.minHeight = img.style.minHeight || '80px';
          }

        } catch (e) {}
      });

      // Single-image cards: center and contain
      if (imgs.length === 1) {
        const img = imgs[0];
        try {
          img.style.position = 'absolute';
          img.style.top = '50%';
          img.style.left = '50%';
          img.style.transform = 'translate(-50%, -50%)';
          img.style.width = 'auto';
          img.style.maxWidth = '100%';
          img.style.height = '100%';
          img.style.objectFit = 'contain';
        } catch (e) {}
        // ensure container is not pan-mode
        const gallery = card.querySelector('.gallery');
        if (gallery && gallery.getAttribute('data-mode') === 'pan') gallery.removeAttribute('data-mode');
        card.classList.remove('multi-media');
      } else if (imgs.length > 1) {
        // Multi-image cards: ensure ribbon/pan images are visible in-flow
        card.classList.add('multi-media');
        // mark gallery to pan-mode so CSS makes images in-flow
        const gallery = card.querySelector('.gallery');
        if (gallery) gallery.setAttribute('data-mode', 'pan');
        // make sure gallery-track is flex so slides are in-flow
        const track = card.querySelector('.gallery-track, .ribbon-track');
        if (track) track.style.display = 'flex';
        // make first image active
        imgs.forEach(function (ii, j) { ii.classList.toggle('active', j === 0); ii.dataset.active = j === 0 ? 'true' : 'false'; });
        card.querySelectorAll('.gallery-track img, .ribbon-img').forEach(function (i) {
          try {
            i.style.position = i.style.position || 'relative';
            i.style.display = 'block';
            i.style.visibility = 'visible';
            i.style.opacity = i.style.opacity || '1';
          } catch (e) {}
        });
      }
    });

    // Finally, if any gallery tracks are hidden randomly, force them visible and ensure pan-mode layout
    document.querySelectorAll('.gallery-track, .ribbon-track').forEach(function (t) {
      try {
        t.style.visibility = t.style.visibility || 'visible';
        t.style.opacity = t.style.opacity || '';
        if (t.parentElement && t.parentElement.querySelectorAll('img').length > 1) {
          t.style.display = t.style.display || 'flex';
        }
      } catch (e) {}
    });
  } catch (e) {
    console.warn('menu-images stabilization failed', e);
  }
});
