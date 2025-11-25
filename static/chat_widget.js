// Minimal chat widget that mimics telegram-like UI and supports both AI and operator chat
(function () {
  const create = (tag, attrs = {}, children = []) => {
    const el = document.createElement(tag);
    Object.keys(attrs).forEach((k) => el.setAttribute(k, attrs[k]));
    (Array.isArray(children) ? children : [children]).forEach((c) => {
      if (typeof c === "string") el.appendChild(document.createTextNode(c));
      else if (c) el.appendChild(c);
    });
    return el;
  };

  function initChatWidget() {
    let mode = "ai"; // "ai" yoki "operator"
    let operatorPollTimer = null;
    let aiMessages = [];

    // FAB (bottom-left as requested)
    const fab = create(
      "div",
      {
        class: "public-chat-fab",
        title: "Onlayn yordam",
        role: "button",
        tabindex: "0",
      },
      ["💬"]
    );
    document.body.appendChild(fab);

    // Kichik menyu: AI, Operator, Savol yuborish
    const menu = create("div", { class: "public-chat-menu" });
    menu.innerHTML = `
      <button class="chat-menu-item" data-action="ai">🤖 AI bilan suhbat</button>
      <button class="chat-menu-item" data-action="operator">👨‍💼 Operator bilan suhbat</button>
      <button class="chat-menu-item" data-action="question">✉️ Savol yuborish</button>
    `;
    document.body.appendChild(menu);

    // panel
    const panel = create("div", { class: "public-chat-panel" });
    panel.innerHTML = `
    <div class="public-chat-header">
      <div class="mode-tabs">
        <button class="mode-btn active" data-mode="ai">🤖 AI</button>
        <button class="mode-btn" data-mode="operator">👨‍💼 Operator</button>
      </div>
      <button class="close" aria-label="close">✖</button>
    </div>
    <div class="public-chat-body"><div class="messages"></div></div>
    <div class="public-chat-input"><input placeholder="Savolingizni yozing..." aria-label="chat input"/><button>Yuborish</button></div>
  `;
    document.body.appendChild(panel);

    const body = panel.querySelector(".public-chat-body .messages");
    const input = panel.querySelector(".public-chat-input input");
    const sendBtn = panel.querySelector(".public-chat-input button");
    const closeBtn = panel.querySelector(".close");
    const modeButtons = panel.querySelectorAll(".mode-btn");
    const menuItems = menu.querySelectorAll(".chat-menu-item");

    function openPanelWithMode(m) {
      switchMode(m);
      panel.classList.add("open");
      menu.classList.remove("open");
      try {
        input.focus();
      } catch (_) {}
    }

    function renderMessages(list) {
      body.innerHTML = "";
      list.forEach((m) => {
        const whoClass = m.who === "me" ? "me" : "ai";
        const node = create("div", { class: "msg " + whoClass }, [m.text]);
        body.appendChild(node);
      });
      body.scrollTop = body.scrollHeight;
    }

    function appendAiMessage(text, who) {
      aiMessages.push({ text, who });
      if (mode === "ai") {
        renderMessages(aiMessages);
      }
    }

    async function fetchOperatorHistory() {
      if (mode !== "operator") return;
      try {
        const res = await fetch("/api/operator-chat/user/history", {
          method: "GET",
          headers: { Accept: "application/json" },
        });
        const j = await res.json().catch(() => ({}));
        const msgs = (j && j.messages) || [];
        const mapped = msgs.map((m) => ({
          text: m.text || "",
          who: m.sender_type === "user" ? "me" : "ai",
        }));
        if (mode === "operator") {
          renderMessages(mapped);
        }
      } catch (e) {
        // silent
      }
    }

    function switchMode(newMode) {
      if (mode === newMode) return;
      mode = newMode;
      modeButtons.forEach((b) => {
        if (b.getAttribute("data-mode") === mode) b.classList.add("active");
        else b.classList.remove("active");
      });
      if (mode === "ai") {
        // stop operator polling and render last AI chat
        if (operatorPollTimer) {
          clearInterval(operatorPollTimer);
          operatorPollTimer = null;
        }
        renderMessages(aiMessages);
        input.placeholder = "Savolingizni yozing...";
      } else {
        // start operator polling
        renderMessages([]);
        input.placeholder = "Operator uchun xabar yozing...";
        fetchOperatorHistory();
        if (!operatorPollTimer) {
          // Use the original native setInterval in case a global proxy disables intervals
          operatorPollTimer = (
            window._originalSetInterval || window.setInterval
          )(fetchOperatorHistory, 5000);
        }
      }
    }

    // FAB bosilganda avval kichik menyuni ko'rsatamiz/berkitamiz
    fab.addEventListener("click", () => {
      const isOpen = menu.classList.contains("open");
      if (isOpen) menu.classList.remove("open");
      else menu.classList.add("open");
    });

    // Menyu elementlari: AI / Operator / Savol yuborish
    menuItems.forEach((btn) => {
      btn.addEventListener("click", function () {
        const action = this.getAttribute("data-action");
        if (action === "ai") {
          openPanelWithMode("ai");
        } else if (action === "operator") {
          openPanelWithMode("operator");
        } else if (action === "question") {
          // Savol yuborish: superadmin uchun oddiy forma
          const q = prompt("Superadminga savolingizni yozing:");
          if (!q) {
            menu.classList.remove("open");
            return;
          }
          try {
            fetch("/api/chat/superadmin-question", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ text: q, source: "web" }),
            })
              .then((r) => r.json().catch(() => ({})))
              .then((j) => {
                alert((j && j.message) || "Savolingiz yuborildi.");
              })
              .catch(() => {
                alert("Savol yuborishda xatolik yuz berdi.");
              });
          } catch (_) {
            alert("Savol yuborishda xatolik yuz berdi.");
          }
          menu.classList.remove("open");
        }
      });
    });

    closeBtn.addEventListener("click", () => {
      panel.classList.remove("open");
    });

    modeButtons.forEach((btn) => {
      btn.addEventListener("click", function () {
        const m = this.getAttribute("data-mode") || "ai";
        switchMode(m);
      });
    });

    async function send() {
      const t = input.value.trim();
      if (!t) return;

      if (mode === "ai") {
        appendAiMessage(t, "me");
        input.value = "";
        try {
          const payload = { text: t, sender_name: window.USER_NAME || "Guest" };
          const res = await fetch("/api/chat/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          const j = await res.json().catch(() => ({}));
          if (j && j.reply) {
            appendAiMessage(j.reply, "ai");
          } else if (j && j.success === false && j.message) {
            appendAiMessage("AI: " + j.message, "ai");
          } else {
            appendAiMessage("Xatolik: server javob bermadi", "ai");
          }
        } catch (e) {
          appendAiMessage("Xatolik: tarmoq muammosi", "ai");
        }
      } else {
        // operator rejimi
        input.value = "";
        try {
          const payload = {
            text: t,
            sender_name: window.USER_NAME || "Guest",
            phone: window.USER_PHONE || "",
            source: "web",
          };
          const res = await fetch("/api/operator-chat/user/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          const j = await res.json().catch(() => ({}));
          const msg = (j && j.message) || "Xabar operatorga yuborildi.";
          // Show acknowledgement as bot message
          renderMessages([...(body.innerText ? [] : [])]);
          // Just append short ack to current view
          const ackNode = create("div", { class: "msg ai" }, [msg]);
          body.appendChild(ackNode);
          body.scrollTop = body.scrollHeight;
          // Refresh full history after sending
          fetchOperatorHistory();
        } catch (e) {
          const errNode = create("div", { class: "msg ai" }, [
            "Xatolik: xabar operatorga yuborilmadi",
          ]);
          body.appendChild(errNode);
          body.scrollTop = body.scrollHeight;
        }
      }
    }

    sendBtn.addEventListener("click", send);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") send();
    });
  }

  // Ensure the widget initializes after the document body exists
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initChatWidget);
  } else {
    // DOM already ready
    initChatWidget();
  }
})();
