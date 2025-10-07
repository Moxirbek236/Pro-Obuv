
          // Load chats function
          function loadChats() {
            const IS_USER = (window.CURRENT_MEMBER_TYPE === 'user');
            fetch("/api/chats")
                .then(safeJson)
                .then((data) => {
                  listEl.innerHTML = "";
                  if (!data || !Array.isArray(data.chats)) return;

                  let chats = data.chats;
                  if (IS_USER) {
                    const forbiddenNames = new Set(['All Team','Staffs','Couriers']);
                    chats = chats.filter(m => !(m.is_group === 1 || m.is_group === true || forbiddenNames.has((m.name||'').trim())));
                  }

                  const colorPalette = ['#16a34a','#0ea5e9','#f97316','#7c3aed','#ef4444','#06b6d4','#f59e0b'];
                  const nameColorMap = {};
                  function pickColorFor(idOrName){
                    const key = String(idOrName || '').trim();
                    if(!key) return '#6b7280';
                    if(nameColorMap[key]) return nameColorMap[key];
                    let h=0; for(let i=0;i<key.length;i++){ h = (h<<5)-h + key.charCodeAt(i); h |= 0 }
                    const idx = Math.abs(h) % colorPalette.length;
                    nameColorMap[key] = colorPalette[idx];
                    return nameColorMap[key];
                  }

                  data.chats.forEach((m) => {
                    const div = document.createElement('div');
                    div.className = 'chat-item d-flex align-items-center';
                    div.style.gap = '8px';
                    div.title = m.name || m.display_name || 'Chat';

                    const av = document.createElement('div');
                    av.className = 'chat-avatar';
                    av.style.background = pickColorFor(m.id || m.name || m.display_name);
                    if(m.avatar){ const img = document.createElement('img'); img.src = m.avatar; img.style.width='36px'; img.style.height='36px'; img.style.borderRadius='50%'; img.style.objectFit='cover'; av.appendChild(img); }
                    // attach member metadata when available for profile popup
                    if(m.member_type && m.member_id){ av.dataset.memberType = m.member_type; av.dataset.memberId = m.member_id; }
                    // click avatar to view profile
                    av.addEventListener('click', (ev)=>{ ev.stopPropagation(); if(av.dataset.memberType && av.dataset.memberId) fetchMemberProfile(av.dataset.memberType, av.dataset.memberId); });

                    const meta = document.createElement('div');
                    meta.style.flex = '1';
                    meta.innerHTML = `<div style="font-weight:600">${escapeHtml(m.name || m.display_name || 'Chat')}</div><div style="font-size:12px;color:#666">${escapeHtml(m.preview || '')}</div>`;

                    div.appendChild(av);
                    div.appendChild(meta);

                    div.dataset.chatId = m.id;
                    div.addEventListener('click', ()=>{
                      openChat(m.id, m.name || m.display_name || 'Chat');
                    });

                    listEl.appendChild(div);
                  });
                })
                .catch((e) => {
                  // console.log("Load chats error", e);
                });
            }

            function createOrOpenPrivateChat(member) {
              // call POST /api/chats to create private chat with selected member
              const payload = {
                member_type: member.member_type,
                member_id: member.member_id,
              };
              fetch("/api/chats", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  "X-CSRF-Token":
                    typeof CSRF_TOKEN !== "undefined" ? CSRF_TOKEN : "",
                },
                body: JSON.stringify(payload),
              })
                .then(safeJson)
                .then((resp) => {
                  if (resp && resp.success && resp.chat_id) {
                    // open the new chat
                    {# openChat(resp.chat_id, resp.name || "Chat " + resp.chat_id); #}
                  } else {
                    // fallback: refresh chat list
                    loadChats();
                  }
                })
                .catch((e) => {
                  // console.log("Create private chat error", e);
                  loadChats();
                });
            }

            function openChat(chatId, name) {
              activeChatId = chatId;
              // ensure panel is visible
              if (panel.style.display !== 'block') togglePanel();
              messagesEl.innerHTML = '<div class="text-muted">Yuklanmoqda...</div>';
              // notifications are handled via separate FAB, do not inject notify button into chat header

              fetch(`/api/chats/${chatId}/messages?limit=200`)
                .then(safeJson)
                .then((data) => {
                  messagesEl.innerHTML = "";
                  if (!data || !data.messages)
                    return (messagesEl.innerHTML =
                      '<div class="text-muted">Xabarlar topilmadi</div>');
                  data.messages.forEach((m) => {
                    const d = document.createElement("div");
                    d.className = "chat-message d-flex gap-2";

                    const avatar = document.createElement("div");
                    avatar.className = "chat-avatar";
                    if (m.sender_avatar) {
                      const img = document.createElement("img");
                      img.src = m.sender_avatar;
                      img.style.width = "36px";
                      img.style.height = "36px";
                      img.style.borderRadius = "50%";
                      img.style.objectFit = "cover";
                      avatar.appendChild(img);
                    }
                    // Attach sender metadata for profile click if available
                    if(m.sender_type && m.sender_id){ avatar.dataset.memberType = m.sender_type; avatar.dataset.memberId = m.sender_id; }
                    avatar.addEventListener('click', (ev)=>{ ev.stopPropagation(); if(avatar.dataset.memberType && avatar.dataset.memberId) fetchMemberProfile(avatar.dataset.memberType, avatar.dataset.memberId); });

                    const content = document.createElement("div");
                    const header = document.createElement("div");
                    header.style.fontSize = "12px";
                    header.style.color = "#666";
                    header.textContent = `${m.sender_name || m.sender_type || "N/A"} ${m.created_at || ""}`;

                    const bodyDiv = document.createElement("div");
                    bodyDiv.innerHTML = escapeHtml(m.text);
                    bodyDiv.style.background = "#f1f3f5";
                    bodyDiv.style.padding = "8px 10px";
                    bodyDiv.style.borderRadius = "8px";

                    content.appendChild(header);
                    content.appendChild(bodyDiv);

                    d.appendChild(avatar);
                    d.appendChild(content);
                    messagesEl.appendChild(d);
                  });
                  messagesEl.scrollTop = messagesEl.scrollHeight;
                  // After opening, clear unread count badge by refreshing unread count
                  updateChatUnreadCount();
                })
                .catch((e) => {
                  messagesEl.innerHTML =
                    '<div class="text-danger">Xatolik yuz berdi</div>';
                  // console.log(e);
                });
            }

            function escapeHtml(s) {
              return (s || "").replace(/[&<>"']/g, function (c) {
                return {
                  "&": "&amp;",
                  "<": "&lt;",
                  ">": "&gt;",
                  '"': "&quot;",
                  "'": "&#39;",
                }[c];
              });
            }

            sendBtn.addEventListener("click", () => {
              const text = textEl.value.trim();
              if (!text || !activeChatId) return;
              fetch(`/api/chats/${activeChatId}/messages`, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  "X-CSRF-Token":
                    typeof CSRF_TOKEN !== "undefined" ? CSRF_TOKEN : "",
                },
                body: JSON.stringify({ text }),
              })
                .then(safeJson)
                .then((resp) => {
                  if (resp && resp.success) {
                    textEl.value = "";
                    {# openChat(activeChatId); #}
                  }
                })
                .catch((e) => {
                  // console.log("Send chat error", e);
                });
            });

            // Poll for new messages every 7s when panel open
            setInterval(() => {
              if (panel.style.display === "block" && activeChatId) {
                // reload messages for active chat and render Telegram-like bubbles
                fetch(`/api/chats/${activeChatId}/messages?limit=200`)
                  .then(safeJson)
                  .then((d) => {
                    if (d && d.messages) {
                      messagesEl.innerHTML = '';
                      d.messages.forEach((m) => {
                        const wrapper = document.createElement('div');
                        wrapper.style.display = 'flex';
                        wrapper.style.marginBottom = '8px';
                        const isMe = window.CURRENT_MEMBER_ID && String(m.sender_id) === String(window.CURRENT_MEMBER_ID);
                        wrapper.style.justifyContent = isMe ? 'flex-end' : 'flex-start';

                        const bubble = document.createElement('div');
                        bubble.className = 'tg-bubble ' + (isMe ? 'tg-bubble-right' : 'tg-bubble-left');
                        bubble.innerHTML = `<div style="font-size:12px;color:#6b7280;margin-bottom:4px">${escapeHtml(m.sender_name||m.sender_type||'')}</div><div>${escapeHtml(m.text||'')}</div><div style="font-size:10px;color:#9ca3af;margin-top:6px;text-align:${isMe?'right':'left'}">${escapeHtml(m.created_at||'')}</div>`;
                        wrapper.appendChild(bubble);
                        messagesEl.appendChild(wrapper);
                      });
                      messagesEl.scrollTop = messagesEl.scrollHeight;
                    }
                  })
                  .catch(() => {});
              }
            }, 7000);

            // Chat unread badge updater
            function updateChatUnreadCount(){
              fetch('/api/chat-unread-count').then(safeJson).then((r)=>{
                try{
                  const unread = (r && r.unread) || 0;
                  const badge = document.getElementById('chat-unread-count');
                  if(!badge) return;
                  if(unread>0){ badge.style.display='inline-block'; badge.textContent = unread>99? '99+': String(unread); }
                  else badge.style.display='none';
                }catch(e){ }
              }).catch(()=>{});
            }

            // Update unread count on load and every 10s
            updateChatUnreadCount();
            setInterval(updateChatUnreadCount, 10000);

            // Notify modal handlers
            const notifyModal = document.getElementById("notifyModal");
            const notifyCancelBtn = document.getElementById("notifyCancelBtn");
            const notifySendBtn = document.getElementById("notifySendBtn");
            if (notifyCancelBtn)
              notifyCancelBtn.addEventListener("click", () => {
                if (notifyModal) {
                  notifyModal.style.display = "none";
                  // clear inputs
                  const t = document.getElementById('notifyTitle');
                  const b = document.getElementById('notifyBody');
                  if (t) t.value = '';
                  if (b) b.value = '';
                }
              });
            // Server will render IS_SUPER_ADMIN true/false
            const IS_SUPER_ADMIN = {{ (session.get('super_admin') and True) | tojson }};
            // Current member context for chat (used to align "my" messages)
            window.CURRENT_MEMBER_ID = {{ (session.get('user_id') or session.get('staff_id') or session.get('courier_id') or None) | tojson }};
            window.CURRENT_MEMBER_TYPE = {{ ('user' if session.get('user_id') else ('staff' if session.get('staff_id') else ('courier' if session.get('courier_id') else 'anonymous'))) | tojson }};
            if (IS_SUPER_ADMIN && notifySendBtn) {
              // Only attach send handler for superadmin
              notifySendBtn.addEventListener("click", () => {
                const title = document.getElementById("notifyTitle").value.trim();
                const body = document.getElementById("notifyBody").value.trim();
                if (!title || !body) return alert("Iltimos sarlavha va matn kiriting");

                const isBroadcast = confirm('Barcha foydalanuvchilarga yuborilsinmi? OK = BARCHA; Cancel = Yagona qabul qiluvchi');
                let payload = { title, body };
                if (isBroadcast) {
                  const group = prompt('Qaysi guruh? (all, users, staff, couriers)', 'all') || 'all';
                  payload.recipient_type = group;
                } else {
                  const rType = prompt('Qabul qiluvchi turi? (users, staff, couriers)', 'users');
                  const rId = prompt('Qabul qiluvchining id raqami', '');
                  if (!rId) return alert('Iltimos id kiriting');
                  payload.recipient_type = rType || 'users';
                  payload.recipient_id = parseInt(rId, 10);
                }

                fetch("/super-admin/send-notification", {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    "X-CSRF-Token": typeof CSRF_TOKEN !== "undefined" ? CSRF_TOKEN : "",
                  },
                  body: JSON.stringify(payload),
                })
                  .then(safeJson)
                  .then((r) => {
                    if (r && r.success) {
                      alert("Bildirishnoma yuborildi");
                      if (notifyModal) {
                        notifyModal.style.display = "none";
                        const t = document.getElementById('notifyTitle');
                        const b = document.getElementById('notifyBody');
                        if (t) t.value = '';
                        if (b) b.value = '';
                      }
                    } else alert("Yuborishda xatolik: " + (r && r.message ? r.message : ''));
                  })
                  .catch((e) => {
                    alert("Yuborishda xatolik");
                    // console.log(e);
                  });
              });
            }

      // Notification count updater
            function updateNotifyCount() {
              fetch("/api/notifications")
                .then(safeJson)
                .then((r) => {
                  try {
                    const notes = (r && r.notifications) || [];
                    // count unread (read_flag === 0) if present
                    let unread = 0;
                    notes.forEach((n) => {
                      if (
                        n.read_flag === 0 ||
                        n.read_flag === "0" ||
                        n.read_flag === null
                      )
                        unread++;
                    });
                    const badges = document.querySelectorAll("#notify-count");
                    badges.forEach((b) => {
                      if (unread > 0) {
                        b.style.display = "inline-block";
                        b.textContent = unread > 99 ? "99+" : String(unread);
                      } else {
                        b.style.display = "none";
                      }
                    });
                  } catch (e) {
                    // console.log("notify count parse error", e);
                  }
                })
                .catch((e) => {
                  // console.log("Notify count fetch error", e);
                });
            }

            // Fetch and show member profile in popup modal
            function fetchMemberProfile(memberType, memberId){
              fetch(`/api/member/${memberType}/${memberId}`)
                .then(safeJson)
                .then((r)=>{ if(r && r.success && r.profile) showMemberProfile(r.profile); })
                .catch((e)=>{
                  // console.log('Member profile fetch error', e);
                });
            }

            function showMemberProfile(profile){
              if(!profile) return;
              const modal = document.getElementById('memberProfileModal');
              if(!modal) return;
              document.getElementById('memberProfileAvatar').src = profile.avatar || '/static/images/default-avatar.svg';
              document.getElementById('memberProfileName').textContent = profile.name || profile.username || ('#'+profile.id);
              document.getElementById('memberProfileRole').textContent = (profile.role || '').toString();
              document.getElementById('memberProfileId').textContent = profile.id || '';
              document.getElementById('memberProfileUsername').textContent = profile.username || '';
              document.getElementById('memberProfilePhone').textContent = profile.phone || '';
              document.getElementById('memberProfileBirth').textContent = profile.birth_date || '';
              modal.style.display = 'block';
            }

            const memberProfileClose = document.getElementById('memberProfileClose');
            if(memberProfileClose) memberProfileClose.addEventListener('click', ()=>{ const m = document.getElementById('memberProfileModal'); if(m) m.style.display='none'; });

            // Update on load and every 20s
            updateNotifyCount();
            setInterval(updateNotifyCount, 20000);

            // When opening the notify modal, mark visible notifications as read
            const notifyButtons = document.querySelectorAll('.nav-notify');
            notifyButtons.forEach((b) => b.addEventListener('click', async ()=>{
              if(!IS_SUPER_ADMIN){
                // non-super-admin: fetch latest notifications and show read-only viewer
                try{
                  const res = await fetch('/api/notifications');
                  const data = await res.json().catch(()=>({}));
                  const list = (data && data.notifications) || [];
                  const preview = document.getElementById('notifyListPreview');
                  if(preview){
                    preview.innerHTML = '';
                    if(list.length===0) preview.innerHTML = '<div class="text-muted">Hech qanday bildirishnoma yo\'q</div>';
                    list.slice(0,10).forEach(n=>{
                      const item = document.createElement('div');
                      item.className = 'mb-2';
                      item.innerHTML = `<div style="font-weight:600">${escapeHtml(n.title || '')}</div><div style="font-size:12px;color:#666">${escapeHtml(n.body || '')}</div><hr/>`;
                      preview.appendChild(item);
                    });
                  }
                  if(notifyModal) notifyModal.style.display = 'block';
                  // mark read for this recipient (best-effort)
                  fetch('/api/notifications/mark-read', { method: 'POST', headers: { 'X-CSRF-Token': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '' } }).then(()=>updateNotifyCount()).catch(()=>{});
                }catch(e){
                  // console.log('Failed to load notifications', e);
                  if(notifyModal) notifyModal.style.display = 'block';
                }
                return;
              }
              // super admin opens composer modal
              if(notifyModal) notifyModal.style.display = 'block';
            }));
            // Close viewer button handler for non-superadmins
            const notifyCloseViewer = document.getElementById('notifyCloseViewer');
            if(notifyCloseViewer) notifyCloseViewer.addEventListener('click', ()=>{ const m = document.getElementById('notifyModal'); if(m) m.style.display='none'; });
          })();
    