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
    var alert = document.createElement("div");
    alert.className = "alert alert-" + type + " alert-dismissible fade show";
    alert.role = "alert";
    alert.style.zIndex = 9999;
    alert.innerText = text;

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-close";
    btn.setAttribute("data-bs-dismiss", "alert");
    btn.setAttribute("aria-label", "Close");
    alert.appendChild(btn);

    // insert at top of container
    if (container.firstChild)
      container.insertBefore(alert, container.firstChild);
    else container.appendChild(alert);

    // auto-remove after 4s
    setTimeout(function () {
      try {
        alert.classList.remove("show");
        alert.classList.add("hide");
        alert.remove();
      } catch (e) {}
    }, 4000);
  } catch (e) {
    try {
      window.alert(text);
    } catch (err) {}
  }
}
