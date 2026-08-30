// students.js - Students Roster View

let studentsData = [
    { id: '1051', telegram_id: '998877665', name: 'أحمد', last_active: '2026-08-30T10:00:00Z', tickets_count: 3, total_paid: '50$' },
    { id: '1052', telegram_id: '112233445', name: 'ياسر', last_active: '2026-08-29T14:30:00Z', tickets_count: 1, total_paid: '0$' },
    { id: '1053', telegram_id: '556677889', name: 'محمد', last_active: '2026-08-28T09:15:00Z', tickets_count: 5, total_paid: '150$' },
    { id: '1054', telegram_id: '445566778', name: 'فاطمة', last_active: '2026-08-25T11:45:00Z', tickets_count: 2, total_paid: '100$' }
];

export function initStudentsView(container) {
    container.innerHTML = `
        <section class="view active module-view" style="position:relative; background: var(--bg);">
            <header class="app-header" style="border-bottom: 1px solid var(--border);">
                <div class="header-left">
                    <button class="hamburger-btn" onclick="toggleSidebar()">☰</button>
                    <div class="header-titles">
                        <h1>👥 سجل الطلاب</h1>
                        <span class="header-subtitle">الطلاب الذين تواصلوا مع الدعم</span>
                    </div>
                </div>
                <div class="search-bar" style="margin-right: 15px; flex:1;">
                    <input type="text" id="student-search" placeholder="بحث بالاسم أو المعرف..." style="width: 100%; padding: 8px 15px; border-radius: 20px; border: 1px solid var(--border); background: var(--surface-hover); color: var(--text-1); outline:none;">
                </div>
            </header>
            
            <div id="students-list" style="padding: 20px; overflow-y: auto; height: calc(100vh - 70px);">
                <!-- Rendered via JS -->
            </div>
        </section>
    `;

    document.getElementById('student-search').addEventListener('input', (e) => {
        renderStudents(e.target.value);
    });

    renderStudents();
}

function renderStudents(query = '') {
    const list = document.getElementById('students-list');
    
    let filtered = studentsData;
    if (query.trim() !== '') {
        const q = query.toLowerCase();
        filtered = studentsData.filter(s => s.name.toLowerCase().includes(q) || s.telegram_id.includes(q));
    }

    if (filtered.length === 0) {
        list.innerHTML = '<div style="text-align:center; padding: 40px; color: var(--text-muted);">لا توجد نتائج</div>';
        return;
    }

    list.innerHTML = `
        <table style="width: 100%; border-collapse: collapse; color: var(--text-1); text-align: right;">
            <thead>
                <tr style="border-bottom: 1px solid var(--border); color: var(--text-muted);">
                    <th style="padding: 15px 10px;">الاسم</th>
                    <th style="padding: 15px 10px;">ID تليجرام</th>
                    <th style="padding: 15px 10px;">التذاكر</th>
                    <th style="padding: 15px 10px;">المدفوعات</th>
                    <th style="padding: 15px 10px;">إجراء</th>
                </tr>
            </thead>
            <tbody>
                ${filtered.map(s => `
                    <tr style="border-bottom: 1px solid var(--border); transition: 0.2s;" onmouseover="this.style.background='var(--surface-hover)'" onmouseout="this.style.background='transparent'">
                        <td style="padding: 15px 10px; font-weight: bold; color: var(--gold);">${s.name}</td>
                        <td style="padding: 15px 10px; color: var(--text-2); font-family: monospace;">${s.telegram_id}</td>
                        <td style="padding: 15px 10px;"><span class="tag" style="background: rgba(46, 204, 113, 0.2); color: #2ecc71;">${s.tickets_count} تذاكر</span></td>
                        <td style="padding: 15px 10px; color: var(--text-2);">${s.total_paid}</td>
                        <td style="padding: 15px 10px;">
                            <button class="btn btn-sm" style="padding: 5px 10px; font-size: 0.8rem;" onclick="alert('عرض سجل التذاكر للطالب قريباً')">📄 السجل</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}
