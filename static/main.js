// main.js — trimmed, single copy, safe fallbacks
// Purpose: minimal global behaviors required by templates:
// - openItemModal fallback (navigates to /product/<id> when modal absent)
// - attachCardHandlers for add-to-cart buttons
// - MenuClient minimal fetch & render with card click navigating to /product/<id>
// - CartManager with cart count updater
// - Small utilities: formatPrice, escapeHtml, renderStars, showNotification

/* globals fetch, document, window */

let cartCount = 0;
window.currentPath = window.currentPath || window.location.pathname;

// --- Utilities ---
function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatPrice(price) {
  try {
    return new Intl.NumberFormat("uz-UZ", {
      style: "currency",
      currency: "UZS",
      minimumFractionDigits: 0,
    }).format(price);
  } catch (e) {
    return String(price || 0);
  }
}

function renderStars(rating) {
  const r = Math.max(0, Math.round(Number(rating) || 0));
  let s = "";
  for (let i = 1; i <= 5; i++) {
    s += `<span class=\"star${i <= r ? " filled" : ""}\">⭐</span>`;
  }
  return s;
}

function showNotification(message, type = "info") {
  // Minimal toast — non-intrusive
  try {
    const id = "toast-container";
    let container = document.getElementById(id);
    if (!container) {
      container = document.createElement("div");
      container.id = id;
      container.style.position = "fixed";
      container.style.right = "16px";
      container.style.bottom = "16px";
      container.style.zIndex = 99999;
      container.style.display = "flex";
      container.style.flexDirection = "column";
      container.style.gap = "8px";
      document.body.appendChild(container);
    }
    const n = document.createElement("div");
    n.textContent = message;
    n.style.padding = "8px 12px";
    n.style.borderRadius = "8px";
    n.style.boxShadow = "0 6px 18px rgba(0,0,0,0.12)";
    n.style.background =
      type === "success" ? "#e6ffef" : type === "error" ? "#ffecec" : "#f2f4f7";
    n.style.color = "#000";
    container.appendChild(n);
    setTimeout(() => n.remove(), 3200);
  } catch (e) {
    try {
      console.log(type, message);
    } catch (e) {}
  }
}

// --- Cart Manager ---
class CartManager {
  updateCartCount() {
    fetch("/api/cart-count")
      .then((r) => {
        if (!r.ok) return { cart_count: cartCount };
        return r.json().catch(() => ({ cart_count: cartCount }));
      })
      .then((data) => {
        cartCount = data.cart_count || data.count || cartCount || 0;
        const els = document.querySelectorAll(
          "#cart-count, .cart-badge, .cart-badge-floating"
        );
        els.forEach((el) => {
          if (cartCount > 0) {
            el.textContent = cartCount;
            el.style.display = "inline-block";
          } else {
            el.style.display = "none";
          }
        });
      })
      .catch(() => {});
  }
  constructor() {
    this.updateCartCount();
    setInterval(() => this.updateCartCount(), 20000);
  }
  addToCart(itemId, quantity = 1) {
    fetch("/add_to_cart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ menu_item_id: itemId, quantity }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data && data.success) {
          this.updateCartCount();
          showNotification("Mahsulot savatchaga qo'shildi", "success");
        } else {
          showNotification((data && data.message) || "Xatolik", "error");
        }
      })
      .catch(() => showNotification("Xatolik", "error"));
  }
}

window.cartManager = window.cartManager || new CartManager();

// --- Safe fallbacks ---
if (typeof window.openItemModal === "undefined") {
  window.openItemModal = function (itemId, evt) {
    // Modal UI was removed — fallback to navigating to product page
    try {
      const id = encodeURIComponent(String(itemId || ""));
      window.location.href = "/product/" + id;
    } catch (e) {
      try {
        console.warn("openItemModal fallback navigation failed for", itemId);
      } catch (e) {}
    }
  };
}

if (typeof window.closeItemModal === "undefined") {
  // modal DOM removed — closing is a no-op fallback
  window.closeItemModal = function () {
    try {
      // no-op: modal removed in templates
    } catch (e) {}
  };
}

if (typeof window.attachCardHandlers === "undefined") {
  window.attachCardHandlers = function () {
    try {
      document.querySelectorAll(".add-to-cart-btn").forEach((btn) => {
        if (btn._wired) return;
        btn._wired = true;
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const id = btn.getAttribute("data-item-id") || btn.dataset.itemId;
          if (!id) return;
          if (
            window.cartManager &&
            typeof window.cartManager.addToCart === "function"
          ) {
            window.cartManager.addToCart(id, 1);
          }
        });
      });
    } catch (e) {}
  };
}

// --- Minimal MenuClient ---
const MenuClient = (function () {
  let state = { q: "", category: "", limit: 24, offset: 0 };

  function buildQuery() {
    const p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    if (state.category) p.set("category", state.category);
    p.set("limit", state.limit);
    p.set("offset", state.offset);
    return p.toString();
  }

  async function fetchAndRender() {
    try {
      const q = buildQuery();
      const res = await fetch("/api/menu-search?" + q);
      if (!res.ok) return;
      const data = await res.json();
      if (!data || !data.success) return;
      renderMenuItems(data.items || []);
    } catch (e) {
      console.warn("MenuClient fetch error", e);
    }
  }

  function renderMenuItems(items) {
    const grid = document.querySelector(".menu-grid");
    if (!grid) return;
    grid.innerHTML = "";
    if (!items.length) {
      grid.innerHTML =
        '<div class="no-results">Hech qanday mahsulot topilmadi.</div>';
      return;
    }
    items.forEach((item) => {
      const div = document.createElement("div");
      div.className = "menu-item";
      div.setAttribute("data-id", item.id || "");
      const imageHtml = (function () {
        try {
          if (item.media && Array.isArray(item.media) && item.media.length) {
            const imgs = item.media
              .map((m) => {
                const src =
                  typeof m === "string" ? m : m.media_url || m.image_url || "";
                return `<img src="${escapeHtml(
                  src || "/static/defoult.png"
                )}" alt="${escapeHtml(
                  item.name || ""
                )}" loading="lazy" decoding="async" onerror="this.src='/static/defoult.png'" />`;
              })
              .join("");
            return `<div class="item-image"><div class="gallery" data-item-id="${escapeHtml(
              item.id || ""
            )}"><div class="gallery-track">${imgs}</div></div></div>`;
          }
        } catch (e) {}
        return `<div class="item-image"><img src="${escapeHtml(
          item.image_url || "/static/defoult.png"
        )}" alt="${escapeHtml(
          item.name || ""
        )}" loading="lazy" decoding="async" onerror="this.src='/static/defoult.png'" /></div>`;
      })();

      // Build colors badges if present (client-side rendering)
      const colorsHtml = (function () {
        try {
          if (item.colors) {
            const cols = String(item.colors)
              .split(",")
              .map((c) => c.trim())
              .filter(Boolean);
            if (cols.length) {
              return (
                `<div class="card-options"><div class="card-colors" aria-label="Available colors">` +
                cols
                  .map(
                    (c) =>
                      `<span class="color-badge" title="${escapeHtml(
                        c
                      )}" style="background:${escapeHtml(c)}"></span>`
                  )
                  .join("") +
                `</div></div>`
              );
            }
          }
        } catch (e) {}
        return "";
      })();

      div.innerHTML = `
        ${imageHtml}
        <div class="item-content">
          <h3 class="item-name">${escapeHtml(item.name || "")}</h3>
          <div class="rating-section"><div class="stars">${renderStars(
            item.avg_rating || item.rating || 0
          )}</div><span class="rating-text">${
        (item.avg_rating || item.rating || 0).toFixed
          ? (item.avg_rating || item.rating || 0).toFixed(1)
          : item.avg_rating || item.rating || 0
      } (${item.orders_count || 0})</span></div>
          ${colorsHtml}
          <div class="item-footer"><div class="price">${formatPrice(
            item.price || 0
          )}</div><div><button class="add-to-cart-btn" data-item-id="${
        item.id
      }">➕</button></div></div>
        </div>`;

      // Navigate to product page when clicking the card
      div.addEventListener("click", function (e) {
        e.stopPropagation();
        try {
          const id = item.id !== undefined ? item.id : "";
          window.location.href = "/product/" + encodeURIComponent(id);
        } catch (err) {
          try {
            openItemModal(item.id, e);
          } catch (e) {}
        }
      });

      grid.appendChild(div);
      // initialize gallery behaviors for this newly-inserted item (if any)
      try {
        initImageGalleries(div);
      } catch (e) {}
    });
    // rebind add-to-cart handlers
    if (typeof attachCardHandlers === "function") attachCardHandlers();
  }

  return { fetchAndRender, setState: (s) => (state = { ...state, ...s }) };
})();

function initImageGalleries(root = document) {
  try {
    const galleries = Array.from(
      (root || document).querySelectorAll(".gallery")
    );
    galleries.forEach(function (g) {
      const track = g.querySelector(".gallery-track");
      if (!track) return;
      // Common setup
      g.style.overflow = "hidden";
      track.style.display = "flex";
      track.style.transition = "transform 220ms ease";
      track.style.willChange = "transform";
      track.style.display = "flex";
      track.style.transition = "transform 220ms ease";
      track.style.willChange = "transform";

      const imgs = Array.from(track.querySelectorAll("img"));
      if (!imgs || imgs.length === 0) return;

      // Detect touch-capable device
      const isTouchDevice = !!(
        "ontouchstart" in window ||
        (navigator && navigator.maxTouchPoints && navigator.maxTouchPoints > 0)
      );

      if (isTouchDevice) {
        // Carousel/snap mode: each image is full-width of container
        let index = 0;
        const resize = () => {
          try {
            const rect = g.getBoundingClientRect();
            const w = Math.round(
              rect.width || g.clientWidth || window.innerWidth
            );
            imgs.forEach((img) => {
              img.style.flex = "0 0 " + w + "px";
              img.style.maxWidth = w + "px";
              img.style.width = w + "px";
            });
            // reposition to current index
            track.style.transform = `translateX(${-index * w}px)`;
          } catch (e) {}
        };

        // initial resize
        resize();
        window.addEventListener("resize", resize);

        // touch swipe handling with threshold and snapping
        let startX = 0,
          startTime = 0,
          dragging = false,
          startTransform = 0;
        const getTranslateX = () => {
          const m = track.style.transform.match(/translateX\((-?\d+)px\)/);
          return m ? parseInt(m[1], 10) : 0;
        };

        g.addEventListener(
          "touchstart",
          function (ev) {
            try {
              dragging = true;
              startX =
                (ev.touches && ev.touches[0] && ev.touches[0].clientX) || 0;
              startTime = Date.now();
              track.style.transition = "none";
              startTransform = getTranslateX();
            } catch (e) {}
          },
          { passive: true }
        );

        g.addEventListener(
          "touchmove",
          function (ev) {
            try {
              if (!dragging) return;
              const x =
                (ev.touches && ev.touches[0] && ev.touches[0].clientX) || 0;
              const dx = x - startX; // positive => moved right
              const rect = g.getBoundingClientRect();
              const w = Math.round(
                rect.width || g.clientWidth || window.innerWidth
              );
              let attempted = startTransform + dx;
              const maxShift = 0; // translateX is negative or zero
              const minShift = -((imgs.length - 1) * w);
              attempted = Math.max(
                minShift - 40,
                Math.min(maxShift + 40, attempted)
              ); // allow small overscroll
              track.style.transform = `translateX(${attempted}px)`;
            } catch (e) {}
          },
          { passive: true }
        );

        g.addEventListener(
          "touchend",
          function (ev) {
            try {
              if (!dragging) return;
              dragging = false;
              const rect = g.getBoundingClientRect();
              const w = Math.round(
                rect.width || g.clientWidth || window.innerWidth
              );
              const endX =
                (ev.changedTouches &&
                  ev.changedTouches[0] &&
                  ev.changedTouches[0].clientX) ||
                startX;
              const dx = endX - startX; // >0 means swipe right (show previous)
              const dt = Date.now() - startTime;
              // determine velocity & distance
              const velocity = Math.abs(dx / Math.max(1, dt));
              const threshold = Math.max(40, w * 0.18); // px or proportion
              if (Math.abs(dx) > threshold || velocity > 0.3) {
                if (dx < 0) {
                  // moved left -> next image
                  index = Math.min(index + 1, imgs.length - 1);
                } else {
                  // moved right -> previous image
                  index = Math.max(index - 1, 0);
                }
              } else {
                // small move -> snap to nearest
                const cur = Math.abs(getTranslateX());
                index = Math.round(cur / w);
              }
              track.style.transition =
                "transform 260ms cubic-bezier(.2,.8,.2,1)";
              track.style.transform = `translateX(${-index * w}px)`;
            } catch (e) {}
          },
          { passive: true }
        );

        // allow external programmatic set by dataset index
        g.setSlide = function (i) {
          try {
            index = Math.max(0, Math.min(imgs.length - 1, i));
            const rect = g.getBoundingClientRect();
            const w = Math.round(
              rect.width || g.clientWidth || window.innerWidth
            );
            track.style.transition = "transform 260ms cubic-bezier(.2,.8,.2,1)";
            track.style.transform = `translateX(${-index * w}px)`;
          } catch (e) {}
        };
      } else {
        // Desktop: hover-follow continuous behavior
        let rect = null;
        const onMove = (ev) => {
          try {
            rect = g.getBoundingClientRect();
            const clientX = ev.clientX;
            const rel = Math.max(
              0,
              Math.min(1, (clientX - rect.left) / rect.width)
            );
            if (imgs.length <= 1) return;
            const maxShift = track.scrollWidth - rect.width;
            const shift = Math.round(maxShift * rel);
            track.style.transform = `translateX(${-shift}px)`;
          } catch (e) {}
        };
        const onLeave = () => {
          try {
            track.style.transform = "";
          } catch (e) {}
        };
        g.addEventListener("mousemove", onMove);
        g.addEventListener("mouseleave", onLeave);

        // keep a minimal touch fallback
        let startX = 0,
          currentX = 0,
          dragging = false;
        g.addEventListener(
          "touchstart",
          function (ev) {
            try {
              dragging = true;
              startX =
                (ev.touches && ev.touches[0] && ev.touches[0].clientX) || 0;
              track.style.transition = "none";
            } catch (e) {}
          },
          { passive: true }
        );
        g.addEventListener(
          "touchmove",
          function (ev) {
            try {
              if (!dragging) return;
              currentX =
                (ev.touches && ev.touches[0] && ev.touches[0].clientX) || 0;
              const dx = startX - currentX;
              const rect2 = g.getBoundingClientRect();
              const maxShift = Math.max(0, track.scrollWidth - rect2.width);
              const m = track.style.transform.match(/translateX\((-?\d+)px\)/);
              const prev = m ? parseInt(m[1], 10) : 0;
              let attempted = prev - dx;
              attempted = Math.max(-maxShift, Math.min(0, attempted));
              track.style.transform = `translateX(${attempted}px)`;
              startX = currentX;
            } catch (e) {}
          },
          { passive: true }
        );
        g.addEventListener("touchend", function () {
          try {
            dragging = false;
            track.style.transition = "transform 220ms ease";
          } catch (e) {}
        });
      }
    });
  } catch (e) {
    console.warn("initImageGalleries failed", e);
  }
}

// Ensure galleries for server-rendered cards are initialized on DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
  try {
    initImageGalleries(document);
  } catch (e) {}
});

// Expose for dynamic rendering paths
window.initImageGalleries = initImageGalleries;

// Provide a safe initMenuClient fallback so older templates calling
// initMenuClient() won't cause ReferenceErrors. Prefer using
// MenuClient.fetchAndRender when available.
if (typeof window.initMenuClient === "undefined") {
  function initMenuClient() {
    try {
      if (
        window.MenuClient &&
        typeof window.MenuClient.fetchAndRender === "function"
      ) {
        // Optionally allow callers to set initial state via window.MENU_CLIENT_INIT
        try {
          if (
            window.MENU_CLIENT_INIT &&
            typeof window.MenuClient.setState === "function"
          ) {
            window.MenuClient.setState(window.MENU_CLIENT_INIT);
          }
        } catch (e) {}
        window.MenuClient.fetchAndRender();
        return;
      }
    } catch (e) {
      console.warn("initMenuClient fallback failed", e);
    }
  }
  window.initMenuClient = initMenuClient;
}

// --- News Ticker ---
class NewsTicker {
  constructor() {
    this.currentIndex = 0;
    this.newsItems = [];
    this.autoSlideInterval = null;
    this.init();
  }

  async init() {
    try {
      await this.loadNews();
      this.setupEventListeners();
      this.startAutoSlide();
    } catch (e) {
      console.warn("News ticker init failed:", e);
    }
  }

  async loadNews() {
    try {
      const response = await fetch("/api/news?ticker=1");
      const data = await response.json();
      if (data && data.success && data.news && data.news.length > 0) {
        this.newsItems = data.news;
        this.updateDisplay();
      } else {
        // Fallback to all news if no ticker-specific news
        const response2 = await fetch("/api/news");
        const data2 = await response2.json();
        if (data2 && data2.success && data2.news && data2.news.length > 0) {
          this.newsItems = data2.news;
          this.updateDisplay();
        } else {
          this.showNoNews();
        }
      }
    } catch (e) {
      console.warn("News loading failed:", e);
      this.showNoNews();
    }
  }

  updateDisplay() {
    const content = document.getElementById("newsTickerContent");
    const indicators = document.getElementById("newsIndicators");
    if (!content) return;

    if (this.newsItems.length === 0) {
      this.showNoNews();
      return;
    }

    const item = this.newsItems[this.currentIndex];
    content.innerHTML = `
      <div class="news-item">
        <div class="news-icon">${
          item.type === "advertisement" ? "📢" : "📰"
        }</div>
        <div class="news-text">
          <div class="news-title">${escapeHtml(item.title || "")}</div>
          <div class="news-content">${escapeHtml(
            (item.content || item.description || "").substring(0, 100)
          )}</div>
        </div>
      </div>
    `;

    // Update indicators
    if (indicators) {
      indicators.innerHTML = "";
      for (let i = 0; i < this.newsItems.length; i++) {
        const dot = document.createElement("span");
        dot.className = `news-indicator ${
          i === this.currentIndex ? "active" : ""
        }`;
        dot.onclick = () => this.goToSlide(i);
        indicators.appendChild(dot);
      }
    }
  }

  showNoNews() {
    const content = document.getElementById("newsTickerContent");
    if (content) {
      content.innerHTML = `
        <div class="news-item">
          <div class="news-icon">📰</div>
          <div class="news-text">
            <div class="news-title">Yangiliklar yo'q</div>
            <div class="news-content">Hozircha yangiliklar mavjud emas</div>
          </div>
        </div>
      `;
    }
  }

  setupEventListeners() {
    // Listen for refresh events
    window.addEventListener("refreshNewsTicker", () => {
      this.loadNews();
    });
  }

  startAutoSlide() {
    if (this.newsItems.length <= 1) return;
    this.autoSlideInterval = setInterval(() => {
      this.nextSlide();
    }, 5000); // 5 seconds
  }

  stopAutoSlide() {
    if (this.autoSlideInterval) {
      clearInterval(this.autoSlideInterval);
      this.autoSlideInterval = null;
    }
  }

  nextSlide() {
    if (this.newsItems.length <= 1) return;
    this.currentIndex = (this.currentIndex + 1) % this.newsItems.length;
    this.updateDisplay();
  }

  prevSlide() {
    if (this.newsItems.length <= 1) return;
    this.currentIndex =
      this.currentIndex === 0
        ? this.newsItems.length - 1
        : this.currentIndex - 1;
    this.updateDisplay();
  }

  goToSlide(index) {
    if (index >= 0 && index < this.newsItems.length) {
      this.currentIndex = index;
      this.updateDisplay();
    }
  }
}

// Global functions for onclick handlers
window.nextNews = function () {
  if (window.newsTicker) window.newsTicker.nextSlide();
};

window.prevNews = function () {
  if (window.newsTicker) window.newsTicker.prevSlide();
};

// initialize when appropriate
document.addEventListener("DOMContentLoaded", function () {
  try {
    initMenuClient();
  } catch (e) {}
  try {
    if (window.cartManager) window.cartManager.updateCartCount();
  } catch (e) {}
  try {
    // Initialize news ticker if the component exists
    if (document.getElementById("newsTicker")) {
      window.newsTicker = new NewsTicker();
    }
  } catch (e) {
    console.warn("News ticker initialization failed:", e);
  }
});

// export
window.showNotification = showNotification;
window.MenuClient = MenuClient;

// end of main.js
