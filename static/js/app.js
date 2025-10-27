// Language switching functionality
function changeLanguage(langCode) {
  const nextPath = window.location.pathname + window.location.search;
  fetch("/api/change-language", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content,
    },
    body: JSON.stringify({ language: langCode, next: nextPath }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        if (data.redirect) {
          window.location.href = data.redirect;
        } else {
          // Fallback: reload the page to apply language change
          window.location.reload();
        }
      } else {
        console.error("Error changing language:", data.message);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}
