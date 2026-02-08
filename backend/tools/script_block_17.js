
      (function () {
        // 1) Make navbar fixed (adds class to the first visible .navbar)
        try {
          const navbar = document.querySelector('.navbar');
          if (navbar) {
            // Add our safer fixed class only if not already fixed
            if (!navbar.classList.contains('fixed-top') && !navbar.classList.contains('fixed-top-custom')) {
              navbar.classList.add('fixed-top-custom');
            }

            // Compute the navbar height and add padding to main to avoid overlap
            const applyMainTopPadding = () => {
              try {
                const main = document.querySelector('main');
                if (!main) return;
                const rect = navbar.getBoundingClientRect();
                // Use Math.ceil to avoid fractional subpixel issues
                const h = Math.ceil(rect.height || 64);
                main.style.paddingTop = (h + 16) + 'px'; // keep a small breathing gap
              } catch (e) {}
            };

            // Apply immediately and on resize
            applyMainTopPadding();
            window.addEventListener('resize', applyMainTopPadding);
          }
        } catch (e) {
          // ignore
        }

        // 2) Theme - ensure default dark, provide reliable toggle that persists to server
        try {
          // Session value already written by template into localStorage earlier in the file.
          // Provide a function toggleTheme that other scripts or UI elements can call.
          window.toggleTheme = function (forceDark) {
            try {
              const isDark = typeof forceDark === 'boolean' ? forceDark : !document.body.classList.contains('dark-theme');
              if (isDark) {
                document.body.classList.add('dark-theme');
                document.body.classList.remove('light-theme');
              } else {
                document.body.classList.remove('dark-theme');
                document.body.classList.add('light-theme');
              }

              // persist locally
              try { localStorage.setItem('darkMode', isDark ? 'true' : 'false'); } catch (e) {}

              // persist to server (best-effort, non-blocking)
              fetch('/api/set-theme', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'X-CSRF-Token': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : ''
                },
                body: JSON.stringify({ theme: isDark ? 'dark' : 'light' })
              }).catch(() => {});

              // Update navbar classes for contrast
              const navbar = document.querySelector('.navbar');
              if (navbar) {
                if (isDark) {
                  navbar.classList.remove('navbar-light', 'bg-light');
                  navbar.classList.add('navbar-dark', 'bg-dark');
                } else {
                  navbar.classList.remove('navbar-dark', 'bg-dark');
                  navbar.classList.add('navbar-light', 'bg-light');
                }
              }
            } catch (e) {}
          };

          // Expose a small helper to bind toggle buttons (elements with .theme-toggle)
          document.addEventListener('click', function (e) {
            if (e.target && e.target.classList && e.target.classList.contains('theme-toggle')) {
              e.preventDefault();
              window.toggleTheme();
            }
          });
        } catch (e) {
          // ignore
        }

        // 3) News-card equalization: make all .news-item match the tallest currently rendered
        try {
          function equalizeNewsItems() {
            try {
              const items = Array.from(document.querySelectorAll('.news-ticker-content .news-item'));
              if (!items.length) return;

              // Reset heights to auto to get natural content height
              items.forEach(it => { it.style.height = 'auto'; it.style.minHeight = ''; });

              // Measure and pick the maximum
              let max = 0;
              items.forEach(it => {
                const h = it.getBoundingClientRect().height;
                if (h > max) max = h;
              });

              if (max <= 0) return;
              // Apply uniform height (use px to avoid cross-browser issues)
              items.forEach(it => { it.style.height = Math.ceil(max) + 'px'; it.style.minHeight = Math.ceil(max) + 'px'; });
            } catch (e) {}
          }

          // Run after news ticker updates or on DOMContentLoaded
          document.addEventListener('DOMContentLoaded', function () {
            // run after a short delay to allow async news load
            setTimeout(equalizeNewsItems, 300);
          });

          // Also observe the news-ticker-content for changes and re-run equalization
          const newsContainer = document.getElementById('news-ticker-content');
          if (newsContainer) {
            const mo = new MutationObserver(() => {
              // small debounce
              if (window._newsEqualizeTimer) clearTimeout(window._newsEqualizeTimer);
              window._newsEqualizeTimer = setTimeout(equalizeNewsItems, 120);
            });
            mo.observe(newsContainer, { childList: true, subtree: true, attributes: true });
          }

          // Re-run on window resize
          window.addEventListener('resize', function () {
            if (window._newsEqualizeTimer) clearTimeout(window._newsEqualizeTimer);
            window._newsEqualizeTimer = setTimeout(equalizeNewsItems, 120);
          });
        } catch (e) {
          // ignore
        }
      })();
    