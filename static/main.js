// Universal Restaurant System - Main JavaScript

// Global o'zgaruvchilar
let cartCount = 0;
// Global current path tracking
window.currentPath = window.currentPath || window.location.pathname;

// Professional Translation System
// Global translations object - attach to window to avoid duplicate declarations
if (typeof window.translations === "undefined") {
  window.translations = {
    uz: {
      menu: "📋 Menyu",
      favorites: "❤️ Sevimlilar",
      contact: "📞 Aloqa",
      about: "❓ Savollar",
      downloads: "📱 Yuklamalar",
      cart: "🛒 Savatcha",
      profile_info: "👤 Profil ma'lumotlari",
      profile_settings: "⚙️ Profil sozlamalari",
      settings: "🔧 Sozlamalar",
      logout: "🚪 Chiqish",
      login: "🔐 Kirish",
      register: "📝 Ro'yxat",
      user: "👤 Foydalanuvchi",
      staff: "👨‍💼 Xodim",
      courier: "🚚 Kuryer",
      admin: "🔧 Admin",
      dashboard: "🏠 Dashboard",
      analytics: "📊 Analytics",
      reports: "📈 Hisobotlar",
      system: "⚙️ Tizim",
      logs: "📝 Loglar",
    },
    ru: {
      menu: "📋 Меню",
      favorites: "❤️ Избранное",
      contact: "📞 Контакты",
      about: "❓ Вопросы",
      downloads: "📱 Загрузки",
      cart: "🛒 Корзина",
      profile_info: "👤 Данные профиля",
      profile_settings: "⚙️ Настройки профиля",
      settings: "🔧 Настройки",
      logout: "🚪 Выход",
      login: "🔐 Вход",
      register: "📝 Регистрация",
      user: "👤 Пользователь",
      staff: "👨‍💼 Сотрудник",
      courier: "🚚 Курьер",
      admin: "🔧 Админ",
      dashboard: "🏠 Панель",
      analytics: "📊 Аналитика",
      reports: "📈 Отчеты",
      system: "⚙️ Система",
      logs: "📝 Логи",
    },
    en: {
      menu: "📋 Menu",
      favorites: "❤️ Favorites",
      contact: "📞 Contact",
      about: "❓ About",
      downloads: "📱 Downloads",
      cart: "🛒 Cart",
      profile_info: "👤 Profile Info",
      profile_settings: "⚙️ Profile Settings",
      settings: "🔧 Settings",
      logout: "🚪 Logout",
      login: "🔐 Login",
      register: "📝 Register",
      user: "👤 User",
      staff: "👨‍💼 Staff",
      courier: "🚚 Courier",
      admin: "🔧 Admin",
      dashboard: "🏠 Dashboard",
      analytics: "📊 Analytics",
      reports: "📈 Reports",
      system: "⚙️ System",
      logs: "📝 Logs",
    },
  };
}

// Universal Theme Management
class UniversalThemeManager {
  constructor() {
    this.initializeTheme();
    this.setupEventListeners();
  }

  initializeTheme() {
    const darkMode = localStorage.getItem("darkMode") === "true";
    const fontSize = localStorage.getItem("fontSize") || "medium";
    const language = localStorage.getItem("language") || "uz";

    console.log("Universal Theme - Initializing:", {
      darkMode,
      fontSize,
      language,
    });

    this.applyTheme(darkMode);
    this.applyFontSize(fontSize);
    this.applyLanguage(language);
  }

  applyTheme(isDark) {
    const body = document.body;
    const navbar = document.querySelector(".navbar");

    // Clear theme classes
    body.classList.remove("dark-theme", "light-theme");

    if (isDark) {
      body.classList.add("dark-theme");
      body.setAttribute("data-theme", "dark");

      if (navbar) {
        navbar.classList.remove("navbar-light", "bg-light");
        navbar.classList.add("navbar-dark", "bg-dark");
      }

      console.log("Universal Theme - Dark mode applied");
    } else {
      body.classList.add("light-theme");
      body.setAttribute("data-theme", "light");

      if (navbar) {
        navbar.classList.remove("navbar-dark", "bg-dark");
        navbar.classList.add("navbar-light", "bg-light");
      }

      console.log("Universal Theme - Light mode applied");
    }

    // Save to localStorage
    localStorage.setItem("darkMode", isDark);

    // Save to server
    this.saveToServer("theme", isDark ? "dark" : "light");
  }

  applyFontSize(size) {
    const body = document.body;

    // Clear font classes
    body.classList.remove(
      "font-small",
      "font-medium",
      "font-large",
      "font-xlarge"
    );

    // Apply font size
    body.classList.add("font-" + size);
    body.setAttribute("data-font-size", size);

    console.log("Universal Theme - Font size applied:", size);

    // Save to localStorage
    localStorage.setItem("fontSize", size);

    // Save to server
    this.saveToServer("font_size", size);
  }

  applyLanguage(language) {
    const body = document.body;

    // Clear language classes
    body.classList.remove("lang-uz", "lang-ru", "lang-en");

    // Apply language
    body.classList.add("lang-" + language);
    body.setAttribute("data-language", language);

    console.log("Universal Theme - Language applied:", language);

    // Save to localStorage
    localStorage.setItem("language", language);

    // Translate page
    this.translatePage(language);

    // Save to server
    this.saveToServer("language", language);
  }

  translatePage(language) {
    const trans = window.translations[language] || window.translations.uz;

    // Navbar links
    this.updateElementText('a[href*="menu"]', trans.menu);
    this.updateElementText('a[href*="favorites"]', trans.favorites);
    this.updateElementText('a[href*="contact"]', trans.contact);
    this.updateElementText('a[href*="about"]', trans.about);
    this.updateElementText('a[href*="downloads"]', trans.downloads);

    // Cart link
    const cartLink = document.querySelector('a[href*="cart"]');
    if (cartLink && cartLink.innerHTML.includes("🛒")) {
      const cartBadge =
        cartLink.querySelector(".cart-badge") ||
        cartLink.querySelector("#cart-count");
      const badgeHtml = cartBadge ? cartBadge.outerHTML : "";
      cartLink.innerHTML = trans.cart + " " + badgeHtml;
    }

    // Login/Register links
    this.updateElementText(
      'a[href*="login"]:not([href*="staff"]):not([href*="courier"])',
      trans.login
    );
    this.updateElementText(
      'a[href*="register"]:not([href*="staff"]):not([href*="courier"])',
      trans.register
    );

    // Dropdown items
    this.translateDropdownItems(trans);

    console.log("Universal Theme - Translation completed:", language);
  }

  updateElementText(selector, text) {
    const element = document.querySelector(selector);
    if (element && !element.innerHTML.includes("<")) {
      element.innerHTML = text;
    }
  }

  translateDropdownItems(trans) {
    const dropdownItems = document.querySelectorAll(".dropdown-item");
    dropdownItems.forEach((item) => {
      const text = item.textContent.trim();

      if (text.includes("Foydalanuvchi")) {
        item.innerHTML = trans.user;
      } else if (text.includes("Xodim")) {
        item.innerHTML = trans.staff;
      } else if (text.includes("Kuryer")) {
        item.innerHTML = trans.courier;
      } else if (text.includes("Admin")) {
        item.innerHTML = trans.admin;
      } else if (text.includes("Profil ma'lumotlari")) {
        item.innerHTML = trans.profile_info;
      } else if (text.includes("Profil sozlamalari")) {
        item.innerHTML = trans.profile_settings;
      } else if (text.includes("Sozlamalar")) {
        item.innerHTML = trans.settings;
      } else if (text.includes("Dashboard")) {
        item.innerHTML = trans.dashboard;
      } else if (text.includes("Chiqish")) {
        item.innerHTML = trans.logout;
      } else if (text.includes("Analytics")) {
        item.innerHTML = trans.analytics;
      } else if (text.includes("Hisobotlar")) {
        item.innerHTML = trans.reports;
      } else if (text.includes("Tizim")) {
        item.innerHTML = trans.system;
      } else if (text.includes("Loglar")) {
        item.innerHTML = trans.logs;
      }
    });
  }

  saveToServer(setting, value) {
    const endpoint =
      setting === "language" ? "/api/set-language" : "/api/set-settings";
    const payload =
      setting === "language" ? { language: value } : { [setting]: value };

    fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // include CSRF token if available from templates (base.html defines CSRF_TOKEN)
        "X-CSRF-Token": typeof CSRF_TOKEN !== "undefined" ? CSRF_TOKEN : "",
      },
      body: JSON.stringify(payload),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          console.log("Universal Theme - Setting saved:", setting, value);
        }
      })
      .catch((error) => {
        console.log("Universal Theme - Save error:", error);
      });
  }

  setupEventListeners() {
    // Storage event listener
    window.addEventListener("storage", (e) => {
      if (e.key === "darkMode") {
        this.applyTheme(e.newValue === "true");
      } else if (e.key === "fontSize") {
        this.applyFontSize(e.newValue);
      } else if (e.key === "language") {
        this.applyLanguage(e.newValue);
      }
    });

    // Theme toggle listeners
    document.addEventListener("change", (e) => {
      if (e.target.name === "theme_mode") {
        this.applyTheme(e.target.value === "dark");
      } else if (e.target.name === "font_size") {
        this.applyFontSize(e.target.value);
      }
    });
  }
}

// Global functions
window.changeTheme = function (isDark) {
  if (window.universalTheme) {
    window.universalTheme.applyTheme(isDark);
  }
};

window.changeFontSize = function (size) {
  if (window.universalTheme) {
    window.universalTheme.applyFontSize(size);
  }
};

window.changeLanguage = function (language) {
  if (window.universalTheme) {
    window.universalTheme.applyLanguage(language);
    // Show notification
    showNotification("Til muvaffaqiyatli o'zgartirildi");
  }
};

// Cart Management
class CartManager {
  constructor() {
    this.updateCartCount();
    this.setupAutoUpdate();
  }

  updateCartCount() {
    fetch("/api/cart-count")
      .then((response) => {
        if (response.status === 429) {
          console.warn("Cart count rate limited (429)");
          return Promise.resolve({ cart_count: cartCount });
        }
        if (!response.ok) return Promise.resolve({ cart_count: cartCount });
        return response.json().catch((err) => {
          console.warn("Cart count json parse error", err);
          return { cart_count: cartCount };
        });
      })
      .then((data) => {
        const cartCountElements = document.querySelectorAll(
          "#cart-count, .cart-badge, .cart-badge-floating"
        );
        cartCountElements.forEach((element) => {
          const count = data.cart_count || data.count || 0;
          if (count > 0) {
            element.textContent = count;
            element.style.display = "inline-block";
            if (element.classList.contains("cart-badge-floating")) {
              element.classList.add("show");
            }
          } else {
            element.style.display = "none";
            if (element.classList.contains("cart-badge-floating")) {
              element.classList.remove("show");
            }
          }
        });
        cartCount = data.cart_count || data.count || 0;
      })
      .catch((error) => console.log("Cart count error:", error));
  }

  setupAutoUpdate() {
    // Update every 20 seconds to reduce server load
    setInterval(() => {
      this.updateCartCount();
    }, 20000);
  }

  addToCart(itemId, quantity = 1, size = null, color = null) {
    const payload = { menu_item_id: itemId, quantity: quantity };
    if (size !== null && size !== undefined && size !== "") payload.size = size;
    if (color !== null && color !== undefined && color !== "")
      payload.color = color;

    fetch("/add_to_cart", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          this.updateCartCount();
          showNotification("Mahsulot savatchaga qo'shildi", "success");

          // Update cart count display
          if (data.cart_count !== undefined) {
            const cartCountElements = document.querySelectorAll(
              "#cart-count, .cart-badge, .cart-badge-floating"
            );
            cartCountElements.forEach((element) => {
              element.textContent = data.cart_count;
              if (data.cart_count > 0) {
                element.style.display = "inline-block";
                element.classList.add("show");
              }
            });
          }
        } else {
          showNotification(data.message || "Xatolik yuz berdi", "error");
        }
      })
      .catch((error) => {
        console.log("Add to cart error:", error);
        showNotification("Savatchaga qo'shishda xatolik", "error");
      });
  }
}

// Notification System (uses a persistent #toast-container)
function showNotification(message, type = "info") {
  try {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.style.position = "fixed";
      container.style.right = "20px";
      container.style.bottom = "20px";
      container.style.zIndex = "2147483647"; // very high
      container.style.display = "flex";
      container.style.flexDirection = "column";
      container.style.gap = "8px";
      document.body.appendChild(container);
    }

    const notification = document.createElement("div");
    notification.className = `toast-notification toast-${type}`;
    notification.style.minWidth = "220px";
    notification.style.maxWidth = "360px";
    notification.style.padding = "10px 14px";
    notification.style.borderRadius = "8px";
    notification.style.boxShadow = "0 6px 18px rgba(0,0,0,0.12)";
    notification.style.opacity = "0";
    notification.style.transform = "translateY(6px)";
    notification.style.transition = "opacity 220ms ease, transform 220ms ease";
    notification.style.background =
      type === "success" ? "#e6ffef" : type === "error" ? "#ffecec" : "#f2f4f7";
    notification.style.color = "#111";

    notification.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px">
        <div style="font-size:18px">${
          type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️"
        }</div>
        <div style="flex:1">${message}</div>
      </div>
    `;

    container.appendChild(notification);

    // Show
    requestAnimationFrame(() => {
      notification.style.opacity = "1";
      notification.style.transform = "translateY(0)";
    });

    // Auto-remove after timeout
    setTimeout(() => {
      notification.style.opacity = "0";
      notification.style.transform = "translateY(6px)";
      setTimeout(() => {
        if (notification.parentNode)
          notification.parentNode.removeChild(notification);
      }, 240);
    }, 3600);
  } catch (err) {
    // Fallback
    try {
      console.log("showNotification fallback", message, type);
      alert(message);
    } catch (e) {
      // ignore
    }
  }
}

// Service Worker Registration
function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .register("/static/sw.js")
      .then((registration) => {
        console.log("SW registered: ", registration);
      })
      .catch((error) => {
        console.log("SW registration failed: ", error);
      });
  }
}

// Universal Initialization
let universalTheme;
let cartManager;

document.addEventListener("DOMContentLoaded", function () {
  try {
    // Initialize theme manager
    universalTheme = new UniversalThemeManager();
    window.universalTheme = universalTheme;

    // Initialize cart manager
    cartManager = new CartManager();
    window.cartManager = cartManager;

    // Register service worker
    registerServiceWorker();

    // Setup menu item clicks
    setupMenuItemClicks();

    // Setup form submissions
    setupFormSubmissions();

    console.log("Universal System - Initialization complete");
  } catch (error) {
    console.error("Initialization error:", error);
  }
});

// Menu item click handlers
function setupMenuItemClicks() {
  document.addEventListener("click", function (e) {
    // Add to cart buttons
    if (e.target.classList.contains("add-to-cart-btn")) {
      e.preventDefault();
      const itemId = e.target.getAttribute("data-item-id");
      const quantity = e.target.getAttribute("data-quantity") || 1;
      const size = e.target.getAttribute("data-size");
      const color = e.target.getAttribute("data-color");
      if (itemId && window.cartManager) {
        window.cartManager.addToCart(itemId, quantity, size, color);
      }
    }

    // Theme toggle buttons
    if (e.target.classList.contains("theme-toggle")) {
      e.preventDefault();
      const isDark = !document.body.classList.contains("dark-theme");
      if (window.universalTheme) {
        window.universalTheme.applyTheme(isDark);
      }
    }
  });
}

// Form submission handlers
function setupFormSubmissions() {
  // Settings form
  const settingsForm = document.getElementById("settings-form");
  if (settingsForm) {
    settingsForm.addEventListener("submit", function (e) {
      e.preventDefault();

      const formData = new FormData(settingsForm);
      const settings = Object.fromEntries(formData);

      // Apply settings immediately
      if (settings.theme_mode && window.universalTheme) {
        window.universalTheme.applyTheme(settings.theme_mode === "dark");
      }
      if (settings.font_size && window.universalTheme) {
        window.universalTheme.applyFontSize(settings.font_size);
      }
      if (settings.language && window.universalTheme) {
        window.universalTheme.applyLanguage(settings.language);
      }

      showNotification("Sozlamalar saqlandi", "success");
    });
  }
}

// Utility Functions
function formatPrice(price) {
  return new Intl.NumberFormat("uz-UZ", {
    style: "currency",
    currency: "UZS",
    minimumFractionDigits: 0,
  }).format(price);
}

function formatDate(date) {
  return new Intl.DateTimeFormat("uz-UZ", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

// Global error handler
window.addEventListener("error", function (e) {
  console.error("JavaScript xatosi:", e.error);
  if (typeof showNotification === "function") {
    showNotification("Sahifada xatolik yuz berdi", "error");
  }
});

// Page visibility handler
document.addEventListener("visibilitychange", function () {
  if (!document.hidden && window.cartManager) {
    window.cartManager.updateCartCount();
  }
});

// Resize handler
window.addEventListener("resize", function () {
  // Handle responsive changes if needed
  const isMobile = window.innerWidth < 768;
  document.body.classList.toggle("mobile-view", isMobile);
});

// Yangiliklar tasmasi (News Ticker) - Yangi Slider System
class NewsTicker {
  constructor(selector = ".news-ticker-content", options = {}) {
    console.log("NewsTicker constructor called with selector:", selector);
    this.container = document.querySelector(selector);
    console.log("Container found:", this.container);
    this.options = {
      autoSlide: options.autoSlide !== false,
      slideInterval: options.slideInterval || 3000, // 3 sekund
      visibleItems: options.visibleItems || 4, // Ekranda ko'rinadigan elementlar soni
      itemWidth: options.itemWidth || 300, // Har bir element kengligi (gap bilan)
      autoUpdate: options.autoUpdate !== false,
      updateInterval: options.updateInterval || 60000, // 1 daqiqa
      ...options,
    };

    if (!this.container) {
      console.error("News ticker container not found with selector:", selector);
      return;
    }

    // Slider holati
    this.currentIndex = 0;
    this.newsItems = [];
    this.isPlaying = true;
    this.autoSlideTimer = null;

    console.log("Calling init()");
    this.init();
  }

  init() {
    console.log("NewsTicker init() called");
    // Navigation tugmalarini topish
    this.prevBtn = document.getElementById("newsPrevBtn");
    this.nextBtn = document.getElementById("newsNextBtn");
    this.playBtn = document.getElementById("newsPlayBtn");
    this.playIcon = document.getElementById("playIcon");

    console.log("Buttons found:", {
      prevBtn: this.prevBtn,
      nextBtn: this.nextBtn,
      playBtn: this.playBtn,
      playIcon: this.playIcon,
    });

    // Event listener'larni o'rnatish
    this.setupEventListeners();

    // Yangiliklarni yuklash
    console.log("Loading news...");
    this.loadNews();

    // Vaqti-vaqti bilan yangilab turish
    if (this.options.autoUpdate) {
      setInterval(() => this.loadNews(), this.options.updateInterval);
    }
  }

  setupEventListeners() {
    console.log(
      "Setting up event listeners - prevBtn:",
      this.prevBtn,
      "nextBtn:",
      this.nextBtn
    );
    if (this.prevBtn) {
      console.log("Adding click listener to prevBtn");
      this.prevBtn.addEventListener("click", () => {
        console.log("Prev button clicked!");
        this.slidePrev();
      });
    } else {
      console.warn("Previous button not found!");
    }

    if (this.nextBtn) {
      console.log("Adding click listener to nextBtn");
      this.nextBtn.addEventListener("click", () => {
        console.log("Next button clicked!");
        this.slideNext();
      });
    } else {
      console.warn("Next button not found!");
    }

    if (this.playBtn) {
      this.playBtn.addEventListener("click", () => this.toggleAutoSlide());
    }

    // Hover pause/resume
    if (this.container) {
      this.container.addEventListener("mouseenter", () =>
        this.pauseAutoSlide()
      );
      this.container.addEventListener("mouseleave", () =>
        this.resumeAutoSlide()
      );
    }

    // Touch events (mobile)
    let startX = 0;
    let endX = 0;

    if (this.container) {
      this.container.addEventListener("touchstart", (e) => {
        startX = e.touches[0].clientX;
      });

      this.container.addEventListener("touchend", (e) => {
        endX = e.changedTouches[0].clientX;
        const diff = startX - endX;

        if (Math.abs(diff) > 50) {
          // Minimum swipe distance
          if (diff > 0) {
            this.slideNext();
          } else {
            this.slidePrev();
          }
        }
      });
    }
  }

  loadNews() {
    fetch("/api/news")
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.news && data.news.length > 0) {
          this.newsItems = data.news;
          this.updateNewsItems();
          this.startAutoSlide();
        }
      })
      .catch((error) => {
        console.error("Yangiliklar yuklashda xatolik:", error);
      });
  }

  updateNewsItems() {
    if (!this.container || !this.newsItems.length) return;

    // Yangiliklar HTMLini yaratish
    let html = "";

    this.newsItems.forEach((item) => {
      const isAd = item.type === "advertisement";
      const hasImage = item.image_url && item.image_url.trim() !== "";
      const hasVideo = item.video_url && item.video_url.trim() !== "";
      const hasYouTube = item.youtube_embed && item.youtube_embed.trim() !== "";

      html += `<div class="news-item ${isAd ? "advertisement" : "news"}">`;

      // Rasm yoki video mavjud bo'lsa tepa qismda ko'rsatish
      if (hasImage) {
        html += `<img src="${item.image_url}" alt="${item.title}" class="news-media clickable-media" onclick="openMediaModal('${item.image_url}', 'image', '${item.title}')">`;
      } else if (hasYouTube) {
        // embed YouTube iframe thumbnail-sized in ticker (clickable to open modal)
        html += `<div class="news-media youtube-embed" onclick="openMediaModal('${item.youtube_embed}', 'youtube', '${item.title}')">`;
        html += `<iframe src="${item.youtube_embed}" frameborder="0" allowfullscreen style="width:100%;height:160px;border:0;border-radius:6px"></iframe>`;
        html += `</div>`;
      } else if (hasVideo) {
        html += `<video src="${item.video_url}" class="news-media clickable-media" muted autoplay loop onclick="openMediaModal('${item.video_url}', 'video', '${item.title}')"></video>`;
      }

      // Matn qismi
      html += '<div class="news-text-content">';
      html += `<div class="news-title">${item.title}</div>`;

      if (item.content && item.content.trim() !== "") {
        html += `<div class="news-content">${item.content}</div>`;
      }

      html += "</div>"; // news-text-content ning oxiri
      html += "</div>"; // news-item ning oxiri
    });

    // HTMLni konteynerga joylashtirish
    this.container.innerHTML = html;

    // Slider pozitsiyasini o'rnatish
    this.updateSliderPosition();
  }

  slideNext() {
    if (!this.newsItems.length) return;

    this.currentIndex = (this.currentIndex + 1) % this.newsItems.length;
    this.updateSliderPosition();
    this.restartAutoSlide();
  }

  slidePrev() {
    if (!this.newsItems.length) return;

    this.currentIndex =
      this.currentIndex === 0
        ? this.newsItems.length - 1
        : this.currentIndex - 1;
    this.updateSliderPosition();
    this.restartAutoSlide();
  }

  updateSliderPosition() {
    if (!this.container || !this.newsItems.length) return;

    const translateX = -(this.currentIndex * this.options.itemWidth);
    this.container.style.transform = `translateX(${translateX}px)`;
  }

  startAutoSlide() {
    if (!this.options.autoSlide || !this.isPlaying) return;

    this.stopAutoSlide();
    this.autoSlideTimer = setInterval(() => {
      this.slideNext();
    }, this.options.slideInterval);
  }

  stopAutoSlide() {
    if (this.autoSlideTimer) {
      clearInterval(this.autoSlideTimer);
      this.autoSlideTimer = null;
    }
  }

  pauseAutoSlide() {
    this.stopAutoSlide();
  }

  resumeAutoSlide() {
    if (this.isPlaying) {
      this.startAutoSlide();
    }
  }

  restartAutoSlide() {
    if (this.isPlaying) {
      this.startAutoSlide();
    }
  }

  toggleAutoSlide() {
    this.isPlaying = !this.isPlaying;

    if (this.isPlaying) {
      this.startAutoSlide();
      if (this.playIcon) this.playIcon.textContent = "⏸️";
    } else {
      this.stopAutoSlide();
      if (this.playIcon) this.playIcon.textContent = "▶️";
    }
  }
}

// Yangiliklar tasmasini ishga tushirish
document.addEventListener("DOMContentLoaded", function () {
  console.log("Initializing News Ticker - DOM Content Loaded");
  // Asosiy yangiliklar tasmasi - Yangi Slider
  window.newsTicker = new NewsTicker(".news-ticker-content", {
    autoSlide: true,
    slideInterval: 3000, // 3 sekund
    visibleItems: 4, // Desktop
    itemWidth: 300, // gap + padding bilan
    autoUpdate: true,
    updateInterval: 60000, // 1 daqiqa
  });

  console.log("News Ticker initialized:", window.newsTicker);

  // Responsive item width
  function updateSliderSettings() {
    if (!window.newsTicker) return;

    const width = window.innerWidth;
    let itemWidth = 300;
    let visibleItems = 4;

    if (width <= 480) {
      itemWidth = 220;
      visibleItems = 1;
    } else if (width <= 768) {
      itemWidth = 250;
      visibleItems = 2;
    } else if (width <= 968) {
      itemWidth = 270;
      visibleItems = 3;
    }

    window.newsTicker.options.itemWidth = itemWidth;
    window.newsTicker.options.visibleItems = visibleItems;

    // Pozitsiyani qayta hisoblash
    if (window.newsTicker.updateSliderPosition) {
      window.newsTicker.updateSliderPosition();
    }
  }

  // Initial call
  updateSliderSettings();

  // Window resize listener
  window.addEventListener("resize", updateSliderSettings);
});

// Media Modal Functions for News Ticker
function openMediaModal(mediaUrl, mediaType, title) {
  console.log("Opening media modal:", mediaUrl, mediaType, title);

  // Create modal if it doesn't exist
  let modal = document.getElementById("mediaModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "mediaModal";
    modal.className = "media-modal-overlay";
    modal.innerHTML = `
      <div class="media-modal-content">
        <div class="media-modal-header">
          <h3 id="mediaModalTitle"></h3>
          <button class="media-modal-close" onclick="closeMediaModal()">&times;</button>
        </div>
        <div class="media-modal-body">
          <div id="mediaModalContainer"></div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  // Set modal content
  const titleElement = document.getElementById("mediaModalTitle");
  const containerElement = document.getElementById("mediaModalContainer");

  titleElement.textContent = title || "Медиа";

  if (mediaType === "image") {
    containerElement.innerHTML = `<img src="${mediaUrl}" alt="${title}" class="modal-media-image">`;
  } else if (mediaType === "video") {
    containerElement.innerHTML = `<video src="${mediaUrl}" controls class="modal-media-video"></video>`;
  } else if (mediaType === "youtube") {
    // mediaUrl expected to be an embed URL like https://www.youtube.com/embed/VIDEO_ID
    containerElement.innerHTML = `<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;"><iframe src="${mediaUrl}" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen></iframe></div>`;
  }

  // Show modal
  modal.style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeMediaModal() {
  const modal = document.getElementById("mediaModal");
  if (modal) {
    modal.style.display = "none";
    document.body.style.overflow = "auto";
  }
}

// Close modal when clicking outside content
document.addEventListener("click", function (e) {
  const modal = document.getElementById("mediaModal");
  if (modal && e.target === modal) {
    closeMediaModal();
  }
});

// Close modal with ESC key
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    closeMediaModal();
  }
});

// Export for global use
window.showNotification = showNotification;
window.NewsTicker = NewsTicker;
window.openMediaModal = openMediaModal;
window.closeMediaModal = closeMediaModal;
