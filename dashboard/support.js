// Global State
let allTickets = [];
let filteredTickets = [];
let currentStatus = 'Nouveau'; 
let currentCategory = 'all'; // all, urgent, tech, finance, course, exam
let adminId = null;
let activeTicketId = null;

// Fake Data for demonstration
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

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
        adminId = window.Telegram.WebApp.initDataUnsafe.user.id;
        window.Telegram.WebApp.expand();
        loadTickets();
    } else {
        document.getElementById('config-overlay').style.display = 'flex';
    }
});

function submitManualUserId() {
    adminId = document.getElementById('manual-user-id').value;
    if (!adminId) return;
    document.getElementById('config-overlay').style.display = 'none';
    loadTickets();
}

async function loadTickets() {
    const feed = document.getElementById('tickets-feed');
    feed.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>جاري تحميل التذاكر...</p></div>';
    
    try {
        const res = await fetch('/api/admin/tickets');
        const data = await res.json();
        let apiTickets = data.tickets || [];
        
        // MIX REAL TICKETS WITH MOCK TICKETS FOR DEMO
        if (apiTickets.length === 0) {
            allTickets = mockTickets;
        } else {
            allTickets = [...apiTickets, ...mockTickets];
        }
        
        // Sort newest first
        allTickets = allTickets.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        applyFilters();
    } catch (e) {
        // Fallback to mock data if API fails
        console.warn("API Error, loading mock data");
        allTickets = mockTickets.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        applyFilters();
    }
}

function filterByStatus(status, element) {
    currentStatus = status;
    document.querySelectorAll('.bottom-nav .nav-item').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    applyFilters();
}

function filterByCategory(category, element) {
    currentCategory = category;
    document.querySelectorAll('.filter-chips-container .filter-chip').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    applyFilters();
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
    // Hash name to a number 1-4 for background color
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
    
    if (filteredTickets.length === 0) {
        feed.innerHTML = '<div style="text-align:center; padding:50px; color:var(--text-muted);">لا توجد تذاكر مطابقة للفلاتر الحالية</div>';
        return;
    }
    
    feed.innerHTML = filteredTickets.map(t => {
        const name = t.first_name || 'طالب';
        const initial = name.charAt(0);
        const avatarClass = getAvatarBg(name);
        
        // Generate a display ID (pad short IDs)
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
    
    // Set Context Bar
    const contextHtml = [];
    if (ticket.theme) contextHtml.push(`📁 ${ticket.theme}`);
    if (ticket.is_urgent) contextHtml.push(`🚨 عاجل`);
    document.getElementById('chat-context').innerHTML = `
        <span class="context-badge">${contextHtml.join(' • ') || 'عام'}</span>
        <span class="context-date">${formatTime(ticket.timestamp)}</span>
    `;
    
    const chatFeed = document.getElementById('chat-feed');
    let chatHtml = '';
    
    // If there is RAG history, show it!
    if (ticket.rag_history) {
        chatHtml += `
            <div class="bubble bot-rag">
                🤖 <b>تدخل البوت المسبق (FAQ):</b><br>
                ${ticket.rag_history}
            </div>
        `;
    }
    
    // Student message
    chatHtml += `
        <div class="bubble student">
            ${ticket.text || ticket.subtheme || 'لا يوجد نص'}
            <span class="time">${formatTime(ticket.timestamp)}</span>
        </div>
    `;
    
    chatFeed.innerHTML = chatHtml;
    
    // View transitions
    document.getElementById('view-inbox').classList.remove('active');
    document.getElementById('view-chat').classList.add('active');
}

function goBack() {
    activeTicketId = null;
    document.getElementById('view-chat').classList.remove('active');
    document.getElementById('view-inbox').classList.add('active');
    applyFilters();
}

async function resolveCurrentTicket() {
    if (!activeTicketId) return;
    try {
        // If it's a mock ticket, just resolve locally
        if (activeTicketId.startsWith('mock_')) {
             const idx = allTickets.findIndex(t => t.id === activeTicketId);
             if (idx > -1) allTickets[idx].status = 'Résolu';
             goBack();
             return;
        }
        
        const formData = new FormData();
        formData.append('ticket_id', activeTicketId);
        formData.append('admin_id', adminId);
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
    
    // Actually sending to server will go here
}

function generateAIResponse() {
    const input = document.getElementById('chat-reply-input');
    input.value = "جاري توليد الرد من قاعدة المعرفة (FAQ)... ✨";
    
    setTimeout(() => {
        input.value = "وعليكم السلام ورحمة الله وبركاته، بخصوص سؤالك عن المسألة، الجواب هو أنه يجوز ذلك بناءً على ما ورد في التفريغ. هل هناك استفسار آخر؟";
    }, 1500);
}
