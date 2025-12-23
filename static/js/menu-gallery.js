(function () {
  // card-gallery module: interactive horizontal ribbon with seamless loop
  // - vanilla JS
  // - non-polluting (IIFE)
  // - responsive, touch & keyboard support
  // - lazy loads images from data-src attributes

  function qs(sel, el) { return (el || document).querySelector(sel); }
  function qsa(sel, el) { return Array.from((el || document).querySelectorAll(sel)); }

  function initGallery(el) {
    try {
      const viewport = qs('.gallery-viewport', el);
      const track = qs('.gallery-track', el);
      if (!viewport || !track) return;

      // Collect images (may be populated via data-src). We'll duplicate the track
      // and then populate actual `src` attributes to ensure duplication contains URLs.
      const initialImgs = qsa('img.gallery-item', track);
      if (initialImgs.length === 0) return;

      // If there's only one image, don't initialize the ribbon/looping behavior.
      // Keep the single image static and visible to avoid transform/translation issues.
      const itemCount = initialImgs.length;
      if (itemCount === 1) {
        const img = initialImgs[0];
        try {
          const ds = img.getAttribute('data-src');
          if (!img.src && ds) img.src = ds;
          img.style.objectFit = 'contain';
          img.style.width = '100%';
          img.style.height = '100%';
          img.style.flex = '0 0 100%';
          img.style.opacity = '1';
          img.style.visibility = 'visible';
        } catch (e) {}
        // ensure track has no transforms and is visible
        try {
          track.style.transform = 'none';
          track.style.transition = 'none';
          track.style.display = 'block';
          track.style.willChange = 'auto';
          track.style.opacity = '1';
        } catch (e) {}
        return;
      }

      // Duplicate images 3x to enable seamless looping
      const originalHTML = track.innerHTML;
      track.innerHTML = originalHTML + originalHTML + originalHTML;
      let viewportW = viewport.clientWidth;
      let imageW = 0; // will be computed in onResize
      let baseWidth = 0; // init 0 to avoid early transforms
      // logical position must be declared before any early transform attempts
      let logical = 0;
      let target = 0;
      let last = performance.now();
      let pointerActive = false;

      // Apply necessary styles to track (inline for isolation)
      track.style.display = 'flex';
      // ensure no transform is applied before sizes are measured
      track.style.transform = 'translate3d(0,0,0)';
      // Use natural sizing via flex-basis on images; do not set percent width here
      track.style.transition = 'transform 0.12s linear';
      track.style.willChange = 'transform';

      const allImgs = qsa('img.gallery-item', track);
      // Ensure all duplicated imgs have their `src` set (use data-src fallback)
      // NOTE: don't assign pixel widths here — imageW is 0 until we measure.
      // Assign a neutral flexible layout and fade images in after sizing to avoid
      // initial collapse/left-shift on page refresh.
      allImgs.forEach(img => {
        const ds = img.getAttribute('data-src');
        if (!img.src && ds) img.src = ds;
        img.style.objectFit = 'cover';
        img.draggable = false;
        img.style.minWidth = '0';
        img.style.height = '100%';
        img.style.flex = '0 0 auto';
        img.style.margin = '0';
        img.style.opacity = '0';
        img.style.transition = 'opacity 160ms linear';
        // Robust error fallback: if image fails, replace with default placeholder
        img.addEventListener('error', function () {
          try {
            if (this.getAttribute('data-fallback') !== '1') {
              this.setAttribute('data-fallback', '1');
              this.src = '/static/defoult.webp';
            }
          } catch (e) {}
        });
      });

      // Keep track hidden visually until we compute sizes to avoid early layout jumps.
      try {
        track.style.visibility = 'visible';
        track.style.opacity = '0';
        track.style.transition = 'opacity 160ms linear';
      } catch (e) {}

      // When the first original image loads (or errors), recompute sizes and reset transforms
      try {
        const firstOriginal = initialImgs[0];
        if (firstOriginal) {
          const onFirstReady = function () {
            try {
              onResize();
              // now that sizes are known, initialize logical/target and set transform
              logical = 0; target = 0;
              setTransformFromLogical();
              // reveal track and fade in images now that sizing is stable
              try { track.style.opacity = '1'; } catch (e) {}
              const updatedImgs = qsa('img.gallery-item', track);
              updatedImgs.forEach(img => { img.style.opacity = '1'; });
            } catch (e) {}
          };
          if (firstOriginal.complete && firstOriginal.naturalWidth > 0) {
            onFirstReady();
          } else {
            firstOriginal.addEventListener('load', onFirstReady, {once: true});
            firstOriginal.addEventListener('error', onFirstReady, {once: true});
          }
        }
      } catch (e) {}

      // Create indicators
      const indicators = el.querySelector('.gallery-indicators');
      if (indicators) {
        indicators.innerHTML = '';
        for (let i = 0; i < itemCount; i++) {
          const dot = document.createElement('button');
          dot.type = 'button';
          dot.className = 'gallery-dot';
          dot.dataset.idx = i;
          dot.setAttribute('aria-label', 'Show image ' + (i + 1));
          indicators.appendChild(dot);
        }
      }

      // Resize handler
      function onResize() {
        viewportW = viewport.clientWidth;
        imageW = viewportW;
        baseWidth = imageW * itemCount;
        // update sizes for all duplicated images (now that we know imageW)
        const updatedImgs = qsa('img.gallery-item', track);
        updatedImgs.forEach(img => {
          img.style.width = imageW + 'px';
          img.style.flex = '0 0 ' + imageW + 'px';
        });
      }
      window.addEventListener('resize', onResize);

      // Logical position within baseWidth handled earlier

      function setTransformFromLogical() {
        if (!baseWidth) return;
        // place inside the middle copy to avoid edge artifacts
        const pos = ((logical % baseWidth) + baseWidth) % baseWidth;
        const actual = pos + baseWidth; // center copy
        // use translate3d for GPU acceleration
        track.style.transform = `translate3d(${-actual}px,0,0)`;
      }

      // Mouse/pointer mapping: left-> ribbon moves right (we invert mapping so
      // mouse right means ribbon goes left visually)
      el.addEventListener('pointerenter', function () { pointerActive = true; });
      el.addEventListener('pointerleave', function () {
        pointerActive = false;
        // smooth return to first image on leave
        target = 0;
      });
      el.addEventListener('pointermove', function (ev) {
        try {
          const r = el.getBoundingClientRect();
          const x = Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width));
          // map 0..1 to 0..baseWidth (mouse at right -> target large -> translate more left)
          target = x * baseWidth;
        } catch (e) {}
      });

      // Touch support: map touch X to target, also allow drag
      let touchStartX = 0; let touchStartTarget = 0; let isTouchDragging = false;
      el.addEventListener('touchstart', function (ev) {
        const t = ev.touches && ev.touches[0];
        if (!t) return;
        isTouchDragging = true;
        touchStartX = t.clientX;
        touchStartTarget = target;
      }, {passive:true});
      el.addEventListener('touchmove', function (ev) {
        if (!isTouchDragging) return;
        const t = ev.touches && ev.touches[0]; if (!t) return;
        const dx = t.clientX - touchStartX;
        // move logical proportionally (invert to match pointer mapping)
        const r = el.getBoundingClientRect();
        const pct = Math.max(-1, Math.min(1, dx / r.width));
        target = (touchStartTarget - pct * baseWidth + baseWidth * 1000) % baseWidth;
      }, {passive:true});
      el.addEventListener('touchend', function () { isTouchDragging = false; });

      // Keyboard support when card is focused
      el.addEventListener('keydown', function (ev) {
        if (ev.key === 'ArrowLeft' || ev.key === 'ArrowRight') {
          ev.preventDefault();
          const dir = (ev.key === 'ArrowLeft') ? -1 : 1;
          target = (target + dir * imageW * 0.9 + baseWidth) % baseWidth;
        }
      });

      // Indicator click
      if (indicators) {
        indicators.addEventListener('click', function (ev) {
          const btn = ev.target.closest('.gallery-dot');
          if (!btn) return;
          const idx = parseInt(btn.dataset.idx, 10) || 0;
          target = idx * imageW;
        });
      }

      // Animation loop using rAF with stable easing
      function tick(now) {
        const dt = Math.max(0, Math.min(0.05, (now - last) / 1000));
        last = now;
        // ease towards target (lower factor = smoother)
        const ease = 0.12;
        logical += (target - logical) * ease;
        setTransformFromLogical();

        // update active dot (derived from logical position)
        if (indicators && baseWidth && imageW) {
          const pos = ((logical % baseWidth) + baseWidth) % baseWidth;
          const cur = Math.floor(pos / imageW) % itemCount;
          const dots = qsa('.gallery-dot', indicators);
          dots.forEach((d, i) => d.classList.toggle('active', i === cur));
        }

        requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);

      // initial placement: center on 0 (first image)
      logical = 0; target = 0; setTransformFromLogical();

    } catch (e) {
      console.warn('menu-gallery init error', e);
    }
  }

  function initAll() {
    qsa('.card-gallery').forEach(initGallery);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initAll);
  else initAll();
})();
