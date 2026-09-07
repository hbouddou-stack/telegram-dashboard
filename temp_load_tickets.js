function loadStudentTickets() {
            const list = document.getElementById('student-tickets-list');
            const tid = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.id : null) || null;
            if (!tid) {
                list.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-2);">لم يتم التعرف على حسابك. افتح التطبيق عبر تليجرام.</div>`;
                return;
            }
            try {
                const res = await fetch(`${BOT_BASE}/api/tickets/student?telegram_id=${tid}`);
                if (res.ok) {
                    const data = await res.json();
                    renderStudentTickets(data.tickets || []);
                } else {
                    renderStudentTickets([]);
                }
            } catch(e) {
                renderStudentTickets([]);
            }
        }

                function renderStudentTickets(tickets) {
            studentAllTicketsList = tickets || [];
            const list = document.getElementById('student-tickets-list');
            if (!list) return;
            
            studentLoadedTicketsMap = {};

            // Count for filter pills
            const resolvedList = studentAllTicketsList.filter(t => t.status === 'resolved' || t.status === 'محلولة');
            const pendingList = studentAllTicketsList.filter(t => !resolvedList.includes(t));
            
            const cntAll = document.getElementById('cnt-all');
            const cntPending = document.getElementById('cnt-pending');
            const cntResolved = document.getElementById('cnt-resolved');
            if (cntAll) cntAll.innerText = studentAllTicketsList.length;
            if (cntPending) cntPending.innerText = pendingList.length;
            if (cntResolved) cntResolved.innerText = resolvedList.length;

            const badge = document.getElementById('inbox-badge');
            if (badge) {
                if (pendingList.length > 0) {
                    badge.innerText = pendingList.length;
                    badge.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                }
            }

            if (!studentAllTicketsList || studentAllTicketsList.length === 0) {
                list.innerHTML = `
                <div style="text-align:center; padding:40px 20px; background:var(--surface); border-radius:16px; border:1px dashed rgba(255,255,255,0.15); margin-top:10px;">
                    <div style="font-size:3rem; margin-bottom:15px;">📫</div>
                    <h3 style="font-size:1.1rem; margin:0 0 10px 0; color:var(--text-1);">صندوق الرسائل فارغ</h3>
                    <p style="font-size:0.88rem; color:var(--text-2); line-height:1.6; margin:0 0 20px 0;">
                        ستظهر هنا جميع تذاكر الدعم ومتابعة الردود من إدارة الأكاديمية أولاً بأول.
                    </p>
                    <button class="btn-primary" style="width:auto; padding:12px 28px; margin:0 auto; display:inline-flex; align-items:center; gap:8px;" onclick="switchTab('new')">
                        <span>✍️</span> فتح تذكرة جديدة
                    </button>
                </div>`;
                return;
            }

            // Filter according to active pill
            let displayTickets = [...studentAllTicketsList];
            if (activeInboxFilter === 'pending') {
                displayTickets = pendingList;
            } else if (activeInboxFilter === 'resolved') {
                displayTickets = resolvedList;
            }

            // Newest first for display
            displayTickets.sort((a,b) => (new Date(b.timestamp || 0)) - (new Date(a.timestamp || 0)));

            if (displayTickets.length === 0) {
                list.innerHTML = `<div style="text-align:center; color:var(--text-2); padding:30px;">لا توجد تذاكر في هذا التصنيف.</div>`;
                return;
            }

            list.innerHTML = displayTickets.map(t => {
                studentLoadedTicketsMap[t.id] = t;
                const isResolved = (t.status === 'resolved' || t.status === 'محلولة');
                const isInProgress = (t.status === 'in_progress' || t.status === 'قيد المعالجة');
                const statusColor = isResolved ? '#2ecc71' : (isInProgress ? '#3498db' : '#f39c12');
                const statusBg = isResolved ? 'rgba(46,204,113,0.1)' : (isInProgress ? 'rgba(52,152,219,0.1)' : 'rgba(243,156,18,0.1)');
                const statusLabel = isResolved ? '🟢 تم الحل' : (isInProgress ? '🔵 قيد المعالجة' : '🟠 في انتظار الرد');
                const cardTint = isResolved ? 'rgba(46,204,113,0.03)' : 'rgba(243,156,18,0.03)';
                
                const date = t.timestamp ? new Date(t.timestamp).toLocaleDateString('ar-MA') : '';
                const subjectTitle = t.subtheme || t.theme || 'استفسار عام';
                const messageSnippet = (t.message || t.text || '').replace(/\\n/g, ' ').substring(0, 85);
                const hasAttachment = (t.has_attachment || t.file_path || t.file_data || (t.message && t.message.includes('[مرفق]')));
                const attachBadge = hasAttachment ? `<span style="background:rgba(241,196,15,0.12); color:var(--accent); border:1px solid rgba(241,196,15,0.3); padding:3px 9px; border-radius:8px; font-size:0.75rem; display:inline-flex; align-items:center; gap:4px;">📎 مرفق</span>` : '';

                return `
                <div onclick="openTicketThread(${t.id})" style="background:linear-gradient(90deg, rgba(255,255,255,0.03) 0%, ${cardTint} 100%); border:1px solid rgba(255,255,255,0.09); padding:16px; border-radius:14px; margin-bottom:12px; cursor:pointer; transition:all 0.2s; border-right:4px solid ${statusColor};" onmouseover="this.style.borderColor='var(--accent)'" onmouseout="this.style.borderColor='rgba(255,255,255,0.09)'">
                    <!-- Top Info Bar -->
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <span style="font-weight:800; font-size:0.92rem; color:var(--accent); letter-spacing:0.5px;">#TK-${t.id}</span>
                        <span style="color:${statusColor}; font-size:0.75rem; background:${statusBg}; border:1px solid ${statusColor}; padding:3px 10px; border-radius:12px; font-weight:bold;">${statusLabel}</span>
                    </div>

                    <!-- Subject Title -->
                    <div style="font-weight:700; font-size:0.98rem; color:#ffffff; margin-bottom:6px; line-height:1.4;">
                        ${subjectTitle}
                    </div>

                    <!-- Category Pills (Non-clickable) -->
                    <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px;">
                        <span style="background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); color:var(--text-2); padding:2px 8px; border-radius:6px; font-size:0.76rem;">🏷️ ${t.theme || 'عام'}</span>
                        ${t.subtheme && t.subtheme !== subjectTitle ? `<span style="background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); color:var(--text-2); padding:2px 8px; border-radius:6px; font-size:0.76rem;">🔹 ${t.subtheme}</span>` : ''}
                        ${attachBadge}
                    </div>

                    <!-- Message Preview -->
                    <div style="font-size:0.84rem; color:var(--text-2); margin-bottom:12px; line-height:1.4; opacity:0.85; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        ${messageSnippet}${messageSnippet.length >= 85 ? '...' : ''}
                    </div>

                    <!-- Footer Bar -->
                    <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(255,255,255,0.05); padding-top:10px;">
                        <span style="font-size:0.75rem; color:rgba(255,255,255,0.4);">${date}</span>
                        <span style="font-size:0.82rem; color:var(--accent); font-weight:bold; display:inline-flex; align-items:center; gap:4px;">عرض المحادثة 💬 ➔</span>
                    </div>
                </div>`;
            }).join('');
        }

        window.onload = () => {
            loadStudentFaq();
            loadStudentTickets();
        };
        
        
                // ========================
        // LIVE PREDICTIVE FAQ (ULTRA SMART)
        // ========================
        function normalizeArabic(text) {
            if (!text) return '';
            return String(text)
                .toLowerCase()
                .replace(/[إأآا]/g, 'ا')
                .replace(/[ىي]/g, 'ي')
                .replace(/ة/g, 'ه')
                .replace(/[\u064B-\u065F\u0670]/g, '')
                .trim();
        }

        let liveSearchTimer;
        function livePredictiveFaqSearch(text) {
            const rawQuery = (text || '').trim();
            const box = document.getElementById('predictive-faq-box');
            const resEl = document.getElementById('predictive-faq-results');
            if (!box || !resEl) return;
            
            if (rawQuery.length < 2) {
                box.style.display = 'none';
                return;
            }
            
            clearTimeout(liveSearchTimer);
            liveSearchTimer = setTimeout(() => {
                const normQuery = normalizeArabic(rawQuery);
                const words = normQuery.split(/\s+/).filter(w => w.length >= 2);
                
                const searchTokens = [];
                words.forEach(w => {
                    searchTokens.push(w);
                    if (w.startsWith('ال') && w.length > 3) {
                        searchTokens.push(w.substring(2));
                    }
                });

                const dataset = (studentFaqAll && studentFaqAll.length > 0) ? studentFaqAll : defaultFallbackFaq;
                
                const matches = dataset.filter(item => {
                    const qNorm = normalizeArabic(item.question);
                    const aNorm = normalizeArabic(item.answer);
                    const catNorm = normalizeArabic(item.category || '');
                    const combined = qNorm + ' ' + aNorm + ' ' + catNorm;
                    return searchTokens.some(token => combined.includes(token));
                }).slice(0, 3);
                
                if (matches.length === 0) {
                    box.style.display = 'none';
                    return;
                }
                
                resEl.innerHTML = matches.map(m => `
                    <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:10px; margin-top:8px;">
                        <div style="font-weight:bold; font-size:0.88rem; color:var(--text-1); cursor:pointer; display:flex; justify-content:space-between; align-items:center;" onclick="togglePredictiveAnswer(${m.id})">
                            <span>❓ ${m.question}</span>
                            <span style="font-size:0.75rem; color:var(--accent); background:rgba(241,196,15,0.15); padding:2px 8px; border-radius:10px;">عرض الحل ➔</span>
                        </div>
                        <div id="pred-ans-${m.id}" style="display:none; margin-top:8px; font-size:0.84rem; color:var(--text-2); border-top:1px solid rgba(255,255,255,0.08); padding-top:8px; line-height:1.5;">
                            ${(m.answer || '').replace(/\\n/g, "<br>")}
                            <div style="margin-top:10px; text-align:left;">
                                <button onclick="acceptPredictiveSolution(${m.id})" style="background:#2ecc71; color:white; border:none; padding:6px 14px; border-radius:8px; font-size:0.78rem; cursor:pointer; font-family:'Tajawal'; font-weight:bold;">
                                    ✅ هذه الإجابة حلت مشكلتي
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('');
                
                box.style.display = 'block';
            }, 50);
        }

        function togglePredictiveAnswer(id) {
            const el = document.getElementById(`pred-ans-${id}`);
            if (el) {
                el.style.display = (el.style.display === 'none' || !el.style.display) ? 'block' : 'none';
            }
        }

        function acceptPredictiveSolution(id) {
            resolveTicket();
        }

        // ========================
        // TICKET CONVERSATION THREAD & CSAT
        // ========================
        let currentThreadTicketId = null;
        let studentLoadedTicketsMap = {};
        let studentAllTicketsList = [];
        let activeInboxFilter = 'all';

        function filterStudentInbox(filterType, btn) {
            activeInboxFilter = filterType;
            document.querySelectorAll('#inbox-filter-pills .faq-cat-btn').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');
            renderStudentTickets(studentAllTicketsList);
        }

                        let selectedReplyFileBase64 = null;
        let selectedReplyFileName = '';

        function handleReplyFileSelect(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                selectedReplyFileName = file.name;
                const reader = new FileReader();
                reader.onload = function(e) {
                    selectedReplyFileBase64 = e.target.result;
                    const preview = document.getElementById('modal-reply-attachment-preview');
                    const nameEl = document.getElementById('modal-reply-filename');
                    if (preview && nameEl) {
                        nameEl.innerText = "📎 " + selectedReplyFileName;
                        preview.style.display = 'inline-flex';
                    }
                };
                reader.readAsDataURL(file);
            }
        }

        function clearReplyAttachment() {
            selectedReplyFileBase64 = null;
            selectedReplyFileName = '';
            const preview = document.getElementById('modal-reply-attachment-preview');
            const fileInput = document.getElementById('modal-reply-file');
            if (preview) preview.style.display = 'none';
            if (fileInput) fileInput.value = '';
        }

        function openTicketThread(ticketId) {
            const ticket = studentLoadedTicketsMap[ticketId];
            if (!ticket) return;
            currentThreadTicketId = ticketId;
            clearReplyAttachment();
            
            document.getElementById('modal-thread-title').innerText = `#TK-${ticket.id} - ${ticket.subtheme || ticket.theme || 'استفسار'}`;
            const dateStr = ticket.timestamp ? new Date(ticket.timestamp).toLocaleString('ar-MA') : '';
            document.getElementById('modal-thread-subtitle').innerText = `التاريخ: ${dateStr}`;
            
            const statusEl = document.getElementById('modal-thread-status');
            const isResolved = (ticket.status === 'resolved' || ticket.status === 'محلولة');
            const isInProgress = (ticket.status === 'in_progress' || ticket.status === 'قيد المعالجة');
            
            if (isResolved) {
                statusEl.innerText = '🟢 تم الرد (محلولة)';
                statusEl.style.background = 'rgba(46,204,113,0.15)';
                statusEl.style.color = '#2ecc71';
                statusEl.style.border = '1px solid #2ecc71';
            } else if (isInProgress) {
                statusEl.innerText = '🔵 قيد المعالجة';
                statusEl.style.background = 'rgba(52,152,219,0.15)';
                statusEl.style.color = '#3498db';
                statusEl.style.border = '1px solid #3498db';
            } else {
                statusEl.innerText = '🟠 في انتظار الرد';
                statusEl.style.background = 'rgba(243,156,18,0.15)';
                statusEl.style.color = '#f39c12';
                statusEl.style.border = '1px solid #f39c12';
            }
            
            let messages = [];
            if (ticket.conversation) {
                try {
                    messages = typeof ticket.conversation === 'string' ? JSON.parse(ticket.conversation) : ticket.conversation;
                } catch(e) { messages = []; }
            }
            
            if (!messages || messages.length === 0) {
                messages = [{ sender: 'student', name: ticket.first_name || 'أنت', text: ticket.message || '', timestamp: dateStr, file_data: ticket.file_data, file_name: ticket.file_name }];
                if (ticket.admin_reply) {
                    messages.push({ sender: 'admin', name: ticket.assigned_to || 'فريق الدعم', text: ticket.admin_reply, timestamp: '' });
                }
            }
            
            const container = document.getElementById('modal-thread-messages');
            container.innerHTML = messages.map((m, idx) => {
                const isStudent = (m.sender === 'student' || m.sender === 'user' || !m.sender || m.sender === '');
                const senderTitle = isStudent ? '👤 ' + (m.name || 'أنت') : '🛡️ المشرف (' + (m.name || 'فريق الدعم') + ')';
                const editedTag = m.edited ? '<span style="font-size:0.7rem; color:rgba(255,255,255,0.4); margin-right:4px;">(معدّل)</span>' : '';
                const editBtn = isStudent ? `<button onclick="editStudentMessage(${idx})" style="background:rgba(241,196,15,0.12); border:1px solid rgba(241,196,15,0.3); color:var(--accent); font-size:0.72rem; padding:2px 8px; border-radius:6px; cursor:pointer; font-family:'Tajawal'; display:inline-flex; align-items:center; gap:3px;" title="تعديل هذه الرسالة">✏️ تعديل</button>` : '';
                
                let attachmentHtml = '';
                if (m.file_data) {
                    if (m.file_data.startsWith('data:image') || m.file_data.includes('.jpg') || m.file_data.includes('.png') || m.file_data.includes('.jpeg')) {
                        attachmentHtml = `<img src="${m.file_data}" style="max-width:100%; max-height:180px; border-radius:8px; margin-top:8px; display:block; cursor:pointer; border:1px solid rgba(255,255,255,0.15);" onclick="window.open(this.src)" />`;
                    } else {
                        attachmentHtml = `<a href="${m.file_data}" target="_blank" style="display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.1); padding:6px 12px; border-radius:8px; color:var(--accent); font-size:0.8rem; margin-top:6px; text-decoration:none;">📄 ${m.file_name || 'تحميل المرفق'}</a>`;
                    }
                }

                return `
                <div style="display:flex; flex-direction:column; align-items:${isStudent ? 'flex-start' : 'flex-end'}; margin-bottom:12px;">
                    <div style="font-size:0.75rem; color:var(--text-2); margin-bottom:3px; padding:0 4px; display:flex; align-items:center; gap:4px;">
                        <span>${senderTitle}</span>
                        ${editBtn}
                    </div>
                    <div id="msg-bubble-${idx}" style="background:${isStudent ? '#1e3a8a' : 'rgba(255,255,255,0.08)'}; border:1px solid ${isStudent ? '#3b82f6' : 'rgba(255,255,255,0.15)'}; padding:12px 16px; border-radius:14px; max-width:85%; font-size:0.9rem; line-height:1.5; color:#fff;">
                        ${(m.text || '').replace(/\\n/g, '<br>')}
                        ${attachmentHtml}
                    </div>
                    <div style="display:flex; align-items:center; font-size:0.7rem; color:rgba(255,255,255,0.35); margin-top:3px; padding:0 4px;">
                        ${m.timestamp || ''} ${editedTag}
                    </div>
                </div>`;
            }).join('');
            
            // Handle Actions Banner vs Reply Bar
            let banner = document.getElementById('thread-resolved-banner');
            const replyBox = document.getElementById('modal-reply-bar');
            
            if (isResolved) {
                if (!banner) {
                    banner = document.createElement('div');
                    banner.id = 'thread-resolved-banner';
                    container.parentNode.insertBefore(banner, replyBox);
                }
                banner.style.display = 'block';
                banner.innerHTML = `
                    <div style="background:rgba(46,204,113,0.08); border:1px solid rgba(46,204,113,0.25); border-radius:12px; padding:14px; margin:15px; text-align:center;">
                        <div style="font-weight:bold; font-size:0.92rem; color:#2ecc71; margin-bottom:4px;">✅ تم حل هذه التذكرة وإغلاقها</div>
                        <div style="font-size:0.82rem; color:var(--text-2); margin-bottom:10px;">هل ما زلت بحاجة لمساعدة حول نفس الموضوع؟</div>
                        <div style="display:flex; gap:8px; justify-content:center; flex-wrap:wrap;">
                            <button onclick="reopenCurrentTicket()" style="background:#2ecc71; color:white; border:none; padding:8px 16px; border-radius:20px; font-weight:bold; font-size:0.82rem; cursor:pointer; font-family:'Tajawal';">
                                🔄 لا زال لدي استفسار (إعادة فتح)
                            </button>
                            <button onclick="openNewTopicFromThread()" style="background:rgba(255,255,255,0.06); color:var(--text-1); border:1px solid rgba(255,255,255,0.15); padding:8px 16px; border-radius:20px; font-size:0.82rem; cursor:pointer; font-family:'Tajawal';">
                                ➕ موضوع جديد منفصل
                            </button>
                        </div>
                    </div>
                `;
                if (replyBox) replyBox.style.display = 'none';
            } else {
                if (banner) banner.style.display = 'none';
                if (replyBox) replyBox.style.display = 'flex';
            }
            
            document.getElementById('ticket-thread-modal').style.display = 'flex';
            
            // Drag and drop support on thread container
            container.ondragover = (e) => { e.preventDefault(); container.style.border = '2px dashed var(--accent)'; };
            container.ondragleave = (e) => { e.preventDefault(); container.style.border = 'none'; };
            container.ondrop = (e) => {
                e.preventDefault();
                container.style.border = 'none';
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    handleReplyFileSelect({ files: e.dataTransfer.files });
                }
            };
            
            setTimeout(() => { container.scrollTop = container.scrollHeight; }, 100);
        }

        async function editStudentMessage(msgIdx) {
            if (!currentThreadTicketId) return;
            const bubble = document.getElementById(`msg-bubble-${msgIdx}`);
            if (!bubble) return;
            const oldText = bubble.innerText.trim();
            const newText = prompt("تعديل رسالتك:", oldText);
            if (!newText || newText.trim() === oldText) return;
            
            bubble.innerHTML = newText.trim().replace(/\\n/g, '<br>') + ' <span style="font-size:0.7rem; color:rgba(255,255,255,0.4);">(معدّل)</span>';
            
            try {
                await fetch(`${BOT_BASE}/api/tickets/${currentThreadTicketId}/messages/edit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message_index: msgIdx, text: newText.trim(), role: 'student' })
                });
            } catch(e) { console.error('Edit message error:', e); }
        }

        async function reopenCurrentTicket() {
            if (!currentThreadTicketId) return;
            const statusEl = document.getElementById('modal-thread-status');
            if (statusEl) {
                statusEl.innerText = '🟠 في انتظار الرد';
                statusEl.style.background = 'rgba(243,156,18,0.15)';
                statusEl.style.color = '#f39c12';
                statusEl.style.border = '1px solid #f39c12';
            }
            const banner = document.getElementById('thread-resolved-banner');
            if (banner) banner.style.display = 'none';
            const replyBox = document.getElementById('modal-reply-bar');
            if (replyBox) replyBox.style.display = 'flex';
            
            try {
                await fetch(`${BOT_BASE}/api/tickets/${currentThreadTicketId}/reopen`, { method: 'POST' });
                if (studentLoadedTicketsMap[currentThreadTicketId]) {
                    studentLoadedTicketsMap[currentThreadTicketId].status = 'pending';
                }
            } catch(e) { console.error('Reopen error:', e); }
        }

        function openNewTopicFromThread() {
            closeTicketThread();
            switchTab('new');
        }

        function closeTicketThread() {
            document.getElementById('ticket-thread-modal').style.display = 'none';
            currentThreadTicketId = null;
            clearReplyAttachment();
        }

        async function sendStudentFollowupReply() {
            const input = document.getElementById('modal-reply-input');
            const msg = (input ? input.value : '').trim();
            if ((!msg && !selectedReplyFileBase64) || !currentThreadTicketId) return;
            
            const fileDataToSend = selectedReplyFileBase64;
            const fileNameToSend = selectedReplyFileName;
            
            input.value = '';
            clearReplyAttachment();
            
            const container = document.getElementById('modal-thread-messages');
            let attachmentHtml = '';
            if (fileDataToSend) {
                if (fileDataToSend.startsWith('data:image')) {
                    attachmentHtml = `<img src="${fileDataToSend}" style="max-width:100%; max-height:180px; border-radius:8px; margin-top:8px; display:block;" />`;
                } else {
                    attachmentHtml = `<div style="background:rgba(255,255,255,0.1); padding:6px 12px; border-radius:8px; color:var(--accent); font-size:0.8rem; margin-top:6px;">📄 ${fileNameToSend}</div>`;
                }
            }

            container.innerHTML += `
                <div style="display:flex; flex-direction:column; align-items:flex-start; margin-bottom:12px;">
                    <div style="font-size:0.75rem; color:var(--text-2); margin-bottom:3px; padding:0 4px;">👤 أنت</div>
                    <div style="background:#1e3a8a; border:1px solid #3b82f6; padding:12px 16px; border-radius:14px; max-width:85%; font-size:0.9rem; color:#fff;">
                        ${msg ? msg.replace(/\\n/g, '<br>') : ''}
                        ${attachmentHtml}
                    </div>
                </div>
            `;
            container.scrollTop = container.scrollHeight;
            
            const tid = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.id : null) || null;
            const fname = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.first_name : "") || "الطالب";
            const uname = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user ? window.Telegram.WebApp.initDataUnsafe.user.username : "") || "";
            
            try {
                await fetch(`${BOT_BASE}/api/tickets/${currentThreadTicketId}/reply`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: msg, 
                        telegram_id: tid, 
                        first_name: fname, 
                        username: uname,
                        file_data: fileDataToSend,
                        file_name: fileNameToSend
                    })
                });
            } catch(e) { console.error('Reply error:', e); }
        }

        // --- LIVE RADAR PING ---
        function initLiveRadarPing() {
            const sendPing = () => {
                try {
                    const user = (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe ? window.Telegram.WebApp.initDataUnsafe.user : null);
                    if (!user) return;
                    let activeTab = 'Inconnu';
                    if ((document.getElementById('tabnew-btn') && document.getElementById('tabnew-btn').classList.contains('active'))) activeTab = 'Nouveau Ticket';
                    if ((document.getElementById('tabfaq-btn') && document.getElementById('tabfaq-btn').classList.contains('active'))) activeTab = 'FAQ';
                    if ((document.getElementById('tabinbox-btn') && document.getElementById('tabinbox-btn').classList.contains('active'))) activeTab = 'Boîte de réception';
                    
                    fetch('/api/presence/ping', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            user_id: user.id,
                            name: user.first_name + (user.last_name ? ' ' + user.last_name : ''),
                            page: 'Support / ' + activeTab
                        })
                    }).catch(e => {});
                } catch(e) {}
            };
            sendPing();
            setInterval(sendPing, 15000);
        }
        setTimeout(initLiveRadarPing, 1000);
    
        function openStudentSuggestModal() {
            const m = document.getElementById('student-suggest-modal');
            if (m) {
                document.getElementById('suggest-form-body').style.display = 'block';
                document.getElementById('suggest-success-body').style.display = 'none';
                document.getElementById('suggest-question-input').value = '';
                document.getElementById('suggest-desc-input').value = '';
                m.style.display = 'flex';
            }
        }

        function closeStudentSuggestModal() {
            const m = document.getElementById('student-suggest-modal');
            if (m) m.style.display = 'none';
        }

        async function submitStudentFaqSuggestion() {
            const q = document.getElementById('suggest-question-input').value.trim();
            const desc = document.getElementById('suggest-desc-input').value.trim();
            const cat = document.getElementById('suggest-cat-input').value;
            const btn = document.getElementById('btn-submit-suggest');
            
            if (!q) {
                alert("يرجى كتابة صيغة السؤال المقترح.");
                return;
            }
            
            btn.disabled = true;
            btn.innerHTML = "جاري الإرسال...";
            
            const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user;
            const tid = tgUser?.id || '';
            const name = tgUser?.first_name || 'طالب';
            
            try {
                const res = await fetch(`${BOT_BASE}/api/faq/suggest`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: q,
                        description: desc,
                        category: cat,
                        telegram_id: tid,
                        student_name: name
                    })
                });
                
                const data = await res.json();
                if (data.success) {
                    document.getElementById('suggest-form-body').style.display = 'none';
                    document.getElementById('suggest-success-body').style.display = 'block';
                } else {
                    alert("حدث خطأ: " + (data.error || "تعذر إرسال الاقتراح"));
                }
            } catch(e) {
                alert("خطأ في الاتصال بالخادم.");
            } finally {
                btn.disabled = false;
                btn.innerHTML = "🚀 إرسال الاقتراح";
            }
        }

</script>

    
    <!-- TICKET THREAD MODAL -->
    <div class="modal-overlay" id="ticket-thread-modal" style="display:none; z-index:3000;">
        <div class="modal-content" style="max-height:90vh; display:flex; flex-direction:column; padding:0; overflow:hidden;">
            <!-- Modal Header -->
            <div style="padding:15px 20px; border-bottom:1px solid rgba(255,255,255,0.1); display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03);">
                <div>
                    <div style="font-weight:bold; font-size:1rem; color:var(--text-1);" id="modal-thread-title">تفاصيل التذكرة</div>
                    <div style="font-size:0.75rem; color:var(--text-2);" id="modal-thread-subtitle">تاريخ الإنشاء: --</div>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span id="modal-thread-status" style="font-size:0.75rem; padding:3px 10px; border-radius:12px;">قيد الانتظار</span>
                    <button class="modal-close" style="position:static;" onclick="closeTicketThread()">✕</button>
                </div>
            </div>

            <!-- Messages Thread Area -->
            <div id="modal-thread-messages" style="flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:15px; background:rgba(0,0,0,0.2);">
                <!-- Dynamically populated -->
            </div>

            <!-- CSAT Rating Widget (Shown if ticket is resolved) -->
            <div id="modal-csat-box" style="display:none; padding:15px; background:rgba(241,196,15,0.08); border-top:1px solid rgba(241,196,15,0.2); text-align:center;">
                <div style="font-size:0.9rem; font-weight:bold; color:var(--accent); margin-bottom:8px;">⭐️ ما هو تقييمك لخدمة الدعم؟</div>
                <div style="font-size:1.8rem; display:flex; justify-content:center; gap:8px; cursor:pointer; margin-bottom:8px;" id="csat-stars">
                    <span onclick="selectCsatStar(1)">⭐</span>
                    <span onclick="selectCsatStar(2)">⭐</span>
                    <span onclick="selectCsatStar(3)">⭐</span>
                    <span onclick="selectCsatStar(4)">⭐</span>
                    <span onclick="selectCsatStar(5)">⭐</span>
                </div>
                <div id="csat-status-msg" style="font-size:0.8rem; color:#2ecc71; font-weight:bold; display:none;">تم حفظ تقييمك بنجاح، شكراً لك! 🙏</div>
            </div>

            <!-- Reply Input Bar -->
            <div id="modal-reply-bar" style="padding:15px; border-top:1px solid rgba(255,255,255,0.1); background:rgba(255,255,255,0.02); display:flex; gap:10px;">
                <input type="text" id="modal-reply-input" placeholder="اكتب رداً إضافياً للإدارة..." style="flex:1; background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.15); color:#fff; padding:12px; border-radius:10px; font-family:'Tajawal'; font-size:0.9rem; outline:none;" onkeypress="if(event.key === 'Enter') sendStudentFollowupReply()" />
                <button onclick="sendStudentFollowupReply()" style="background:var(--accent); color:#1e3a8a; border:none; padding:0 18px; border-radius:10px; font-weight:bold; font-family:'Tajawal'; cursor:pointer;">
                    إرسال
                </button>
            </div>
        </div>
    </div>


    <!-- STUDENT FAQ SUGGESTION MODAL -->
    <div id="student-suggest-modal" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.8); z-index:9999; align-items:center; justify-content:center; padding:20px; backdrop-filter:blur(5px);">
        <div style="background:#16162a; border:1px solid rgba(255,255,255,0.15); border-radius:16px; max-width:420px; width:100%; padding:20px; box-shadow:0 10px 30px rgba(0,0,0,0.5); font-family:'Tajawal', sans-serif;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:10px;">
                <div style="font-weight:bold; font-size:1.1rem; color:var(--text-1); display:flex; align-items:center; gap:8px;">
                    <span>💡</span> اقترح سؤالاً للـ FAQ
                </div>
                <button onclick="closeStudentSuggestModal()" style="background:none; border:none; color:var(--text-2); font-size:1.4rem; cursor:pointer;">&times;</button>
            </div>
            
            <div id="suggest-form-body">
                <div style="margin-bottom:12px;">
                    <label style="font-size:0.8rem; color:var(--text-2); display:block; margin-bottom:5px;">📌 القسم / التصنيف</label>
                    <select id="suggest-cat-input" style="width:100%; padding:10px; border-radius:8px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:var(--text-1); font-family:'Tajawal';">
                        <option value="الدخول">🔐 تسجيل الدخول والحساب</option>
                        <option value="الدفع">💳 الدفع والاشتراكات</option>
                        <option value="الدروس">📚 الدروس والمرفقات</option>
                        <option value="الشهادات">🎓 الشهادات والاختبارات</option>
                        <option value="عام" selected>💬 عام</option>
                    </select>
                </div>
                
                <div style="margin-bottom:12px;">
                    <label style="font-size:0.8rem; color:var(--text-2); display:block; margin-bottom:5px;">❓ صيغة السؤال المقترح</label>
                    <input type="text" id="suggest-question-input" placeholder="مثال: كيف يمكنني تحميل فيديوهات الدورة؟" style="width:100%; padding:10px; border-radius:8px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:var(--text-1); font-family:'Tajawal'; font-size:0.88rem; box-sizing:border-box;">
                </div>
                
                <div style="margin-bottom:15px;">
                    <label style="font-size:0.8rem; color:var(--text-2); display:block; margin-bottom:5px;">📝 تفاصيل إضافية أو الإجابة المتوقعة (اختياري)</label>
                    <textarea id="suggest-desc-input" rows="3" placeholder="اكتب هنا أي توضيح أو سياق إضافي..." style="width:100%; padding:10px; border-radius:8px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:var(--text-1); font-family:'Tajawal'; font-size:0.85rem; box-sizing:border-box; resize:none;"></textarea>
                </div>
                
                <div style="display:flex; gap:10px;">
                    <button onclick="closeStudentSuggestModal()" style="flex:1; padding:10px; border-radius:8px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:var(--text-1); cursor:pointer; font-family:'Tajawal';">إلغاء</button>
                    <button onclick="submitStudentFaqSuggestion()" id="btn-submit-suggest" style="flex:2; padding:10px; border-radius:8px; background:linear-gradient(135deg, #8E2DE2, #4A00E0); border:none; color:white; font-weight:bold; cursor:pointer; font-family:'Tajawal';">🚀 إرسال الاقتراح</button>
                </div>
            </div>
            
            <div id="suggest-success-body" style="display:none; text-align:center; padding:20px 10px;">
                <div style="font-size:3rem; margin-bottom:10px;">🎉</div>
                <div style="font-weight:bold; font-size:1.1rem; color:#2ecc71; margin-bottom:8px;">شكراً لمساهمتك!</div>
                <div style="font-size:0.85rem; color:var(--text-2); line-height:1.5; margin-bottom:15px;">تم إرسال اقتراحك لفريق الإدارة. بعد مراجعته واعتماده سيظهر مباشرة في الأسئلة الشائعة لجميع الطلاب.</div>
                <button onclick="closeStudentSuggestModal()" style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2); color:white; padding:8px 20px; border-radius:20px; cursor:pointer; font-family:'Tajawal';">إغلاق</button>
            </div>
        </div>
    </div>


    <!-- STORIES VIEWER MODAL -->
    <div id="story-viewer-modal">
        <div class="story-progress-bar-wrap" id="story-progress-container"></div>
        <div class="story-top-author">
            <div class="story-author-info">
                <div class="story-author-avatar" id="story-author-icon">🏛️</div>
                <div class="story-author-name" id="story-author-title">أكاديمية أُسوة</div>
            </div>
            <button class="story-close-btn" onclick="closeStoryViewer()">✕</button>
        </div>
        <div class="story-body">
            <div class="story-nav-zones">
                <div class="story-nav-left" onclick="prevStorySlide()"></div>
                <div class="story-nav-right" onclick="nextStorySlide()"></div>
            </div>
            <div class="story-card-slide">
                <div class="story-slide-icon" id="story-slide-icon">🏛️</div>
                <div class="story-slide-title" id="story-slide-title">العنوان</div>
                <div class="story-slide-text" id="story-slide-text">النص التوضيحي</div>
                <button class="story-slide-btn" id="story-slide-btn" onclick="handleStoryAction()">التالي ➔</button>
            </div>
        </div>
    </div>

</body>
</html>