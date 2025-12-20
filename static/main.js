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

      // Detect touch-capable device
      const isTouchDevice = !!(
        "ontouchstart" in window ||
        (navigator && navigator.maxTouchPoints && navigator.maxTouchPoints > 0)
      );

      if (isTouchDevice && !g.hasAttribute('data-item-id')) {
        // Carousel/snap mode: each image is full-width of container (skip for menu items)
        let index = 0;
        try {
          const videos = container.querySelectorAll("video");
          videos.forEach((v) => {
            try {
              const videos = container.querySelectorAll("video");
              videos.forEach((v) => {
                v.addEventListener("loadedmetadata", () =>
                  this.equalizeHeights()
                );
                v.addEventListener("canplay", () => this.equalizeHeights());
                if (v.readyState >= 1) {
                  try {
                    this.equalizeHeights();
                  } catch (e) {}
                }
              });
            } catch (e) {}
            v.addEventListener("loadedmetadata", () => this.equalizeHeights());
            v.addEventListener("canplay", () => this.equalizeHeights());
            if (v.readyState >= 1) {
              try {
                this.equalizeHeights();
              } catch (e) {}
            }
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
            
            // Snap to nearest image instead of continuous movement
            const targetIndex = Math.round(rel * (imgs.length - 1));
            const maxShift = track.scrollWidth - rect.width;
            const targetShift = Math.round(maxShift * (targetIndex / (imgs.length - 1)));
            
            track.style.transform = `translateX(${-targetShift}px)`;
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

      // Add setSlide method for programmatic control (both touch and desktop modes)
      g.setSlide = function (i) {
        try {
          const idx = Math.max(0, Math.min(imgs.length - 1, i || 0));
          
          if (isTouchDevice && !g.hasAttribute('data-item-id')) {
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
      // Recalculate heights on resize for responsive layouts
      window.addEventListener("resize", () => {
        try {
          this.equalizeHeights();
        } catch (e) {}
      });
      this.startAutoSlide();
    } catch (e) {
      console.warn("News ticker init failed:", e);
    }
  }

  equalizeHeights() {
    const container = document.getElementById("newsTickerContent");
    if (!container) return;
    const items = Array.from(container.querySelectorAll(".news-item"));
    if (!items || items.length === 0) return;

    // Reset heights first so we measure natural heights
    items.forEach((it) => {
      it.style.height = "auto";
    });

    // On small screens we prefer natural stacking - don't enforce equal height
    const narrow =
      window.matchMedia && window.matchMedia("(max-width: 640px)").matches;
    if (narrow) return;

    let maxH = 0;
    items.forEach((it) => {
      try {
        const h = it.getBoundingClientRect().height;
        if (h > maxH) maxH = h;
      } catch (e) {}
    });

    if (maxH > 0) {
      items.forEach((it) => {
        try {
          it.style.height = Math.ceil(maxH) + "px";
        } catch (e) {}
      });
    }
  }
  async loadNews() {
    try {
      // Determine preferred language from page (session-injected) or <html lang>
      const preferredLang =
        (document.body &&
          document.body.dataset &&
          document.body.dataset.language) ||
        document.documentElement.lang ||
        "ru";

      // Load news from the API (DB-backed). Use same-origin credentials
      // so admin-authenticated content can be included when needed.
      const res = await fetch(`/api/news?active=true&lang=${preferredLang}`, {
        cache: "no-cache",
        credentials: "same-origin",
      });
      if (!res || !res.ok) {
        throw new Error("Failed to load /api/news");
      }
      const blob = await res.json().catch(() => null);
      if (!blob || !blob.success) {
        throw new Error("Invalid /api/news payload");
      }

      let items = Array.isArray(blob.news) ? blob.news : [];

      if (!items || !items.length) {
        this.showNoNews();
        return;
      }

      const lang = String(preferredLang || "ru").toLowerCase();
      const supported = ["uz", "ru", "en", "kz"];
      const langKey = supported.indexOf(lang) !== -1 ? lang : "ru";

      // Helper to pick localized field from news.json structure
      const pickLocalized = (obj, base) => {
        if (!obj || !base) return "";
        const direct = obj[`${base}_${langKey}`];
        if (direct) return String(direct);
        return (
          obj[`${base}_uz`] ||
          obj[`${base}_ru`] ||
          obj[`${base}_en`] ||
          obj[`${base}_kz`] ||
          obj[base] ||
          ""
        );
      };

      // Keep only active items and sort by display_order then created_at
      items = items
        .filter((it) => it && (it.is_active === undefined || it.is_active))
        .sort((a, b) => {
          const odA =
            a && a.display_order != null ? Number(a.display_order) : 9999;
          const odB =
            b && b.display_order != null ? Number(b.display_order) : 9999;
          if (odA !== odB) return odA - odB;
          const ca = (a && a.created_at) || "";
          const cb = (b && b.created_at) || "";
          if (ca < cb) return -1;
          if (ca > cb) return 1;
          return 0;
        });

      this.newsItems = items.map((it) => {
        const title = pickLocalized(it, "title");
        const content = pickLocalized(it, "content");
        // Ensure arrays exist even if API omitted them
        it.images = Array.isArray(it.images)
          ? it.images
          : it.images_json
          ? JSON.parse(it.images_json || "[]")
          : it.image_url
          ? [it.image_url]
          : [];
        it.videos = Array.isArray(it.videos)
          ? it.videos
          : it.videos_json
          ? JSON.parse(it.videos_json || "[]")
          : it.video_url
          ? [it.video_url]
          : [];
        it.youtube_embeds = Array.isArray(it.youtube_embeds)
          ? it.youtube_embeds
          : it.youtube_embed
          ? [it.youtube_embed]
          : (it.videos || []).map((v) => {
              const m =
                v &&
                v.match(/(?:v=|\/embed\/|youtu\.be\/)([A-Za-z0-9_\-]{11})/);
              return m ? "https://www.youtube.com/embed/" + m[1] : null;
            });
        return {
          ...it,
          title,
          content,
          localized_title: title,
          localized_content: content,
        };
      });

      if (!this.newsItems.length) {
        this.showNoNews();
        return;
      }

      this.currentIndex = 0;
      this.updateDisplay();
    } catch (e) {
      console.warn("News loading failed from news.json:", e);
      this.showNoNews();
    }
  }

  updateDisplay() {
    const container = document.getElementById("newsTickerContent");
    const indicators = document.getElementById("newsIndicators");
    if (!container) return;
    if (!this.newsItems || this.newsItems.length === 0) {
      this.showNoNews();
      return;
    }
    // Render all visible items horizontally so native scrolling + nav works
    container.innerHTML = "";
    this.newsItems.forEach((it, idx) => {
      const itemWrap = document.createElement("div");
      itemWrap.className = "news-item";
      itemWrap.setAttribute("data-news-id", it.id || "");
      itemWrap.style.display = "inline-block";
      itemWrap.style.verticalAlign = "top";
      // Keep a compact card width for desktop ticker; responsive CSS will
      // allow full-width stacking on narrow screens.
      itemWrap.style.width = "280px";
      itemWrap.style.marginRight = "12px";

      // Build media HTML: support multiple youtube embeds, videos and images.
      let mediaHtml = "";
      try {
        const mediaMainId = `news-media-main-${idx}`;
        const thumbsId = `news-media-thumbs-${idx}`;
        // Determine primary media (prefer youtube embed, then video, then image)
        let primaryHtml = "";
        if (
          it.youtube_embeds &&
          it.youtube_embeds.length &&
          it.youtube_embeds[0]
        ) {
          primaryHtml = `<iframe src="${escapeHtml(
            it.youtube_embeds[0]
          )}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
        } else if (it.videos && it.videos.length && it.videos[0]) {
          primaryHtml = `<video controls muted playsinline src="${escapeHtml(
            it.videos[0]
          )}"></video>`;
        } else if (it.images && it.images.length && it.images[0]) {
          primaryHtml = `<img src="${escapeHtml(
            it.images[0]
          )}" alt="${escapeHtml(it.title || "")}">`;
        }

        // Build thumbnails (images + video thumbnails + youtube thumbnails)
        const thumbs = [];
        (it.images || []).forEach((src) => {
          if (src) thumbs.push({ type: "image", src: src });
        });
        (it.videos || []).forEach((src) => {
          if (src) thumbs.push({ type: "video", src: src });
        });
        (it.youtube_embeds || []).forEach((src, ii) => {
          if (src) {
            // derive youtube thumbnail from embed id
            const m = String(src).match(/embed\/([A-Za-z0-9_\-]{11})/);
            const thumb = m
              ? `https://img.youtube.com/vi/${m[1]}/mqdefault.jpg`
              : null;
            if (thumb) thumbs.push({ type: "youtube", src: src, thumb: thumb });
          }
        });

        const thumbsHtml = thumbs.length
          ? `<div id="${thumbsId}" class="news-media-thumbs">${thumbs
              .map(
                (t, ti) =>
                  `<button data-index="${ti}" class="thumb-btn" data-type="${
                    t.type
                  }" data-src="${escapeHtml(t.src)}" ${
                    t.thumb ? `data-thumb="${escapeHtml(t.thumb)}"` : ""
                  }><img src="${escapeHtml(t.thumb || t.src)}"/></button>`
              )
              .join("")}</div>`
          : "";

        mediaHtml = `<div class="news-media"><div id="${mediaMainId}" class="news-media-main">${primaryHtml}</div>${thumbsHtml}</div>`;
      } catch (e) {
        mediaHtml = "";
      }
      // Prefer localized fields populated by data/news.json or /api/news?lang=...
      const titleText =
        it.localized_title ||
        it.title ||
        it.title_uz ||
        it.title_ru ||
        it.title_en ||
        it.title_kz ||
        "";
      const excerptRaw =
        (
          it.localized_content ||
          it.content ||
          it.description ||
          it.content_uz ||
          it.content_ru ||
          it.content_en ||
          it.content_kz ||
          ""
        ).trim() || "";
      const excerpt = escapeHtml(
        excerptRaw.substring(0, 120) + (excerptRaw.length > 120 ? "..." : "")
      );

      itemWrap.innerHTML = `
        ${mediaHtml}
        <div class="news-body">
          <h4 class="news-title">${escapeHtml(titleText || "")}</h4>
          <p class="news-excerpt">${excerpt}</p>
        </div>
      `;

      itemWrap.addEventListener("click", (e) => {
        try {
          const id = encodeURIComponent(String(it.id || ""));
          window.location.href = "/news/" + id;
        } catch (e) {}
      });
      // Attach thumbnail behavior if any
      try {
        // defer to next tick so DOM exists
        setTimeout(() => {
          const main = itemWrap.querySelector(".news-media-main");
          const thumbs = itemWrap.querySelectorAll(".thumb-btn");
          if (!main || !thumbs || thumbs.length === 0) return;
          thumbs.forEach((btn) => {
            btn.addEventListener("click", (ev) => {
              ev.stopPropagation();
              const type = btn.getAttribute("data-type");
              const src = btn.getAttribute("data-src");
              if (!src) return;
              try {
                if (type === "image") {
                  main.innerHTML = `<img src="${escapeHtml(
                    src
                  )}" alt="${escapeHtml(it.title || "")}">`;
                } else if (type === "video") {
                  main.innerHTML = `<video controls muted playsinline src="${escapeHtml(
                    src
                  )}"></video>`;
                } else if (type === "youtube") {
                  main.innerHTML = `<iframe src="${escapeHtml(
                    src
                  )}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
                }
                // adjust heights after swapping
                try {
                  window.newsTicker && window.newsTicker.equalizeHeights();
                } catch (e) {}
              } catch (e) {}
            });
          });
        }, 1);
      } catch (e) {}
      container.appendChild(itemWrap);
    });

    // Ensure container is horizontally scrollable
    container.style.whiteSpace = "nowrap";
    container.style.overflowX = "auto";
    container.style.display = "block";

    // Equalize card heights so ticker visuals are consistent.
    try {
      // Wait a tick to allow layout and then equalize.
      setTimeout(() => {
        this.equalizeHeights();

        // Re-run when images/iframes finish loading so heights correct after media load
        try {
          const imgs = container.querySelectorAll("img");
          imgs.forEach((im) =>
            im.addEventListener("load", () => this.equalizeHeights())
          );
        } catch (e) {}
        try {
          const iframes = container.querySelectorAll("iframe");
          iframes.forEach((f) =>
            f.addEventListener("load", () => this.equalizeHeights())
          );
        } catch (e) {}
      }, 10);
    } catch (e) {
      console.warn("Equalize heights failed:", e);
    }

    // Update indicators
    if (indicators) {
      indicators.innerHTML = "";
      for (let i = 0; i < this.newsItems.length; i++) {
        const dot = document.createElement("span");
        dot.className =
          "news-indicator" + (i === this.currentIndex ? " active" : "");
        dot.onclick = () => this.goToSlide(i);
        indicators.appendChild(dot);
      }
    }

    // Scroll to the currentIndex so auto-slide feels like a carousel
    try {
      const items = container.querySelectorAll(".news-item");
      if (items && items.length && items[this.currentIndex]) {
        // Use container.scrollTo to explicitly scroll only the ticker container
        // This avoids letting scrollIntoView try to scroll the whole page vertically
        try {
          const el = items[this.currentIndex];
          const elLeft = el.offsetLeft || 0;
          const elCenter = elLeft + (el.clientWidth || 0) / 2;
          const targetLeft = Math.max(
            0,
            Math.round(elCenter - (container.clientWidth || 0) / 2)
          );
          try {
            container.scrollTo({ left: targetLeft, behavior: "smooth" });
          } catch (e) {
            // Some older environments may not support options object
            container.scrollLeft = targetLeft;
          }
        } catch (e) {
          // last-resort fallback: try scrollIntoView but request nearest block
          try {
            items[this.currentIndex].scrollIntoView({
              behavior: "smooth",
              inline: "center",
              block: "nearest",
            });
          } catch (e) {}
        }
      }
    } catch (e) {
      // ignore scrolling errors
    }
  }

  showNoNews() {
    const content = document.getElementById("newsTickerContent");
    if (content) {
      content.innerHTML = `
        <div class="news-item">
          <div class="news-icon">News</div>
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
    if (!autoUpdatesAllowed()) return;
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
