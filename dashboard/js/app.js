// app.js - Main Router and App Controller
import { initInboxView } from './views/inbox.js';

class AppRouter {
    constructor() {
        this.routes = {
            'inbox': this.loadInbox.bind(this),
            'students': this.loadPlaceholder.bind(this, '👥 نظام إدارة الطلاب قريباً...'),
            'stats': this.loadPlaceholder.bind(this, '📊 الإحصائيات قريباً...'),
            'faq': this.loadPlaceholder.bind(this, '🧠 مدير الذكاء الاصطناعي والأسئلة الشائعة قريباً...'),
            'settings': this.loadPlaceholder.bind(this, '⚙️ الإعدادات والصلاحيات قريباً...')
        };
        
        this.currentRoute = null;
        this.init();
    }

    init() {
        // Handle Sidebar Clicks
        document.querySelectorAll('.sidebar-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const route = e.currentTarget.getAttribute('data-route');
                if (route) this.navigate(route);
            });
        });

        // Check if admin is already logged in (from previous script logic or telegram)
        if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe && window.Telegram.WebApp.initDataUnsafe.user) {
            window.adminId = window.Telegram.WebApp.initDataUnsafe.user.id;
            window.Telegram.WebApp.expand();
            this.navigate('inbox');
        } else {
            // Listen for manual login event
            window.addEventListener('admin-logged-in', () => {
                this.navigate('inbox');
            });
            document.getElementById('config-overlay').style.display = 'flex';
        }
    }

    navigate(route) {
        if (!this.routes[route]) return;
        
        // Update Sidebar UI
        document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
        const activeItem = document.querySelector(`.sidebar-item[data-route="${route}"]`);
        if (activeItem) activeItem.classList.add('active');

        // Clear and load new view
        const mainContent = document.getElementById('main-content');
        mainContent.innerHTML = ''; // basic cleanup, in a real framework we'd unmount
        
        this.currentRoute = route;
        this.routes[route](mainContent);
    }

    loadInbox(container) {
        initInboxView(container);
    }

    loadPlaceholder(text, container) {
        container.innerHTML = `
            <div class="module-view active" style="display:flex; align-items: center; justify-content: center; height:100%;">
                <h2 style="color: var(--text-muted);">${text}</h2>
            </div>
        `;
    }
}

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
    window.app = new AppRouter();
});
