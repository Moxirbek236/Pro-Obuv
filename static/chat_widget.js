// Minimal chat widget that mimics telegram-like UI and talks to /api/chat/send
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

  // FAB (bottom-left as requested)
  const fab = create(
    "div",
    {
      class: "public-chat-fab",
      title: "AI yordamchi",
      role: "button",
      tabindex: "0",
    },
    ["🤖"]
  );
  document.body.appendChild(fab);

  // panel
  const panel = create("div", { class: "public-chat-panel" });
  panel.innerHTML = `
    <div class="public-chat-header">AI yordamchi <button class="close" aria-label="close">✕</button></div>
    <div class="public-chat-body"><div class="messages"></div></div>
    <div class="public-chat-input"><input placeholder="Savolingizni yozing..." aria-label="chat input"/><button>Yuborish</button></div>
  `;
  document.body.appendChild(panel);

  const body = panel.querySelector(".public-chat-body .messages");
  const input = panel.querySelector(".public-chat-input input");
  const sendBtn = panel.querySelector(".public-chat-input button");
  const closeBtn = panel.querySelector(".close");

  function appendMessage(text, who = "ai") {
    const m = create("div", { class: "msg " + (who === "me" ? "me" : "ai") }, [
      text,
    ]);
    body.appendChild(m);
    body.scrollTop = body.scrollHeight;
  }

  fab.addEventListener("click", () => panel.classList.toggle("open"));
  closeBtn.addEventListener("click", () => panel.classList.remove("open"));

  async function send() {
    const t = input.value.trim();
    if (!t) return;
    appendMessage(t, "me");
    input.value = "";
    try {
      const payload = { text: t, sender_name: window.USER_NAME || "Guest" };
      const res = await fetch("/api/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const j = await res.json();
      if (j && j.reply) {
        appendMessage(j.reply, "ai");
      } else if (j && j.success === false && j.message) {
        appendMessage("AI: " + j.message, "ai");
      } else {
        appendMessage("Xatolik: server javob bermadi", "ai");
      }
    } catch (e) {
      appendMessage("Xatolik: tarmoq muammosi", "ai");
    }
  }
  sendBtn.addEventListener("click", send);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") send();
  });
})();
