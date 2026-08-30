// inbox.js - Inbox View Module

// Global State (Scoped to this module)
let allTickets = [];
let filteredTickets = [];
let currentStatus = 'Nouveau'; 
let currentCategory = 'all';
let activeTicketId = null;

const mockTickets = [
    {
        id: '1051',
        first_name: 'أحمد',
        theme: 'تقني',
        subtheme: 'مشكلة في الدخول',
        text: 'السلام عليكم، لم أستطع الدخول إلى حسابي منذ الأمس، تظهر لي رسالة خطأ.',
        status: 'Nouveau',
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        is_urgent: true,
        rag_history: 'حاولت مساعدة الطالب بإرسال رابط استعادة كلمة المرور لكنه أصر على التحدث مع مشرف.'
    },
    {
        id: '1052',
        first_name: 'ياسر',
        theme: 'مالي',
        subtheme: 'تأكيد الدفع',
        text: 'لقد قمت بتحويل الرسوم عبر البنك، أين أرسل الإيصال؟',
        status: 'Nouveau',
        timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
        is_urgent: false,
        rag_history: null
    },
    {
        id: '1053',
        first_name: 'محمد',
        theme: 'دعم الدروس',
        subtheme: 'نقص في ملف PDF',
        text: 'ملف التفريغ للدرس الثالث لا يفتح معي، هل يمكنكم إعادة رفعه؟',
        status: 'En cours',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
        is_urgent: false,
        rag_history: null
    },
    {
        id: '1054',
        first_name: 'فاطمة',
        theme: 'امتحان',
        subtheme: 'موعد الاختبار النهائي',
        text: 'شكراً لكم، تم حل المشكلة وفهمت المطلوب.',
        status: 'Résolu',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
        is_urgent: false,
        rag_history: null
    }
];

export function initInboxView(container) {
    container.innerHTML = `
        <section id="view-inbox" class="view active module-view" style="position:relative;">
            <header class="app-header">
                <div class="header-titles">
                    <h1>💬 الدعم الفني</h1>
                    <span class="header-subtitle">لوحة التحكم</span>
                </div>
                <button class="btn-icon" id="btn-refresh-inbox" aria-label="تحديث">🔄</button>
            </header>
            
            <!-- Category / Funnel Chips -->
            <div class="filter-chips-container" id="inbox-chips">
                <div class="filter-chip active" data-cat="all">الكل</div>
                <div class="filter-chip urgent-chip" data-cat="urgent">🚨 عاجل</div>
                <div class="filter-chip" data-cat="tech">⚙️ تقني</div>
                <div class="filter-chip" data-cat="finance">💳 مالي</div>
                <div class="filter-chip" data-cat="course">📚 دعم الدروس</div>
                <div class="filter-chip" data-cat="exam">📝 امتحان</div>
            </div>
            
            <div id="tickets-feed" class="feed-container">
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>جاري تحميل التذاكر...</p>
                </div>
            </div>

            <!-- Sticky Bottom Navigation (Status) -->
            <nav class="bottom-nav" id="inbox-bottom-nav">
                <div class="nav-item active" data-status="Nouveau">
                    <div class="nav-icon-wrap"><span class="nav-icon">📩</span></div>
                    <span class="nav-label">جديد</span>
                </div>
                <div class="nav-item" data-status="En cours">
                    <div class="nav-icon-wrap"><span class="nav-icon">⏳</span></div>
                    <span class="nav-label">قيد المعالجة</span>
                </div>
                <div class="nav-item" data-status="Résolu">
                    <div class="nav-icon-wrap"><span class="nav-icon">✅</span></div>
                    <span class="nav-label">مكتمل</span>
                </div>
            </nav>
        </section>
    `;

    // Bind events
    document.getElementById('btn-refresh-inbox').addEventListener('click', loadTickets);
    
    document.querySelectorAll('#inbox-chips .filter-chip').forEach(chip => {
        chip.addEventListener('click', (e) => {
            currentCategory = e.currentTarget.getAttribute('data-cat');
            document.querySelectorAll('#inbox-chips .filter-chip').forEach(el => el.classList.remove('active'));
            e.currentTarget.classList.add('active');
            applyFilters();
        });
    });

    document.querySelectorAll('#inbox-bottom-nav .nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            currentStatus = e.currentTarget.getAttribute('data-status');
            document.querySelectorAll('#inbox-bottom-nav .nav-item').forEach(el => el.classList.remove('active'));
            e.currentTarget.classList.add('active');
            applyFilters();
        });
    });

    // Expose global methods for the chat overlay (temporary fix until we componentize the chat)
    window.openTicket = openTicket;
    window.goBack = goBack;
    window.resolveCurrentTicket = resolveCurrentTicket;
    window.sendReply = sendReply;
    window.generateAIResponse = generateAIResponse;
    window.reassignTicket = reassignTicket;
    window.triggerAttach = triggerAttach;

    loadTickets();
}

async function loadTickets() {
    const feed = document.getElementById('tickets-feed');
    if(feed) feed.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>جاري تحميل التذاكر...</p></div>';
    
    try {
        const res = await fetch('/api/admin/tickets');
        const data = await res.json();
        let apiTickets = data.tickets || [];
        
        if (apiTickets.length === 0) {
            allTickets = mockTickets;
        } else {
            allTickets = [...apiTickets, ...mockTickets];
        }
        
        allTickets = allTickets.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        applyFilters();
    } catch (e) {
        console.warn("API Error, loading mock data");
        allTickets = mockTickets.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        applyFilters();
    }
}

function applyFilters() {
    filteredTickets = allTickets.filter(t => {
        // Status Check
        let s = t.status || 'Nouveau';
        if (s === 'pending') s = 'Nouveau';
        if (s === 'En cours de traitement' || s === 'En cours') s = 'En cours';
        if (s === 'Déjà traité' || s === 'resolved' || s === 'Résolu') s = 'Résolu';
        if (s !== currentStatus) return false;
        
        // Category Check
        if (currentCategory !== 'all') {
            const theme = t.theme ? t.theme.toLowerCase() : '';
            if (currentCategory === 'urgent' && !t.is_urgent) return false;
            if (currentCategory === 'tech' && !theme.includes('تقني')) return false;
            if (currentCategory === 'finance' && !theme.includes('مالي')) return false;
            if (currentCategory === 'course' && !theme.includes('دعم')) return false;
            if (currentCategory === 'exam' && !theme.includes('امتحان')) return false;
        }
        
        return true;
    });
    
    renderFeed();
}

function getAvatarBg(name) {
    let sum = 0;
    for(let i=0; i<name.length; i++) sum += name.charCodeAt(i);
    return `avatar-bg-${(sum % 4) + 1}`;
}

function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
}

function renderFeed() {
    const feed = document.getElementById('tickets-feed');
    if (!feed) return;
    
    if (filteredTickets.length === 0) {
        feed.innerHTML = '<div style="text-align:center; padding:50px; color:var(--text-muted);">لا توجد تذاكر مطابقة للفلاتر الحالية</div>';
        return;
    }
    
    feed.innerHTML = filteredTickets.map(t => {
        const name = t.first_name || 'طالب';
        const initial = name.charAt(0);
        const avatarClass = getAvatarBg(name);
        
        let displayId = t.id ? t.id.toString() : Math.floor(Math.random() * 1000).toString();
        if (displayId.length < 4 && !displayId.startsWith('mock_')) displayId = displayId.padStart(4, '0');
        displayId = displayId.replace('mock_', '');
        
        const urgentTag = t.is_urgent ? '<span class="tag tag-urgent">🚨 عاجل</span>' : '';
        const themeTag = t.theme ? `<span class="tag tag-subject">${t.theme}</span>` : '';
        
        return `
            <div class="ticket-card" onclick="openTicket('${t.id}')">
                <div class="ticket-avatar ${avatarClass}">${initial}</div>
                <div class="ticket-content">
                    <div class="ticket-header">
                        <span class="ticket-author">${name} <span style="font-size:0.75rem; color:var(--gold); font-weight:normal;">#${displayId}</span></span>
                        <span class="ticket-time">${formatTime(t.timestamp)}</span>
                    </div>
                    <div class="ticket-tags">
                        ${urgentTag}
                        ${themeTag}
                    </div>
                    <div class="ticket-preview">${t.subtheme || t.text || '...'}</div>
                </div>
            </div>
        `;
    }).join('');
}

// --- CHAT OVERLAY LOGIC ---

function openTicket(id) {
    const ticket = allTickets.find(t => t.id === id);
    if (!ticket) return;
    activeTicketId = id;
    
    let displayId = id.toString().replace('mock_', '');
    if (displayId.length < 4) displayId = displayId.padStart(4, '0');
    
    const name = ticket.first_name || 'طالب';
    document.getElementById('chat-title').innerHTML = `${name} <span style="color:var(--gold); font-size:0.8rem;">#${displayId}</span>`;
    document.getElementById('chat-header-avatar').innerText = name.charAt(0);
    document.getElementById('chat-header-avatar').className = `chat-avatar ${getAvatarBg(name)}`;
    
    const contextHtml = [];
    if (ticket.theme) contextHtml.push(`📁 ${ticket.theme}`);
    if (ticket.is_urgent) contextHtml.push(`🚨 عاجل`);
    document.getElementById('chat-context').innerHTML = `
        <span class="context-badge">${contextHtml.join(' • ') || 'عام'}</span>
        <span class="context-date">${formatTime(ticket.timestamp)}</span>
    `;
    
    const chatFeed = document.getElementById('chat-feed');
    let chatHtml = '';
    
    if (ticket.rag_history) {
        chatHtml += `
            <div class="bubble bot-rag">
                🤖 <b>تدخل البوت المسبق (FAQ):</b><br>
                ${ticket.rag_history}
            </div>
        `;
    }
    
    chatHtml += `
        <div class="bubble student">
            ${ticket.text || ticket.subtheme || 'لا يوجد نص'}
            <span class="time">${formatTime(ticket.timestamp)}</span>
        </div>
    `;
    
    chatFeed.innerHTML = chatHtml;
    
    // View transitions
    document.getElementById('view-chat').classList.add('active');
}

function goBack() {
    activeTicketId = null;
    document.getElementById('view-chat').classList.remove('active');
    applyFilters();
}

async function resolveCurrentTicket() {
    if (!activeTicketId) return;
    try {
        if (activeTicketId.toString().startsWith('105')) {
             const idx = allTickets.findIndex(t => t.id === activeTicketId);
             if (idx > -1) allTickets[idx].status = 'Résolu';
             goBack();
             return;
        }
        
        const formData = new FormData();
        formData.append('ticket_id', activeTicketId);
        formData.append('admin_id', window.adminId);
        formData.append('status', 'resolved');
        
        await fetch('/admin/resolve-ticket', { method: 'POST', body: formData });
        
        const idx = allTickets.findIndex(t => t.id === activeTicketId);
        if (idx > -1) allTickets[idx].status = 'resolved'; 
        
        goBack();
    } catch (e) {
        alert('حدث خطأ');
    }
}

function sendReply() {
    const input = document.getElementById('chat-reply-input');
    const msg = input.value.trim();
    if (!msg) return;
    
    const chatFeed = document.getElementById('chat-feed');
    chatFeed.innerHTML += `
        <div class="bubble admin">
            ${msg}
            <span class="time">الآن</span>
        </div>
    `;
    
    input.value = '';
    chatFeed.scrollTop = chatFeed.scrollHeight;
}

function generateAIResponse() {
    const input = document.getElementById('chat-reply-input');
    input.value = "جاري توليد الرد من قاعدة المعرفة (FAQ)... ✨";
    
    setTimeout(() => {
        input.value = "وعليكم السلام ورحمة الله وبركاته، بخصوص سؤالك، يمكننا حله باتباع الخطوات التالية...";
    }, 1500);
}

function reassignTicket() {
    alert("سيتم إضافة ميزة تحويل التذكرة لمشرف آخر قريباً.");
}

function triggerAttach() {
    alert("سيتم إضافة ميزة إرفاق صورة قريباً.");
}
