import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ==== 1. ADD CSS for pill buttons ====
pill_css = """
        /* ===== PILL BUTTONS ===== */
        .pill-btn {
            background: var(--bg);
            color: var(--text2);
            transition: all 0.15s ease;
            user-select: none;
        }
        .pill-btn:active { opacity: 0.7; }
        .pill-active {
            background: var(--accent2) !important;
            color: white !important;
        }
"""
html = html.replace("</style>", pill_css + "\n</style>")

# ==== 2. ADD JS for new filters + sort + view toggle ====
new_js = """
        // ===== NEW FILTER STATE =====
        let filters = { status: 'all', gender: 'all', level: 'all', color: 'all', source: 'all', telegram: 'all', payment: 'all' };

        // Pill button helper
        function _activatePill(groupPrefix, clickedEl) {
            document.querySelectorAll('[id^="' + groupPrefix + '"]').forEach(el => {
                el.classList.remove('pill-active');
            });
            if (clickedEl) clickedEl.classList.add('pill-active');
        }

        function setGenderFilter(val, el) {
            filters.gender = val;
            _activatePill('g-', el);
            filterStudents();
        }
        function setTelegramFilter(val, el) {
            filters.telegram = val;
            _activatePill('tg-', el);
            filterStudents();
        }
        function setPayFilter(val, el) {
            filters.payment = val;
            _activatePill('pay-', el);
            filterStudents();
        }
        function setStatusFilter(val) { filters.status = val; filterStudents(); }
        function setSourceFilter(val) { filters.source = val; filterStudents(); }
        function setLevelFilter(val) { filters.level = val; filterStudents(); }
        function setColorFilter(val, el) {
            filters.color = val;
            document.querySelectorAll('.chip-color').forEach(c => c.classList.remove('active'));
            if(el) el.classList.add('active');
            filterStudents();
        }

        // ===== SORT =====
        function setSort(key, order, el) {
            currentSort = { key, order };
            document.querySelectorAll('.sort-btn').forEach(b => {
                b.style.background = 'var(--bg)';
                b.style.color = 'var(--text1)';
            });
            if (el) { el.style.background = 'var(--accent2)'; el.style.color = 'white'; }
            filterStudents();
        }

        // ===== VIEW TOGGLE =====
        function changeViewMode(mode) {
            currentViewMode = mode;
            localStorage.setItem('viewMode', mode);
            const gridBtn = document.getElementById('view-toggle-grid');
            const tableBtn = document.getElementById('view-toggle-table');
            if (gridBtn && tableBtn) {
                if (mode === 'grid') {
                    gridBtn.style.background = 'var(--accent2)'; gridBtn.style.color = 'white';
                    tableBtn.style.background = 'var(--bg)'; tableBtn.style.color = 'var(--text1)';
                } else {
                    tableBtn.style.background = 'var(--accent2)'; tableBtn.style.color = 'white';
                    gridBtn.style.background = 'var(--bg)'; gridBtn.style.color = 'var(--text1)';
                }
            }
            filterStudents();
        }
"""

# Replace the old let filters = ... block and all old filter functions
old_init = """        let currentCardStyle = localStorage.getItem('cardStyle') || '1';
            let currentViewMode = localStorage.getItem('viewMode') || 'grid';
            let currentSort = { key: 'date', order: 'desc' };"""

new_init = """        let currentCardStyle = '1';
            let currentViewMode = localStorage.getItem('viewMode') || 'grid';
            let currentSort = { key: 'date', order: 'desc' };"""

html = html.replace(old_init, new_init + "\n" + new_js)

# ==== 3. UPDATE filterStudents() to handle new filters ====
# Find and update the matchStatus and matchGender logic
old_match = """                const linked = !!s.telegram_id;
                const isPaid = String(s.payment_status || '').toUpperCase() === 'PAID';
                const matchStatus = filters.status === 'all'
                    || (filters.status === 'linked' && linked)
                    || (filters.status === 'unlinked' && !linked)
                    || (filters.status === 'paid' && isPaid)
                    || (filters.status === 'unpaid' && !isPaid);"""

new_match = """                const linked = !!s.telegram_id;
                const botStarted = !!s.telegram_id;
                const groupJoined = !!s.group_joined || !!s.joined_at;
                const isPaid = String(s.payment_status || '').toUpperCase().trim() === 'PAID';
                
                // Telegram filter (new pills)
                const matchTelegram = filters.telegram === 'all'
                    || (filters.telegram === 'bot' && botStarted)
                    || (filters.telegram === 'group' && groupJoined)
                    || (filters.telegram === 'none' && !botStarted);
                
                // Payment filter (new pills)
                const matchPayment = filters.payment === 'all'
                    || (filters.payment === 'paid' && isPaid)
                    || (filters.payment === 'unpaid' && !isPaid);

                const matchStatus = filters.status === 'all'
                    || (filters.status === 'linked' && linked)
                    || (filters.status === 'unlinked' && !linked)
                    || (filters.status === 'paid' && isPaid)
                    || (filters.status === 'unpaid' && !isPaid);"""

html = html.replace(old_match, new_match)

# Update the return statement to include new filters
old_return = "return matchSearch && matchGender && matchLevel && matchStatus && matchColor && matchSource;"
new_return = "return matchSearch && matchGender && matchLevel && matchStatus && matchColor && matchSource && matchTelegram && matchPayment;"
html = html.replace(old_return, new_return)

# ==== 4. UPDATE SORT LOGIC in filterStudents ====
# Find and update sort logic
old_sort = """            filtered.sort((a, b) => {
                if (currentSort.key === 'name') {
                    return currentSort.order === 'asc'
                        ? (a.first_name || '').localeCompare(b.first_name || '')
                        : (b.first_name || '').localeCompare(a.first_name || '');
                }
                return 0;
            });"""

new_sort = """            filtered.sort((a, b) => {
                if (currentSort.key === 'name') {
                    return currentSort.order === 'asc'
                        ? (a.first_name || '').localeCompare(b.first_name || '')
                        : (b.first_name || '').localeCompare(a.first_name || '');
                }
                if (currentSort.key === 'id') {
                    const idA = parseInt(a.student_id) || 0;
                    const idB = parseInt(b.student_id) || 0;
                    return currentSort.order === 'desc' ? idB - idA : idA - idB;
                }
                if (currentSort.key === 'date') {
                    const dA = new Date(a.created_at || 0);
                    const dB = new Date(b.created_at || 0);
                    return currentSort.order === 'desc' ? dB - dA : dA - dB;
                }
                return 0;
            });"""

if old_sort in html:
    html = html.replace(old_sort, new_sort)
    print("Sort logic updated!")
else:
    print("WARNING: Sort logic not found - adding default sort by date desc at end of filter")

# ==== 5. UPDATE COUNT DISPLAY ====
old_count = 'document.getElementById(\'students-count-display\').textContent'
new_count_code = "document.getElementById('students-count-display').innerHTML"
# Replace the count display to show total vs filtered
html = html.replace(
    "document.getElementById('students-count-display').textContent = `${filtered.length} طالب`;",
    "document.getElementById('students-count-display').innerHTML = `👥 <strong>${filtered.length}</strong> نتيجة <span style='font-size:0.75rem; opacity:0.7;'>(من ${allStudents.length})</span>`;"
)

# ==== 6. ADD STATS TAB CONTENT ====
stats_tab_html = """
    <!-- TAB: إحصاء -->
    <div id="tab-stats" class="tab-content">
        <div style="padding:16px 12px;">
            <h2 style="margin:0 0 16px; font-size:1.1rem; font-weight:800; color:var(--text1);">📈 الإحصائيات اليومية</h2>
            <!-- Period toggle -->
            <div style="display:flex; gap:0; margin-bottom:16px; border-radius:12px; overflow:hidden; border:1px solid var(--border); width:fit-content;">
                <div class="pill-btn pill-active" id="stats-7" onclick="loadDailyStats(7, this)" style="padding:8px 18px; font-size:0.82rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">7 أيام</div>
                <div class="pill-btn" id="stats-30" onclick="loadDailyStats(30, this)" style="padding:8px 18px; font-size:0.82rem; font-weight:700; cursor:pointer;">30 يوم</div>
            </div>
            <!-- Chart area -->
            <div id="daily-chart-area" style="background:var(--card); border-radius:16px; padding:16px; margin-bottom:16px; min-height:160px; display:flex; align-items:flex-end; gap:6px; overflow-x:auto;">
                <div style="color:var(--text2); font-size:0.85rem; margin:auto;">جاري التحميل...</div>
            </div>
            <!-- Daily table -->
            <div style="background:var(--card); border-radius:16px; overflow:hidden;">
                <table id="daily-stats-table" style="width:100%; border-collapse:collapse; font-size:0.82rem;">
                    <thead>
                        <tr style="background:rgba(10,132,255,0.08); text-align:right;">
                            <th style="padding:10px 12px; color:var(--text2); font-weight:700;">📅 التاريخ</th>
                            <th style="padding:10px 12px; color:var(--text2); font-weight:700;">👥 مسجلون</th>
                            <th style="padding:10px 12px; color:#16a34a; font-weight:700;">🟢 مسددون</th>
                            <th style="padding:10px 12px; color:#ef4444; font-weight:700;">🔴 غير مسددين</th>
                        </tr>
                    </thead>
                    <tbody id="daily-stats-body">
                        <tr><td colspan="4" style="padding:20px; text-align:center; color:var(--text2);">جاري التحميل...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
"""

# Inject stats tab before closing body
if 'id="tab-stats"' not in html:
    html = html.replace("</body>", stats_tab_html + "\n</body>")
    print("Stats tab injected!")

# ==== 7. ADD STATS JS ====
stats_js = """
        // ===== DAILY STATS =====
        async function loadDailyStats(days, el) {
            _activatePill('stats-', el);
            const chartArea = document.getElementById('daily-chart-area');
            const tbody = document.getElementById('daily-stats-body');
            if (!chartArea || !tbody) return;

            // Compute from allStudents (no API needed!)
            const now = new Date();
            const rows = [];
            for (let i = days - 1; i >= 0; i--) {
                const d = new Date(now);
                d.setDate(d.getDate() - i);
                const dateStr = d.toISOString().slice(0, 10);
                const dayStudents = allStudents.filter(s => (s.created_at || '').startsWith(dateStr));
                const paidCount = dayStudents.filter(s => String(s.payment_status||'').toUpperCase().trim() === 'PAID').length;
                rows.push({ date: dateStr, total: dayStudents.length, paid: paidCount, unpaid: dayStudents.length - paidCount });
            }

            // Build bar chart
            const maxVal = Math.max(...rows.map(r => r.total), 1);
            chartArea.innerHTML = rows.map(r => {
                const h = Math.max(4, Math.round((r.total / maxVal) * 120));
                const dateLabel = r.date.slice(5); // MM-DD
                const paidPct = r.total > 0 ? Math.round((r.paid/r.total)*100) : 0;
                return `<div style="display:flex; flex-direction:column; align-items:center; gap:3px; min-width:36px; flex:1;">
                    <span style="font-size:0.65rem; font-weight:800; color:var(--accent2);">${r.total > 0 ? r.total : ''}</span>
                    <div style="width:100%; background:linear-gradient(180deg, var(--accent2), #60a5fa); border-radius:6px 6px 0 0; height:${h}px; position:relative; min-height:4px;" title="${r.date}: ${r.total} inscrits (${paidPct}% payés)">
                        <div style="position:absolute; bottom:0; width:100%; background:#16a34a; border-radius:0 0 6px 6px; height:${Math.round(h * r.paid / Math.max(r.total,1))}px;"></div>
                    </div>
                    <span style="font-size:0.6rem; color:var(--text2); white-space:nowrap;">${dateLabel}</span>
                </div>`;
            }).join('');

            // Build table
            tbody.innerHTML = rows.slice().reverse().map(r => `
                <tr style="border-top:1px solid var(--border);">
                    <td style="padding:9px 12px; font-weight:700;">${r.date}</td>
                    <td style="padding:9px 12px; font-weight:800; color:var(--accent2);">${r.total}</td>
                    <td style="padding:9px 12px; color:#16a34a; font-weight:700;">${r.paid}</td>
                    <td style="padding:9px 12px; color:#ef4444; font-weight:700;">${r.unpaid}</td>
                </tr>
            `).join('');
        }

        // Auto-load stats when tab is opened
        const _origSwitchTab = window.switchTab;
"""

if 'loadDailyStats' not in html:
    html = html.replace("</body>", f"<script>\n{stats_js}\n</script>\n</body>")
    print("Stats JS injected!")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Phase 2 done!")
