// @ts-nocheck
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

function autoUpdatesAllowed() {
  try {
    return !window.DISABLE_AUTO_UPDATES;
  } catch (e) {
    return true;
  }
}

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
  let r = Number(rating) || 0;
  r = Math.max(0, Math.min(5, r));
  // round to nearest 0.5 so we can represent halves
  r = Math.round(r * 2) / 2;
  let s = "";
  for (let i = 1; i <= 5; i++) {
    if (r >= i) {
      s += '<span class="star filled">★</span>';
    } else if (r >= i - 0.5) {
      s += '<span class="star half">★</span>';
    } else {
      s += '<span class="star empty">★</span>';
    }
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

// --- AuthStore: reactive, persisted auth state with subscribers
const AuthStore = (function () {
  let state = { logged: false, role: null, user: null };
  const subs = [];
  function notify() {
    subs.forEach((s) => {
      try {
        s(state);
      } catch (e) {}
    });
  }
  function set(newState) {
    state = Object.assign({}, state, newState || {});
    try {
      localStorage.setItem("auth", JSON.stringify(state));
    } catch (e) {}
    notify();
  }
  function init() {
    try {
      const raw = localStorage.getItem("auth");
      if (raw) state = Object.assign({}, state, JSON.parse(raw));
    } catch (e) {}
    // Try to sync with server-side session state
    try {
      fetch("/api/auth/status", { credentials: "same-origin" })
        .then((r) => {
          if (!r.ok) return null;
          return r.json();
        })
        .then((d) => {
          if (d && d.logged_in) set({ logged: true, role: d.user && d.user.role ? d.user.role : d.role || null, user: d.user || d.user });
          else set({ logged: false, role: null, user: null });
        })
        .catch(() => {});
    } catch (e) {}
    // storage event from other windows/tabs
    window.addEventListener("storage", (e) => {
      if (e.key === "auth") {
        try {
          state = JSON.parse(e.newValue || "null") || { logged: false };
        } catch (e) {}
        notify();
      }
    });
    notify();
    return state;
  }
  function subscribe(fn) {
    if (typeof fn !== "function") return function () {};
    subs.push(fn);
    try {
      fn(state);
    } catch (e) {}
    return function () {
      const idx = subs.indexOf(fn);
      if (idx >= 0) subs.splice(idx, 1);
    };
  }
  return { init, set, subscribe, getState: () => state };
})();

window.AuthStore = AuthStore;

// Update navbar DOM based on auth state (shows/hides login/register and ensures profile link)
function updateNavbarByAuth(s) {
  try {
    const loginLink = document.querySelector('a.nav-link[href*="/login_page"]');
    const registerLink = document.querySelector('a.nav-link[href*="/register"]');
    if (s && s.logged) {
      if (loginLink) loginLink.style.display = "none";
      if (registerLink) registerLink.style.display = "none";
      // ensure profile link exists in the primary nav area
      let profileLink = document.querySelector('a.nav-link[href*="/profile"]');
      if (!profileLink) {
        profileLink = document.createElement("a");
        profileLink.className = "nav-link";
        profileLink.href = "/profile";
        profileLink.textContent = "Profil";
        const li = document.createElement("li");
        li.className = "nav-item";
        li.appendChild(profileLink);
        const nav = document.querySelector(".navbar-nav");
        if (nav) nav.appendChild(li);
      }
    } else {
      if (loginLink) loginLink.style.display = "";
      if (registerLink) registerLink.style.display = "";
      const p = document.querySelector('a.nav-link[href*="/profile"]');
      if (p) {
        const li = p.closest("li");
        if (li) li.remove();
      }
    }
  } catch (e) {}
}

// Subscribe on load and initialize
document.addEventListener("DOMContentLoaded", function () {
  try {
    AuthStore.subscribe(updateNavbarByAuth);
    AuthStore.init();
  } catch (e) {}

  // Track pre-login page so we can redirect back after authentication
  try {
    document.querySelectorAll('a.nav-link[href*="/login_page"]').forEach(function(a){
      a.addEventListener('click', function(e){
        try{ sessionStorage.setItem('preLogin', window.location.pathname + (window.location.search||'')); }catch(_){}
      });
    });
  } catch (e) {}
});

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
    if (autoUpdatesAllowed()) {
      this.pollTimer = setInterval(() => this.updateCartCount(), 20000);
    }
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
      if (res && res.ok) {
        const data = await res.json().catch(() => null);
        if (data && data.success && Array.isArray(data.items)) {
          // cache last successful dataset to allow client-side fallback filtering
          try {
            window.menuDataArr = data.items.slice();
          } catch (e) {}
          renderMenuItems(data.items || []);
          return;
        }
      }
    } catch (e) {
      console.warn("MenuClient fetch error", e);
    }
    // If API failed or returned nothing, try client-side filtering of existing DOM/data
    try {
      applyClientSideFilter();
    } catch (e) {
      console.warn("applyClientSideFilter failed", e);
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
      // Use same class as server template so filtering and diagnostics work
      div.className = "menu-item-card";
      div.setAttribute("data-id", item.id || "");
      try {
        div.setAttribute(
          "data-category",
          (item.category || "").toString().toLowerCase()
        );
      } catch (e) {}
      const imageHtml = (function () {
        try {
          if (item.media && Array.isArray(item.media) && item.media.length) {
            const imgs = item.media
              .map((m) => {
                const src =
                  typeof m === "string" ? m : m.media_url || m.image_url || "";
                // Prefer localized name if provided by API
                const altText = item.name_local || item.name || "";
                return `<img src="${escapeHtml(
                  src || "/static/defoult.webp"
                )}" alt="${escapeHtml(
                  altText
                )}" loading="lazy" decoding="async" onerror="this.src='/static/defoult.webp'" />`;
              })
              .join("");
            return `<div class="card-image"><div class="gallery" data-item-id="${escapeHtml(
              item.id || ""
            )}"><div class="gallery-track">${imgs}</div></div></div>`;
          }
        } catch (e) {}
        const altText = item.name_local || item.name || "";
        return `<div class="card-image"><img src="${escapeHtml(
          item.image_url || "/static/defoult.webp"
        )}" alt="${escapeHtml(
          altText
        )}" loading="lazy" decoding="async" onerror="this.src='/static/defoult.webp'" /></div>`;
      })();

      // Colors and add-to-cart removed by request (no UI controls needed on cards)
      const colorsHtml = "";

      div.innerHTML = `
        ${imageHtml}
        <div class="card-body">
          <h3 class="card-title">${escapeHtml(
            item.name_local || item.name || ""
          )}</h3>
          <div class="card-rating"><div class="stars">${renderStars(
            item.avg_rating || item.rating || 0
          )}</div><span class="rating-text">${
        (item.avg_rating || item.rating || 0).toFixed
          ? (item.avg_rating || item.rating || 0).toFixed(1)
          : item.avg_rating || item.rating || 0
      } (${item.orders_count || 0})</span></div>
          ${colorsHtml}
          <!-- item-footer (price/add-to-cart) removed intentionally -->
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

    // Enforce circular caps and toggle for long menus
    try {
      enforceMenuCaps();
    } catch (e) {}
  }

  // Cap rules and toggle handling
  function enforceMenuCaps() {
    const grid = document.querySelector(".menu-grid");
    if (!grid) return;
    // Remove previous toggle if present
    let existingToggle = document.querySelector(".menu-grid-toggle");
    if (existingToggle) existingToggle.remove();

    const isPhone = window.matchMedia("(max-width: 575.98px)").matches;
    const isLaptop = window.matchMedia("(min-width: 992px)").matches;
    const maxItemsPhone = 14; // 2 columns * 7 rows
    const maxItemsLaptop = 30; // 3 columns * 10 rows
    const cap = isPhone
      ? maxItemsPhone
      : isLaptop
      ? maxItemsLaptop
      : maxItemsPhone;

    const cards = Array.from(grid.querySelectorAll(".menu-item-card"));
    // First, unhide all
    cards.forEach((c) => c.classList.remove("hidden-by-cap"));

    if (cards.length > cap) {
      // Use pagination instead of single toggle. Render first page by default.
      paginateMenu(grid, cards, cap);
    } else {
      // remove any existing pagination controls
      const prev = document.querySelector(".menu-grid-pagination");
      if (prev) prev.remove();
    }
  }

  // Paginate menu cards: shows itemsPerPage per page and renders page navigation
  function paginateMenu(grid, cards, itemsPerPage) {
    if (!grid) return;
    // remove previous pagination if any
    const existing = document.querySelector(".menu-grid-pagination");
    if (existing) existing.remove();

    const total = cards.length;
    const pages = Math.max(1, Math.ceil(total / itemsPerPage));
    let currentPage = parseInt(grid.getAttribute("data-menu-page") || "1", 10);
    if (currentPage < 1) currentPage = 1;
    if (currentPage > pages) currentPage = pages;
    grid.setAttribute("data-menu-page", String(currentPage));

    // hide all, then show only the slice for current page
    cards.forEach((c) => c.classList.add("hidden-by-cap"));
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const visible = cards.slice(start, end);
    visible.forEach((c) => c.classList.remove("hidden-by-cap"));

    // build pagination markup similar to the sample (table-based row)
    const wrap = document.createElement("div");
    wrap.className = "menu-grid-pagination";
    const table = document.createElement("table");
    table.className = "menu-pagination-table";
    const tbody = document.createElement("tbody");
    const tr = document.createElement("tr");

    // helper to create a page cell
    function pageCell(pageNum, label, isActive) {
      const td = document.createElement("td");
      td.className = "menu-page-cell";
      if (isActive) td.classList.add("active");
      const a = document.createElement("a");
      a.href = "#";
      a.className = "menu-page-link";
      a.setAttribute("data-page", String(pageNum));
      a.setAttribute("aria-label", "Sahifa " + pageNum);
      a.textContent = label || String(pageNum);
      a.addEventListener("click", function (e) {
        e.preventDefault();
        const targetPage = parseInt(this.getAttribute("data-page"), 10) || 1;
        grid.setAttribute("data-menu-page", String(targetPage));
        paginateMenu(grid, cards, itemsPerPage);
        try {
          grid.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (e) {}
      });
      td.appendChild(a);
      return td;
    }

    // Prev
    const prevPage = Math.max(1, currentPage - 1);
    tr.appendChild(pageCell(prevPage, "«", false));

    // show up to 9 page numbers with current centered when possible
    const maxVisible = 9;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(pages, startPage + maxVisible - 1);
    if (endPage - startPage + 1 < maxVisible) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }

    for (let p = startPage; p <= endPage; p++) {
      tr.appendChild(pageCell(p, String(p), p === currentPage));
    }

    // Next
    const nextPage = Math.min(pages, currentPage + 1);
    tr.appendChild(pageCell(nextPage, "»", false));

    tbody.appendChild(tr);
    table.appendChild(tbody);
    wrap.appendChild(table);
    grid.parentNode.insertBefore(wrap, grid.nextSibling);
  }

  return { fetchAndRender, setState: (s) => (state = { ...state, ...s }) };
})();

// Debounce helper and global search/filter wiring used by templates
function debounce(fn, wait) {
  let t = null;
  return function (...args) {
    if (t) clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), wait || 250);
  };
}

// Run caps on load and viewport change
window.addEventListener("DOMContentLoaded", function () {
  try {
    enforceMenuCaps();
  } catch (e) {}
});

// Debounced resize handler to re-run cap enforcement
window.addEventListener(
  "resize",
  (function () {
    let t = null;
    return function () {
      if (t) clearTimeout(t);
      t = setTimeout(function () {
        try {
          enforceMenuCaps();
        } catch (e) {}
      }, 250);
    };
  })()
);

// Read filter inputs, update MenuClient state and fetch results (or fallback)
window.performMenuSearch = function () {
  try {
    // DISABLED: MenuClient replacement of styled cards
    // Use only client-side filtering to preserve beautiful card styling
    applyClientSideFilter();
    return;

    const qEl = document.getElementById("menuSearchInput");
    const catEl = document.getElementById("filterCategory");
    const sizeEl = document.getElementById("filterSize");
    const colorEl = document.getElementById("filterColor");
    const sortEl = document.getElementById("filterSort");

    const q = qEl ? qEl.value.trim() : "";
    const category = catEl ? catEl.value || "" : "";
    const size = sizeEl ? sizeEl.value || "" : "";
    const color = colorEl ? colorEl.value || "" : "";
    const sort = sortEl ? sortEl.value || "" : "";

    if (window.MenuClient && typeof window.MenuClient.setState === "function") {
      window.MenuClient.setState({ q, category, size, color, sort, offset: 0 });
      // async fetch - MenuClient has its own fallback to client-side filtering
      try {
        window.MenuClient.fetchAndRender();
      } catch (e) {
        console.warn("MenuClient.fetchAndRender failed", e);
        applyClientSideFilter();
      }
    } else {
      // If MenuClient missing, attempt client-side filter only
      applyClientSideFilter();
    }
  } catch (e) {
    console.warn("performMenuSearch error", e);
  }
};

// Debounced version wired by templates to input events
window.debouncedSearch = debounce(window.performMenuSearch, 300);

// Simple client-side filter that hides/shows existing .menu-item-card elements based on inputs
// NOTE: this function must only work with menu cards. Previous versions
// accidentally mixed in news-ticker logic which broke the whole script.
window.applyClientSideFilter = function () {
  try {
    const grid = document.querySelector(".menu-grid");
    if (!grid) return;

    const q = (document.getElementById("menuSearchInput")?.value || "")
      .toLowerCase()
      .trim();
    const category = (document.getElementById("filterCategory")?.value || "")
      .toLowerCase()
      .trim();
    const size = (document.getElementById("filterSize")?.value || "")
      .toLowerCase()
      .trim();
    const color = (document.getElementById("filterColor")?.value || "")
      .toLowerCase()
      .trim();

    const cards = Array.from(grid.querySelectorAll(".menu-item-card"));
    cards.forEach((card) => {
      let visible = true;
      try {
        const title = (
          card.querySelector(".item-name")?.textContent ||
          card.querySelector(".card-title")?.textContent ||
          ""
        ).toLowerCase();
        const cat = (card.getAttribute("data-category") || "").toLowerCase();

        if (category && !cat.includes(category)) {
          visible = false;
        }
        if (visible && q && !title.includes(q)) {
          visible = false;
        }
        if (visible && size) {
          const sizesRaw = (card.dataset.sizes || "").toLowerCase();
          if (!sizesRaw.includes(size)) visible = false;
        }
        if (visible && color) {
          const colorsRaw = (card.dataset.colors || "").toLowerCase();
          if (!colorsRaw.includes(color)) visible = false;
        }
      } catch (e) {
        console.warn("applyClientSideFilter error for card", e);
      }
      card.style.display = visible ? "block" : "none";
    });
  } catch (e) {
    console.warn("applyClientSideFilter error", e);
  }
};

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

      // Ensure pan-mode images use relative positioning and flex sizing
      try {
        imgs.forEach((img) => {
          img.style.position = 'relative';
          img.style.inset = 'auto';
          img.style.opacity = '1';
          img.style.flex = '0 0 100%';
          img.style.width = '100%';
          img.style.height = '100%';
          img.style.objectFit = 'contain';
        });
      } catch (e) {}

      // If this gallery has multiple images, enable 'pan' mode and add UI (arrows/dots)
      if (imgs.length > 1) {
        try {
          g.dataset.mode = 'pan';
          // arrows
          if (!g.querySelector('.gallery-arrow--prev')) {
            const prev = document.createElement('button');
            prev.type = 'button';
            prev.className = 'gallery-arrow gallery-arrow--prev';
            prev.setAttribute('aria-label','Previous image');
            prev.innerHTML = '&#x2039;';
            const next = document.createElement('button');
            next.type = 'button';
            next.className = 'gallery-arrow gallery-arrow--next';
            next.setAttribute('aria-label','Next image');
            next.innerHTML = '&#x203A;';
            g.appendChild(prev);
            g.appendChild(next);
          }

          // dots
          if (!g.querySelector('.gallery-dots')) {
            const dots = document.createElement('div');
            dots.className = 'gallery-dots';
            imgs.forEach((im, ii) => {
              const d = document.createElement('button');
              d.type = 'button';
              d.className = 'gallery-dot' + (ii === 0 ? ' active' : '');
              d.setAttribute('data-idx', String(ii));
              dots.appendChild(d);
            });
            g.appendChild(dots);
          }
        } catch (e) {}
      }

      // Detect touch-capable device
      const isTouchDevice = !!(
        "ontouchstart" in window ||
        (navigator && navigator.maxTouchPoints && navigator.maxTouchPoints > 0)
      );

      // On touch devices enable carousel/snap mode for all galleries (including item cards)
      if (isTouchDevice) {
        // Carousel/snap mode: each image is full-width of container (skip for menu items)
        let index = 0;
        try {
          const videos = track.querySelectorAll("video");
          videos.forEach((v) => {
            try {
              v.addEventListener("loadedmetadata", () => {});
              v.addEventListener("canplay", () => {});
            } catch (e) {}
          });
        } catch (e) {}
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

      } else {
        // Desktop: hover-follow continuous pan + arrow/dot controls
        let rect = null;
        let index = 0;

        function updateMetricsPan() {
          rect = g.getBoundingClientRect();
          // size each image to container width for predictable snapping
          try {
              const w = Math.round(rect.width || g.clientWidth || window.innerWidth);
              imgs.forEach((img) => {
                img.style.flex = `0 0 ${w}px`;
                img.style.maxWidth = w + 'px';
                img.style.width = w + 'px';
                img.style.height = '100%';
              });
              // explicitly set track width so scrollWidth calculations are reliable
              const totalW = imgs.length * w;
              track.style.width = totalW + 'px';
              track.style.height = rect.height + 'px';
              // expose total width for pan math
              g._pan_total_width = totalW;
          } catch (e) {}
        }
        updateMetricsPan();
        window.addEventListener('resize', updateMetricsPan);

        function updateActiveDot(i) {
          try {
            const dots = g.querySelectorAll('.gallery-dot');
            if (!dots || !dots.length) return;
            dots.forEach((d, idx) => d.classList.toggle('active', idx === i));
          } catch (e) {}
        }

        const onMove = (ev) => {
          try {
            if (!rect) updateMetricsPan();
            const clientX = ev.clientX;
            const rel = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
            if (imgs.length <= 1) return;
            const totalW = g._pan_total_width || Math.max(0, track.scrollWidth);
            const maxShift = Math.max(0, totalW - rect.width);
            const tx = -Math.round(maxShift * rel);
            track.style.transform = `translateX(${tx}px)`;
            // mark nearest index visually
            const approx = Math.round(rel * (imgs.length - 1));
            if (approx !== index) {
              index = approx;
              updateActiveDot(index);
            }
          } catch (e) {}
        };

        const onLeave = () => {
          try {
            // snap to current index
            const w = rect ? rect.width : (g.clientWidth || window.innerWidth);
            track.style.transition = 'transform 320ms cubic-bezier(.2,.8,.2,1)';
            track.style.transform = `translateX(${-(index * w)}px)`;
            setTimeout(()=>{ try{ track.style.transition = 'transform 220ms ease'; }catch(e){} }, 360);
          } catch (e) {}
        };

        g.addEventListener('mousemove', onMove);
        g.addEventListener('mouseleave', onLeave);

        // wire arrows
        try {
          const prev = g.querySelector('.gallery-arrow--prev');
          const next = g.querySelector('.gallery-arrow--next');
          if (prev) prev.addEventListener('click', (ev) => {
            ev.stopPropagation();
            index = Math.max(0, index - 1);
            const w = rect ? rect.width : (g.clientWidth || window.innerWidth);
            track.style.transition = 'transform 320ms cubic-bezier(.2,.8,.2,1)';
            track.style.transform = `translateX(${-(index * w)}px)`;
            updateActiveDot(index);
          });
          if (next) next.addEventListener('click', (ev) => {
            ev.stopPropagation();
            index = Math.min(imgs.length - 1, index + 1);
            const w = rect ? rect.width : (g.clientWidth || window.innerWidth);
            track.style.transition = 'transform 320ms cubic-bezier(.2,.8,.2,1)';
            track.style.transform = `translateX(${-(index * w)}px)`;
            updateActiveDot(index);
          });

          // dot clicks
          const dots = Array.from(g.querySelectorAll('.gallery-dot'));
          dots.forEach((d) => {
            d.addEventListener('click', (ev) => {
              ev.stopPropagation();
              const idx = parseInt(d.getAttribute('data-idx') || '0', 10) || 0;
              index = Math.max(0, Math.min(imgs.length - 1, idx));
              const w = rect ? rect.width : (g.clientWidth || window.innerWidth);
              track.style.transition = 'transform 320ms cubic-bezier(.2,.8,.2,1)';
              track.style.transform = `translateX(${-(index * w)}px)`;
              updateActiveDot(index);
            });
          });
        } catch (e) {}

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

      // Add setSlide method for programmatic control (both touch and desktop modes)
      g.setSlide = function (i) {
        try {
          const idx = Math.max(0, Math.min(imgs.length - 1, i || 0));
          
          if (isTouchDevice) {
            // Touch/carousel mode: snap to specific slide
            const rect = g.getBoundingClientRect();
            const w = Math.round(rect.width || g.clientWidth || window.innerWidth);
            track.style.transition = "transform 260ms cubic-bezier(.2,.8,.2,1)";
            track.style.transform = `translateX(${-idx * w}px)`;
          } else {
            // Desktop hover-follow mode: jump to specific position
            const rect = g.getBoundingClientRect();
            const maxShift = Math.max(0, track.scrollWidth - rect.width);
            const targetShift = (imgs.length > 1) ? Math.round(maxShift * (idx / (imgs.length - 1))) : 0;
            track.style.transition = "transform 260ms cubic-bezier(.2,.8,.2,1)";
            track.style.transform = `translateX(${-targetShift}px)`;
            // update dots if present
            try {
              const dots = g.querySelectorAll('.gallery-dot');
              if (dots && dots.length) {
                dots.forEach((d, ii) => d.classList.toggle('active', ii === idx));
              }
            } catch (e) {}
          }
        } catch (e) {
          console.warn("setSlide failed:", e);
        }
      };
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
      // Prevent double-initialization on pages that call this multiple times
      if (window._menuClientInitDone && !(window.MENU_CLIENT_INIT && window.MENU_CLIENT_INIT.forceFetch)) {
        return;
      }
      if (
        window.MenuClient &&
        typeof window.MenuClient.fetchAndRender === "function"
      ) {
        // If server already rendered menu cards, avoid re-fetching immediately
        // — this prevents double-rendering where client fetch would clear
        // server-rendered images and re-insert cards (sometimes causing
        // transient missing images). Allow forcing a client fetch via
        // `window.MENU_CLIENT_INIT && window.MENU_CLIENT_INIT.forceFetch`.
        const hasServerCards = !!document.querySelector(
          ".menu-grid .menu-item-card"
        );
        const forced =
          window.MENU_CLIENT_INIT && window.MENU_CLIENT_INIT.forceFetch;
        if (hasServerCards && !forced) {
          try {
            // initialize galleries on existing DOM and apply client filters
            initImageGalleries(document);
            applyClientSideFilter();
            enforceMenuCaps();
            // mark initialized to avoid subsequent double-runs
            window._menuClientInitDone = true;
          } catch (e) {}
          return;
        }
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
        // mark initialized so subsequent calls don't re-fetch unless forced
        window._menuClientInitDone = true;
        return;
      }
    } catch (e) {
      console.warn("initMenuClient fallback failed", e);
    }
  }
  window.initMenuClient = initMenuClient;
}
  try {
    if (window.cartManager) window.cartManager.updateCartCount();
  } catch (e) {}

// export
window.showNotification = showNotification;
window.MenuClient = MenuClient;

// end of main.js
