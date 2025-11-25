(() => {
  const api = {
    list: "/api/operator-chat/staff/chats",
    messages: (id) => `/api/operator-chat/staff/chats/${id}/messages`,
    send: (id) => `/api/operator-chat/staff/chats/${id}/send`,
  };

  let chats = [];
  let activeChat = null;
  let isLoading = false;

  const $chatItems = document.getElementById("chatItems");
  const $chatWindowHeader = document.getElementById("chatWindowHeader");
  const $chatMessages = document.getElementById("chatMessages");
  const $chatInput = document.getElementById("chatInput");
  const $chatSendBtn = document.getElementById("chatSendBtn");

  async function safeJson(resp) {
    try {
      const ct =
        (resp.headers && resp.headers.get
          ? resp.headers.get("content-type")
          : "") || "";
      if (!resp.ok) {
        const txt = await resp.text().catch(() => null);
        console.warn("API returned error", resp.status, txt);
        return { success: false, status: resp.status, errorText: txt };
      }
      if (ct.indexOf("application/json") === -1) {
        const txt = await resp.text().catch(() => null);
        return { success: false, errorText: txt };
      }
      return await resp.json();
    } catch (e) {
      return { success: false };
    }
  }

  function renderChatList() {
    if (!$chatItems) return;
    $chatItems.innerHTML = "";
    if (!chats || chats.length === 0) {
      $chatItems.innerHTML =
        '<div style="padding: 20px; text-align: center; color: #999;">No chats</div>';
      return;
    }
    chats.forEach((c) => {
      const el = document.createElement("div");
      el.className =
        "chat-item" +
        (c.unread_count ? " unread" : "") +
        (activeChat === c.id ? " active" : "");
      el.tabIndex = 0;
      el.style.cursor = "pointer";
      const preview = c.last_text ? c.last_text.substring(0, 40) : "(empty)";
      el.innerHTML = `
        <div class="name">${escapeHtml(c.client_name || "User")}</div>
        <div class="preview">${escapeHtml(preview)}</div>
        ${
          c.unread_count
            ? `<div style="font-size: 10px; font-weight: 700; color: #2563eb; margin-top: 4px;">${c.unread_count} new</div>`
            : ""
        }
      `;
      el.onclick = () => openChat(c.id);
      el.onkeypress = (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openChat(c.id);
        }
      };
      $chatItems.appendChild(el);
    });
  }

  function escapeHtml(s) {
    if (!s) return "";
    return String(s).replace(/[&<>\"']/g, function (m) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[m];
    });
  }

  async function loadChats() {
    if (isLoading) return;
    try {
      isLoading = true;
      const r = await fetch(api.list, { credentials: "same-origin" });
      const j = await safeJson(r);
      if (j && j.success && Array.isArray(j.chats)) {
        chats = j.chats || [];
        renderChatList();
      } else {
        console.warn("loadChats unexpected response", j);
      }
    } catch (e) {
      console.warn("Failed to load chats", e);
    } finally {
      isLoading = false;
    }
  }

  async function openChat(id) {
    if (!id) return;
    activeChat = id;
    $chatWindowHeader.textContent = "Loading...";
    if ($chatMessages) $chatMessages.innerHTML = "";
    renderChatList();

    try {
      const r = await fetch(api.messages(id), { credentials: "same-origin" });
      const j = await safeJson(r);
      if (j && j.success && Array.isArray(j.messages)) {
        const chatData = chats.find((c) => c.id === id);
        $chatWindowHeader.innerHTML = `
          <div>
            <strong>${escapeHtml(
              chatData?.client_name || `Chat #${id}`
            )}</strong>
            <div style="font-size: 11px; color: #999; margin-top: 2px;">${escapeHtml(
              chatData?.client_phone || ""
            )}</div>
          </div>
        `;

        if ($chatMessages) {
          $chatMessages.innerHTML = "";
          j.messages.forEach((m) => {
            const mEl = document.createElement("div");
            mEl.className =
              "msg " + (m.sender_type === "user" ? "user" : "operator");
            const sender =
              m.sender_name || (m.sender_type === "user" ? "User" : "Operator");
            const time = m.created_at
              ? new Date(m.created_at).toLocaleTimeString()
              : "";
            mEl.innerHTML = `
              <div style="display: flex; flex-direction: column; gap: 4px; width: 100%;">
                <div style="font-size: 11px; font-weight: 600; opacity: 0.7;">${escapeHtml(
                  sender
                )}</div>
                <div style="word-break: break-word;">${escapeHtml(
                  m.text || ""
                )}</div>
                <div style="font-size: 10px; opacity: 0.6; margin-top: 4px;">${escapeHtml(
                  time
                )}</div>
              </div>
            `;
            $chatMessages.appendChild(mEl);
          });
          $chatMessages.scrollTop = $chatMessages.scrollHeight;
        }
      } else {
        $chatWindowHeader.textContent =
          j && j.errorText ? j.errorText : "Error loading chat";
      }
    } catch (e) {
      console.warn("openChat error", e);
      $chatWindowHeader.textContent = "Error loading chat";
    }
  }

  async function sendMessage() {
    const text = ($chatInput.value || "").trim();
    if (!text || !activeChat) return;

    $chatSendBtn.disabled = true;
    $chatSendBtn.innerHTML = "Sending...";

    try {
      const resp = await fetch(api.send(activeChat), {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": window.STAFF_CSRF_TOKEN || "",
        },
        body: JSON.stringify({ text }),
      });
      const j = await safeJson(resp);
      if (j && j.success) {
        $chatInput.value = "";
        await openChat(activeChat);
        await loadChats();
      } else {
        alert("Message failed to send");
        console.warn("Send failed", j);
      }
    } catch (e) {
      console.warn("sendMessage error", e);
      alert("Error sending message");
    } finally {
      $chatSendBtn.disabled = false;
      $chatSendBtn.innerHTML = "Send";
    }
  }

  // Periodic updates - every 5 seconds
  (window._originalSetInterval || window.setInterval)(() => {
    if (!activeChat) loadChats();
    else {
      loadChats();
      openChat(activeChat);
    }
  }, 5000);

  // Wire UI
  $chatSendBtn.addEventListener("click", sendMessage);
  $chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Initial load
  loadChats();
})();
