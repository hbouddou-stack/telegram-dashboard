import re
import io

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update HTML filter block (approx lines 406 to 445)
OLD_FILTER_SECTION = '''    <div id="tab-students" class="tab-content active">
        <!-- Intelligent Compact Filters at the very top -->
        <div class="filter-section">
            <!-- Gender filter row with colors: Blue (Male) and Pink (Female) taking full width 50/50 -->
            <div style="display: flex; gap: 10px; justify-content: center; width: 100%; margin-bottom: 8px;">
                <div class="chip-gender chip-all active" id="g-all" onclick="setGenderFilter('all', this)" style="flex:1; text-align:center; padding: 12px; font-size: 0.9rem;">👥 الكل (Tous)</div>
                <div class="chip-gender chip-male" id="g-homme" onclick="setGenderFilter('homme', this)" style="flex:1; text-align:center; padding: 12px; font-size: 0.9rem;">👨 ذكور</div>
                <div class="chip-gender chip-female" id="g-femme" onclick="setGenderFilter('femme', this)" style="flex:1; text-align:center; padding: 12px; font-size: 0.9rem;">👩 إناث</div>
            </div>
            
            <!-- Compact selection for Level and Status side-by-side -->
            <div style="display: grid; grid-template-columns: 1fr 1.2fr 1.2fr; gap: 10px; margin-top: 4px;">
                <div>
                    <div class="filter-title">السنة الدراسية</div>
                    <select id="level-select" onchange="setLevelFilter(this.value)" style="width:100%; padding:9px 12px; background:var(--bg); border:1px solid var(--border); border-radius:10px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.82rem; cursor:pointer;">
                        <option value="all">جميع السنوات</option>
                        <option value="1">السنة الأولى (1)</option>
                        <option value="2">السنة الثانية (2)</option>
                        <option value="3">السنة الثالثة (3)</option>
                        <option value="4">السنة الرابعة (4)</option>
                    </select>
                </div>
                <div>
                    <div class="filter-title">حالة الربط</div>
                    <select id="status-select" onchange="setStatusFilter(this.value)" style="width:100%; padding:9px 12px; background:var(--bg); border:1px solid var(--border); border-radius:10px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.82rem; cursor:pointer;">
                        <option value="all">كل الحالات</option>
                        <option value="linked">✅ مرتبط بتيليجرام</option>
                        <option value="unlinked">❌ غير مرتبط</option>
                        <option value="paid">✅ مسدد (Payé)</option>
                        <option value="unpaid">❌ غير مسدد (Non Payé)</option>
                    </select>
                </div>
                <div>
                    <div class="filter-title">المصدر (Source)</div>
                    <select id="source-select" onchange="setSourceFilter(this.value)" style="width:100%; padding:9px 12px; background:var(--bg); border:1px solid var(--border); border-radius:10px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.82rem; cursor:pointer;">
                        <option value="all">كل المصادر</option>
                        <option value="sheet">📊 Sheet</option>
                        <option value="excel">📗 Excel</option>
                        <option value="manuel">✍️ يدوي (Manuel)</option>
                    </select>
                </div>
            </div>
        </div>'''

NEW_FILTER_SECTION = '''    <div id="tab-students" class="tab-content active">
        <!-- ===== REFONTE FILTRES ===== -->
        <div class="filter-section" style="padding:10px 12px 6px;">

            <!-- GENRE: Pill buttons collés -->
            <div style="display:flex; gap:0; margin-bottom:10px; border-radius:12px; overflow:hidden; border:1px solid var(--border);">
                <div class="pill-btn pill-active" id="g-all" onclick="setGenderFilter('all', this)" style="flex:1; text-align:center; padding:11px 6px; font-size:0.88rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">👥 الكل</div>
                <div class="pill-btn" id="g-homme" onclick="setGenderFilter('homme', this)" style="flex:1; text-align:center; padding:11px 6px; font-size:0.88rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">👨 ذكور</div>
                <div class="pill-btn" id="g-femme" onclick="setGenderFilter('femme', this)" style="flex:1; text-align:center; padding:11px 6px; font-size:0.88rem; font-weight:700; cursor:pointer;">👩 إناث</div>
            </div>

            <!-- TELEGRAM STATUS: Pill buttons -->
            <div style="display:flex; gap:0; margin-bottom:10px; border-radius:12px; overflow:hidden; border:1px solid var(--border);">
                <div class="pill-btn pill-active" id="tg-all" onclick="setTelegramFilter('all', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.75rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">🌍 الكل</div>
                <div class="pill-btn" id="tg-bot" onclick="setTelegramFilter('bot', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.75rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">✅ بدأ البوت</div>
                <div class="pill-btn" id="tg-group" onclick="setTelegramFilter('group', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.75rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">🏘️ انضم المجموعة</div>
                <div class="pill-btn" id="tg-none" onclick="setTelegramFilter('none', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.75rem; font-weight:700; cursor:pointer;">❌ لم يبدأ</div>
            </div>

            <!-- PAIEMENT + SOURCE + NIVEAU: côte à côte -->
            <div style="display:flex; gap:8px; margin-bottom:4px;">
                <!-- Paiement Pill -->
                <div style="flex:1.3; display:flex; gap:0; border-radius:12px; overflow:hidden; border:1px solid var(--border);">
                    <div class="pill-btn pill-active" id="pay-all" onclick="setPayFilter('all', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.75rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">💰 الكل</div>
                    <div class="pill-btn" id="pay-paid" onclick="setPayFilter('paid', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.75rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">🟢 مسدد</div>
                    <div class="pill-btn" id="pay-unpaid" onclick="setPayFilter('unpaid', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.75rem; font-weight:700; cursor:pointer;">🔴 غير مسدد</div>
                </div>
                <!-- Source select compact -->
                <select id="source-select" onchange="setSourceFilter(this.value)" style="flex:1; padding:8px 6px; background:var(--bg); border:1px solid var(--border); border-radius:12px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.75rem; cursor:pointer; font-weight:700;">
                    <option value="all">📁 كل المصادر</option>
                    <option value="excel">📗 Excel</option>
                    <option value="sheet">📊 Sheet</option>
                    <option value="manuel">✍️ يدوي</option>
                </select>
                <!-- Niveau select compact -->
                <select id="level-select" onchange="setLevelFilter(this.value)" style="flex:0.7; padding:8px 6px; background:var(--bg); border:1px solid var(--border); border-radius:12px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.75rem; cursor:pointer; font-weight:700;">
                    <option value="all">📚 الكل</option>
                    <option value="1">سنة 1</option>
                    <option value="2">سنة 2</option>
                    <option value="3">سنة 3</option>
                    <option value="4">سنة 4</option>
                </select>
            </div>
        </div>'''

# We know old filter section didn't match exactly because of "paid/unpaid" options being different maybe?
# Let's use regex to replace it
html = re.sub(
    r'<div id="tab-students" class="tab-content active">.*?<!-- COLOR FILTERS -->',
    NEW_FILTER_SECTION + '\n\n        <!-- COLOR FILTERS -->',
    html, flags=re.DOTALL
)

# 2. Replace old controls with new Sort Bar & View Toggle (lines 447 - 471)
OLD_CONTROLS = '''        <!-- COLOR FILTERS -->
        <div style="display: flex; gap: 8px; margin-bottom: 15px; overflow-x: auto; padding-bottom: 5px;">
            <div class="chip chip-color active" onclick="setColorFilter('all', this)" style="border-radius:20px;">🌍 الكل</div>
            <div class="chip chip-color" onclick="setColorFilter('green', this)" style="border-radius:20px; background: rgba(22, 163, 74, 0.1); color: #16a34a; border-color: #16a34a;">🟢 منضم للمجموعات</div>
            <div class="chip chip-color" onclick="setColorFilter('red', this)" style="border-radius:20px; background: rgba(239, 68, 68, 0.1); color: #ef4444; border-color: #ef4444;">🔴 لم ينضم بعد</div>
            <div class="chip chip-color" onclick="setColorFilter('orange', this)" style="border-radius:20px; background: rgba(249, 115, 22, 0.1); color: #f97316; border-color: #f97316;">🟠 في طور الانضمام</div>
            <div class="chip chip-color" onclick="setColorFilter('black', this)" style="border-radius:20px; background: rgba(17, 17, 17, 0.1); color: #111111; border-color: #111111;">⚫ مستبعد</div>
        </div>
        <input class="search-box" type="text" id="search-input" placeholder="🔍 بحث بالاسم أو البريد..." oninput="filterStudents()">
        <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px 15px; border-bottom: 1px solid var(--border);">
            <div style="font-weight: 800; color: var(--text1); font-size: 0.9rem;" id="students-count-display"></div>
            <div style="display:flex; gap:10px;">
                
                <button id="btn-mass-sms" onclick="sendMassSms()" style="background:#0ea5e9; color:white; border:none; padding:4px 10px; border-radius:6px; font-weight:bold; display:none; cursor:pointer; font-size:0.85rem; margin-right:10px;">
                    📱 إرسال SMS للكل (<span id="mass-sms-count">0</span>)
                </button>
    <select id="card-style-selector" onchange="changeCardStyle(this.value)" style="padding:4px 8px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-size:0.8rem; outline:none;">
                    <option value="1">✨ النموذج 1 (كلاسيكي)</option>
                    <option value="2">📋 النموذج 2 (حالة)</option>
                    <option value="3">📱 النموذج 3 (مدمج)</option>
                </select>
                <select id="view-mode-selector" onchange="changeViewMode(this.value)" style="padding:4px 8px; border-radius:6px; border:1px solid var(--border); background:var(--bg); color:var(--text1); font-size:0.8rem; outline:none;">
                    <option value="grid">🗂️ بطاقات</option>
                    <option value="table">📊 جدول</option>
                </select>
            </div>
        </div>'''

NEW_CONTROLS = '''        <!-- SEARCH + SORT + VIEW CONTROLS -->
        <div style="padding:8px 12px 6px;">
            <input class="search-box" type="text" id="search-input" placeholder="🔍 بحث بالاسم أو البريد أو الهاتف..." oninput="filterStudents()" style="margin-bottom:8px;">
            <!-- Sort bar -->
            <div style="display:flex; gap:6px; overflow-x:auto; padding-bottom:4px; flex-wrap:nowrap; align-items:center;">
                <span style="font-size:0.72rem; color:var(--text2); white-space:nowrap; font-weight:600;">ترتيب:</span>
                <div class="sort-btn sort-active" id="sort-date-desc" onclick="setSort('date','desc',this)" style="white-space:nowrap; padding:5px 10px; border-radius:20px; font-size:0.72rem; font-weight:700; cursor:pointer; border:1px solid var(--border); background:var(--accent2); color:white;">📅 الأحدث</div>
                <div class="sort-btn" id="sort-date-asc" onclick="setSort('date','asc',this)" style="white-space:nowrap; padding:5px 10px; border-radius:20px; font-size:0.72rem; font-weight:700; cursor:pointer; border:1px solid var(--border); background:var(--bg); color:var(--text1);">📅 الأقدم</div>
                <div class="sort-btn" id="sort-name-asc" onclick="setSort('name','asc',this)" style="white-space:nowrap; padding:5px 10px; border-radius:20px; font-size:0.72rem; font-weight:700; cursor:pointer; border:1px solid var(--border); background:var(--bg); color:var(--text1);">🔤 أ→ي</div>
                <div class="sort-btn" id="sort-id-desc" onclick="setSort('id','desc',this)" style="white-space:nowrap; padding:5px 10px; border-radius:20px; font-size:0.72rem; font-weight:700; cursor:pointer; border:1px solid var(--border); background:var(--bg); color:var(--text1);">🔢 رقم ↓</div>
            </div>
        </div>
        <!-- RESULT COUNT + VIEW TOGGLE + SMS BUTTON -->
        <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 12px 8px; border-bottom:1px solid var(--border);">
            <div id="students-count-display" style="font-weight:800; font-size:0.95rem; color:var(--accent2); background:rgba(10,132,255,0.1); padding:5px 12px; border-radius:20px;"></div>
            <div style="display:flex; gap:8px; align-items:center;">
                <button id="btn-mass-sms" onclick="sendMassSms()" style="background:#0ea5e9; color:white; border:none; padding:5px 10px; border-radius:20px; font-weight:bold; display:none; cursor:pointer; font-size:0.78rem;">
                    📱 SMS (<span id="mass-sms-count">0</span>)
                </button>
                <!-- VIEW TOGGLE -->
                <div style="display:flex; gap:0; border-radius:20px; overflow:hidden; border:1px solid var(--border);">
                    <div id="view-toggle-grid" onclick="changeViewMode('grid')" style="padding:6px 12px; cursor:pointer; font-size:0.82rem; font-weight:700; background:var(--accent2); color:white;">🃏</div>
                    <div id="view-toggle-table" onclick="changeViewMode('table')" style="padding:6px 12px; cursor:pointer; font-size:0.82rem; font-weight:700; background:var(--bg); color:var(--text1);">📊</div>
                </div>
            </div>
        </div>'''

html = html.replace(OLD_CONTROLS, NEW_CONTROLS)

# 3. Add CSS for pill buttons
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
if "/* ===== PILL BUTTONS ===== */" not in html:
    html = html.replace("</style>", pill_css + "\n</style>")

# 4. Modify filter object in the SECOND script
html = html.replace(
    "let filters = { status: 'all', gender: 'all', level: 'all', color: 'all', source: 'all' };",
    "let filters = { status: 'all', gender: 'all', level: 'all', color: 'all', source: 'all', telegram: 'all', payment: 'all' };"
)

# 5. Add pill logic and new functions to SECOND script
pill_logic = """
        // ===== PILL BUTTON LOGIC =====
        function _activatePill(groupPrefix, clickedEl) {
            document.querySelectorAll('[id^="' + groupPrefix + '"]').forEach(el => {
                el.classList.remove('pill-active');
            });
            if (clickedEl) clickedEl.classList.add('pill-active');
        }

        // Override existing filter triggers
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
        
        function setSort(key, order, el) {
            currentSort = { key, order };
            document.querySelectorAll('.sort-btn').forEach(b => {
                b.style.background = 'var(--bg)';
                b.style.color = 'var(--text1)';
            });
            if (el) { el.style.background = 'var(--accent2)'; el.style.color = 'white'; }
            filterStudents();
        }
        
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
html = html.replace(
    "function setGenderFilter(val, el) {",
    pill_logic + "\n        // Replaced old setGenderFilter\n        function oldSetGenderFilter(val, el) {"
)

# Remove the changeViewMode function from the first script to prevent duplicate overriding it back to dropdown
html = re.sub(r'function changeViewMode\(mode\)\s*{.*?}', '', html, count=1, flags=re.DOTALL)

# 6. Update filterStudents()
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
                const isPaid = String(s.payment_status || '').toUpperCase().trim() === 'PAID' || String(s.payment_status || '').toUpperCase().trim() === 'PAYE' || String(s.payment_status || '').toUpperCase().trim() === 'مسدد';
                
                const matchTelegram = filters.telegram === 'all'
                    || (filters.telegram === 'bot' && botStarted)
                    || (filters.telegram === 'group' && groupJoined)
                    || (filters.telegram === 'none' && !botStarted);
                
                const matchPayment = filters.payment === 'all'
                    || (filters.payment === 'paid' && isPaid)
                    || (filters.payment === 'unpaid' && !isPaid);

                const matchStatus = filters.status === 'all'
                    || (filters.status === 'linked' && linked)
                    || (filters.status === 'unlinked' && !linked);"""

html = html.replace(old_match, new_match)
html = html.replace(
    "return matchSearch && matchGender && matchLevel && matchStatus && matchColor && matchSource;",
    "return matchSearch && matchGender && matchLevel && matchStatus && matchColor && matchSource && matchTelegram && matchPayment;"
)

# 7. Update filterStudents() SORT logic
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
html = html.replace(old_sort, new_sort)

# 8. Update Counter Output
html = html.replace(
    "document.getElementById('students-count-display').textContent = `${filtered.length} طالب`;",
    "document.getElementById('students-count-display').innerHTML = `👥 <strong>${filtered.length}</strong> نتيجة <span style='font-size:0.75rem; opacity:0.7;'>(من ${allStudents.length})</span>`;"
)

# 9. Add Stats Tab HTML
stats_tab_html = """
    <!-- TAB: إحصاء -->
    <div id="tab-stats" class="tab-content">
        <div style="padding:16px 12px;">
            <h2 style="margin:0 0 16px; font-size:1.1rem; font-weight:800; color:var(--text1);">📈 الإحصائيات اليومية</h2>
            <div style="display:flex; gap:0; margin-bottom:16px; border-radius:12px; overflow:hidden; border:1px solid var(--border); width:fit-content;">
                <div class="pill-btn pill-active" id="stats-7" onclick="loadDailyStats(7, this)" style="padding:8px 18px; font-size:0.82rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">7 أيام</div>
                <div class="pill-btn" id="stats-30" onclick="loadDailyStats(30, this)" style="padding:8px 18px; font-size:0.82rem; font-weight:700; cursor:pointer;">30 يوم</div>
            </div>
            <div id="daily-chart-area" style="background:var(--card); border-radius:16px; padding:16px; margin-bottom:16px; min-height:160px; display:flex; align-items:flex-end; gap:6px; overflow-x:auto;">
                <div style="color:var(--text2); font-size:0.85rem; margin:auto;">جاري التحميل...</div>
            </div>
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
html = html.replace("</body>", stats_tab_html + "\n</body>")

# 10. Add Stats Navigation & load function
stats_nav = """        <div class="nav-item" onclick="switchTab('ghosts')" id="nav-ghosts">
            <span class="nav-icon">👻</span>
            <span>زوار</span>
        </div>
        <div class="nav-item" onclick="switchTab('stats')" id="nav-stats">
            <span class="nav-icon">📈</span>
            <span>إحصاء</span>
        </div>"""
html = html.replace(
    '<div class="nav-item" onclick="switchTab(\'ghosts\')" id="nav-ghosts">\n            <span class="nav-icon">👻</span>\n            <span>زوار</span>\n        </div>',
    stats_nav
)

stats_js = """
        // ===== DAILY STATS =====
        function loadDailyStats(days, el) {
            _activatePill('stats-', el);
            const chartArea = document.getElementById('daily-chart-area');
            const tbody = document.getElementById('daily-stats-body');
            if (!chartArea || !tbody) return;

            const now = new Date();
            const rows = [];
            for (let i = days - 1; i >= 0; i--) {
                const d = new Date(now);
                d.setDate(d.getDate() - i);
                const dateStr = d.toISOString().slice(0, 10);
                const dayStudents = allStudents.filter(s => (s.created_at || '').startsWith(dateStr));
                const paidCount = dayStudents.filter(s => {
                    const ps = String(s.payment_status||'').toUpperCase().trim();
                    return ps === 'PAID' || ps === 'PAYE' || ps === 'مسدد';
                }).length;
                rows.push({ date: dateStr, total: dayStudents.length, paid: paidCount, unpaid: dayStudents.length - paidCount });
            }

            const maxVal = Math.max(...rows.map(r => r.total), 1);
            chartArea.innerHTML = rows.map(r => {
                const h = Math.max(4, Math.round((r.total / maxVal) * 120));
                const dateLabel = r.date.slice(5);
                const paidPct = r.total > 0 ? Math.round((r.paid/r.total)*100) : 0;
                return `<div style="display:flex; flex-direction:column; align-items:center; gap:3px; min-width:36px; flex:1;">
                    <span style="font-size:0.65rem; font-weight:800; color:var(--accent2);">${r.total > 0 ? r.total : ''}</span>
                    <div style="width:100%; background:linear-gradient(180deg, var(--accent2), #60a5fa); border-radius:6px 6px 0 0; height:${h}px; position:relative; min-height:4px;" title="${r.date}: ${r.total} inscrits (${paidPct}% payés)">
                        <div style="position:absolute; bottom:0; width:100%; background:#16a34a; border-radius:0 0 6px 6px; height:${Math.round(h * r.paid / Math.max(r.total,1))}px;"></div>
                    </div>
                    <span style="font-size:0.6rem; color:var(--text2); white-space:nowrap;">${dateLabel}</span>
                </div>`;
            }).join('');

            tbody.innerHTML = rows.slice().reverse().map(r => `
                <tr style="border-top:1px solid var(--border);">
                    <td style="padding:9px 12px; font-weight:700;">${r.date}</td>
                    <td style="padding:9px 12px; font-weight:800; color:var(--accent2);">${r.total}</td>
                    <td style="padding:9px 12px; color:#16a34a; font-weight:700;">${r.paid}</td>
                    <td style="padding:9px 12px; color:#ef4444; font-weight:700;">${r.unpaid}</td>
                </tr>
            `).join('');
        }
"""
html = html.replace("</body>", f"<script>\n{stats_js}\n</script>\n</body>")

html = html.replace(
    "if(id === 'ghosts') loadGhostVisitors();",
    "if(id === 'ghosts') loadGhostVisitors();\n            if(id === 'stats') loadDailyStats(7, document.getElementById('stats-7'));"
)

# 11. Rename Gateway Admin subtitle
html = html.replace("<h1>🛠️ بوابة التحكم والربط</h1>", "<h1>🛠️ Gateway Admin</h1>")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Complete safe refonte written.")
