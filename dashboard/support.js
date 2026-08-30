// Global State
let allTickets = [];
let filteredTickets = [];
let currentStatus = 'Nouveau'; 
let currentCategory = 'all'; // all, urgent, tech, aqida, fiqh, sira
let adminId = null;
let activeTicketId = null;

// Fake Data for demonstration
const mockTickets = [
    {
        id: 'mock_1',
        first_name: 'أحمد',
        theme: 'تقني',
        subtheme: 'مشكلة في الدخول',
        text: 'السلام عليكم، لم أستطع الدخول إلى حسابي منذ الأمس، تظهر لي رسالة خطأ، الرجاء المساعدة بسرعة!',
        status: 'Nouveau',
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 mins ago
        is_urgent: true,
        rag_history: 'حاولت مساعدة الطالب بإرسال رابط استعادة كلمة المرور لكنه أصر على التحدث مع مشرف.'
    },
    {
        id: 'mock_2',
        first_name: 'سارة',
        theme: 'الفقه',
        subtheme: 'سؤال في باب الطهارة',
        text: 'هل يجوز المسح على الجوارب الرقيقة؟ وجدت اختلافاً في التفريغ ولم أفهم جيداً.',
        status: 'Nouveau',
        timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 mins ago
        is_urgent: false,
        rag_history: 'تم تقديم إجابة من ملخص الطهارة: يجوز المسح بشروط (مذكورة في التفريغ ص14).'
    },
    {
        id: 'mock_3',
        first_name: 'محمد',
        theme: 'العقيدة',
        subtheme: 'الأسماء والصفات',
        text: 'الشيخ ذكر مسألة في الدرس الثاني حول توحيد الأسماء والصفات، هل ممكن توضيح إضافي؟',
        status: 'En cours',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
        is_urgent: false,
        rag_history: null
    },
    {
        id: 'mock_4',
        first_name: 'فاطمة',
        theme: 'السيرة',
        subtheme: 'غزوة بدر',
        text: 'شكراً لكم، تم حل المشكلة وفهمت الدرس جيداً بفضل الله ثم بفضلكم.',
        status: 'Résolu',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
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
            if (currentCategory === 'aqida' && !theme.includes('عقيد')) return false;
            if (currentCategory === 'fiqh' && !theme.includes('فقه')) return false;
            if (currentCategory === 'sira' && !theme.includes('سير')) return false;
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
        
        const urgentTag = t.is_urgent ? '<span class="tag tag-urgent">🚨 عاجل</span>' : '';
        const themeTag = t.theme ? `<span class="tag tag-subject">${t.theme}</span>` : '';
        
        return `
            <div class="ticket-card" onclick="openTicket('${t.id}')">
                <div class="ticket-avatar ${avatarClass}">${initial}</div>
                <div class="ticket-content">
                    <div class="ticket-header">
                        <span class="ticket-author">${name}</span>
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
    
    const name = ticket.first_name || 'طالب';
    document.getElementById('chat-title').innerText = name;
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
