// Language switching functionality
function changeLanguage(langCode) {
  try {
    var supported = ["uz", "ru", "en", "kz"];
    var path = window.location.pathname || "/";
    var search = window.location.search || "";
    var segs = path.split("/");

    if (segs.length > 1 && supported.indexOf(segs[1]) !== -1) {
      segs[1] = langCode;
    } else {
      // Insert language as first segment
      segs.splice(1, 0, langCode);
    }

    var newPath = segs.join("/");
    if (!newPath.startsWith("/")) newPath = "/" + newPath;
    newPath = newPath.replace(/\/\/+/g, "/");

    // Normalize some common routes to language-prefixed menu
    if (
      path === "/" ||
      path === "" ||
      path === "/menu" ||
      path.startsWith("/menu")
    ) {
      newPath = "/" + langCode + "/menu";
    }

    // Persist language on server and then navigate to new path
    fetch("/api/change-language", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token":
          (document.querySelector('meta[name="csrf-token"]') || {}).content ||
          "",
      },
      credentials: "same-origin",
      body: JSON.stringify({ language: langCode }),
    })
      .then(function (response) {
        return response.json().catch(function () {
          return {};
        });
      })
      .then(function (data) {
        try {
          // Show user feedback: success or error
          if (data && data.success) {
            showMessage(
              (data.message && data.message) || "Til o'zgartirildi",
              "success"
            );
            // Navigate after a short delay so user sees the message
            setTimeout(function () {
              if (data.redirect) {
                window.location.href = data.redirect;
              } else {
                window.location.href = newPath + search;
              }
            }, 700);
          } else {
            var msg =
              (data && data.message) ||
              "Tilni o'zgartirishda xatolik yuz berdi";
            showMessage(msg, "danger");
          }
        } catch (e) {
          showMessage("Til o'zgartirilganda ichki xatolik", "danger");
          setTimeout(function () {
            window.location.href = newPath + search;
          }, 700);
        }
      })
      .catch(function (err) {
        // If API fails, still navigate so URL drives language detection on server
        console.error("changeLanguage error:", err);
        showMessage("Xabar yubirishda xato — sahifa yangilanmoqda", "danger");
        setTimeout(function () {
          window.location.href = newPath + search;
        }, 700);
      });
  } catch (e) {
    // Last resort
    console.error(e);
    window.location.reload();
  }
}

// Small helper to show a Bootstrap alert at top of main container
function showMessage(text, type) {
  try {
    type = type || "info"; // info, success, danger, warning
    var container = document.querySelector("main.container") || document.body;
    var alertEl = document.createElement("div");
    alertEl.className = "alert alert-" + type + " alert-dismissible fade show";
    alertEl.role = "alert";
    alertEl.style.zIndex = 9999;
    alertEl.innerText = text;

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-close";
    btn.setAttribute("data-bs-dismiss", "alert");
    btn.setAttribute("aria-label", "Close");
    alert.appendChild(btn);

    // insert at top of container
    if (container.firstChild)
      container.insertBefore(alertEl, container.firstChild);
    else container.appendChild(alertEl);

    // auto-remove after 4s
    setTimeout(function () {
      try {
        if (alertEl && alertEl.classList) {
          alertEl.classList.remove("show");
          alertEl.classList.add("hide");
        }
        if (alertEl && alertEl.remove) alertEl.remove();
      } catch (e) {}
    }, 4000);
  } catch (e) {
    try {
      window.alert(text);
    } catch (err) {}
  }
}

// Toast notification funksiyasi (Unified)
function showToast(message, type = 'info') {
  try {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = 'position:fixed; top:20px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:10px; pointer-events:none;';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.style.cssText = 'padding:12px 24px; border-radius:12px; background:#fff; box-shadow:0 10px 30px rgba(0,0,0,0.1); display:flex; align-items:center; transform:translateX(100%); transition:all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55); pointer-events:auto;';
    
    // Add specific styles based on type if needed (can also be handled in CSS)
    if (type === 'success') toast.style.borderLeft = '4px solid #10b981';
    if (type === 'error') toast.style.borderLeft = '4px solid #ef4444';
    if (type === 'warning') toast.style.borderLeft = '4px solid #f59e0b';

    toast.innerHTML = `<div style="font-weight:600; color:#1e293b;">${message}</div>`;
    container.appendChild(toast);

    setTimeout(() => toast.style.transform = 'translateX(0)', 10);

    setTimeout(() => {
      toast.style.transform = 'translateX(110%)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  } catch (e) {
    console.warn('Toast error:', e);
    alert(message);
  }
}

// Global toggleFavorite function
function toggleFavorite(itemId, btn) {
  const icon = btn.querySelector('i');
  if (!icon) return;
  const isAdded = icon.classList.contains('bi-heart-fill');
  const url = isAdded ? `/remove-from-favorites/${itemId}` : `/add-to-favorites/${itemId}`;
  
  btn.disabled = true;
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': (typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : (document.querySelector('meta[name="csrf-token"]')?.content || ''))
    }
  })
  .then(r => r.json())
  .then(data => {
    btn.disabled = false;
    if (data.success || data.message?.includes("allaqachon")) {
      icon.classList.remove(isAdded ? 'bi-heart-fill' : 'bi-heart');
      icon.classList.add(isAdded ? 'bi-heart' : 'bi-heart-fill');
      btn.classList.toggle('active', !isAdded);
      showToast(data.message || 'Muvaffaqiyatli!', 'success');
    } else {
      showToast(data.message || 'Xatolik yuz berdi', 'error');
    }
  })
  .catch(err => {
    btn.disabled = false;
    console.error('Favorite toggle error:', err);
    showToast('Xatolik yuz berdi', 'error');
  });
}
