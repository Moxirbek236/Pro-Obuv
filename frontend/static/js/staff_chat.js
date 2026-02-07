// Staff Operator Chat UI (standalone page)
// Expects elements:
// - #chatItems, #chatWindowHeader, #chatMessages, #chatInput, #chatSendBtn
// Depends on endpoints:
// - GET  /api/operator-chat/staff/chats
// - GET  /api/operator-chat/staff/chats/<id>/messages
// - POST /api/operator-chat/staff/chats/<id>/send

(function () {
  "use strict";

  const $ = (sel) => document.querySelector(sel);

  let currentChatId = null;
  let chatsPollTimer = null;
  let messagesPollTimer = null;

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  async function fetchJson(url, opts) {
    const res = await fetch(url, opts || {});
    try {
      return await res.json();
    } catch (_) {
      return null;
    }
  }

  function renderChats(chats) {
    const listEl = $("#chatItems");
    if (!listEl) return;

    if (!Array.isArray(chats) || chats.length === 0) {
      listEl.innerHTML =
        '<div class="text-center p-3 text-muted small">Chatlar yo‘q</div>';
      return;
    }

    listEl.innerHTML = "";
    chats.forEach((c) => {
      const id = c.id;
      const name = c.client_name || "Mijoz";
      const last = c.last_text || "";
      const unread = Number(c.unread_count || 0);
      const isActive = currentChatId === id;

      const item = document.createElement("button");
      item.type = "button";
      item.className =
        "w-100 text-start border-0 bg-transparent p-0 chat-list-item";
      item.innerHTML = `
        <div class="px-3 py-2 border-bottom ${c.is_new ? "bg-warning bg-opacity-10" : ""} ${isActive ? "bg-primary bg-opacity-10" : ""}">
          <div class="d-flex justify-content-between align-items-center">
            <span class="fw-bold small text-truncate" style="max-width: 220px;">${escapeHtml(
              name
            )}</span>
            ${
              unread > 0
                ? `<span class="badge bg-danger rounded-pill">${unread}</span>`
                : ""
            }
          </div>
          <div class="text-muted small text-truncate">${escapeHtml(last)}</div>
        </div>
      `;
      item.addEventListener("click", () => {
        openChat(id, name);
      });
      listEl.appendChild(item);
    });
  }

  function renderMessages(messages) {
    const box = $("#chatMessages");
    if (!box) return;

    box.innerHTML = "";
    if (!Array.isArray(messages) || messages.length === 0) {
      box.innerHTML =
        '<div class="text-center text-muted small mt-5">Xabarlar yo‘q</div>';
      return;
    }

    messages.forEach((m) => {
      const div = document.createElement("div");
      const isUser = m.sender_type === "user";
      div.className = `mb-2 p-2 rounded small chat-message ${isUser ? "user" : "staff"}`;
      div.textContent = m.text || "";
      box.appendChild(div);
    });
    box.scrollTop = box.scrollHeight;
  }

  async function loadChats() {
    const j = await fetchJson("/api/operator-chat/staff/chats");
    if (!j || !j.success) {
      renderChats([]);
      return;
    }
    renderChats(j.chats || []);
  }

  async function loadMessages(chatId) {
    const j = await fetchJson(`/api/operator-chat/staff/chats/${chatId}/messages`);
    renderMessages((j && j.messages) || []);
  }

  async function openChat(chatId, name) {
    currentChatId = chatId;

    const header = $("#chatWindowHeader");
    if (header) {
      header.innerHTML = `<span class="fw-bold">${escapeHtml(name)}</span>`;
    }

    await loadMessages(chatId);
    await loadChats(); // refresh unread counters + active highlight

    // poll messages for current chat
    if (messagesPollTimer) window.clearInterval(messagesPollTimer);
    messagesPollTimer = window.setInterval(() => {
      if (currentChatId) loadMessages(currentChatId).catch(() => {});
    }, 5000);
  }

  async function sendMessage() {
    const inp = $("#chatInput");
    if (!inp) return;

    const text = (inp.value || "").trim();
    if (!text || !currentChatId) return;

    const csrf =
      window.STAFF_CSRF_TOKEN || window.CSRF_TOKEN || window.csrf_token || "";

    const j = await fetchJson(
      `/api/operator-chat/staff/chats/${currentChatId}/send`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrf,
        },
        body: JSON.stringify({ text }),
      }
    );

    if (j && j.success) {
      inp.value = "";
      await loadMessages(currentChatId);
      await loadChats();
    }
  }

  function startPolling() {
    if (chatsPollTimer) window.clearInterval(chatsPollTimer);
    chatsPollTimer = window.setInterval(() => {
      loadChats().catch(() => {});
    }, 7000);
  }

  function bindUi() {
    const sendBtn = $("#chatSendBtn");
    const inp = $("#chatInput");
    const form = $("#chatSendForm");

    if (sendBtn) sendBtn.addEventListener("click", () => sendMessage().catch(() => {}));

    if (form) {
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        sendMessage().catch(() => {});
      });
    }

    if (inp) {
      inp.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          sendMessage().catch(() => {});
        }
      });
    }
  }

  window.StaffChat = {
    reloadChats: () => loadChats().catch(() => {}),
  };

  document.addEventListener("DOMContentLoaded", () => {
    bindUi();
    loadChats().catch(() => {});
    startPolling();
  });
})();

