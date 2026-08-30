// Global State
let allTickets = [];
let currentFilter = 'Nouveau'; // Or 'En cours', 'Résolu' depending on how tickets are categorized in the db
let adminId = null;
let activeTicketId = null;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    // 1. Handle Auth (from TG WebApp or Manual)
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
    document.getElementById('tickets-feed').innerHTML = '<div style="text-align:center; padding:50px; color:#666;">جاري التحميل...</div>';
    try {
        const res = await fetch('/api/admin/tickets');
        const data = await res.json();
        // Sort newest first
        allTickets = (data.tickets || []).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        renderFeed();
    } catch (e) {
        document.getElementById('tickets-feed').innerHTML = '<div style="text-align:center; padding:50px; color:var(--danger);">خطأ في التحميل</div>';
    }
}

function filterTickets(status, element) {
    currentFilter = status;
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    if (element) {
        element.classList.add('active');
    }
    renderFeed();
}

function renderFeed() {
    const feed = document.getElementById('tickets-feed');
    const filtered = allTickets.filter(t => {
        // Simple mapping based on your existing DB status or defaults
        let s = t.status || 'Nouveau';
        if (s === 'pending') s = 'Nouveau';
        if (s === 'En cours de traitement' || s === 'En cours') s = 'En cours';
        if (s === 'Déjà traité' || s === 'resolved' || s === 'Résolu') s = 'Résolu';
        return s === currentFilter;
    });
    
    if (filtered.length === 0) {
        feed.innerHTML = '<div style="text-align:center; padding:50px; color:var(--text-muted);">لا توجد تذاكر في هذا القسم</div>';
        return;
    }
    
    feed.innerHTML = filtered.map(t => {
        return `
            <div class="ticket-card" onclick="openTicket('${t.id}')">
                <div class="ticket-header">
                    <span class="ticket-author">${t.first_name || 'طالب'}</span>
                    <span class="ticket-theme">${t.theme || 'عام'}</span>
                </div>
                <div class="ticket-preview">${t.subtheme || t.text || '...'}</div>
            </div>
        `;
    }).join('');
}

function openTicket(id) {
    const ticket = allTickets.find(t => t.id === id);
    if (!ticket) return;
    activeTicketId = id;
    
    document.getElementById('chat-title').innerText = ticket.first_name || 'طالب';
    
    const chatFeed = document.getElementById('chat-feed');
    chatFeed.innerHTML = `
        <div class="bubble student">
            <strong>المادة:</strong> ${ticket.theme || 'غير محدد'}<br>
            <strong>السؤال:</strong><br>${ticket.subtheme || ticket.text || 'لا يوجد نص'}
        </div>
    `;
    
    // View transitions
    document.getElementById('view-inbox').classList.remove('active');
    document.getElementById('view-chat').classList.add('active');
}

function goBack() {
    activeTicketId = null;
    document.getElementById('view-chat').classList.remove('active');
    document.getElementById('view-inbox').classList.add('active');
    // Refresh feed to show any status changes if modified
    renderFeed();
}

async function resolveCurrentTicket() {
    if (!activeTicketId) return;
    try {
        const formData = new FormData();
        formData.append('ticket_id', activeTicketId);
        formData.append('admin_id', adminId);
        // Map to what your backend expects, e.g. 'resolved' or 'Déjà traité'
        formData.append('status', 'resolved');
        
        await fetch('/admin/resolve-ticket', { method: 'POST', body: formData });
        
        // Update local state
        const idx = allTickets.findIndex(t => t.id === activeTicketId);
        if (idx > -1) allTickets[idx].status = 'resolved'; // which will map to Résolu
        
        goBack();
    } catch (e) {
        alert('حدث خطأ');
    }
}

function sendReply() {
    alert('Send Reply logic (RAG integration coming later)');
}

function generateAIResponse() {
    alert('AI RAG Generation (Coming later)');
}
