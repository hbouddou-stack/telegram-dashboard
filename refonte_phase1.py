import io, re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ==============================================================
# 1. ADD STATS TAB TO BOTTOM NAV
# ==============================================================
html = html.replace(
    '<div class="nav-item" onclick="switchTab(\'ghosts\')" id="nav-ghosts">\n            <span class="nav-icon">👻</span>\n            <span>زوار</span>\n        </div>',
    '<div class="nav-item" onclick="switchTab(\'ghosts\')" id="nav-ghosts">\n            <span class="nav-icon">👻</span>\n            <span>زوار</span>\n        </div>\n        <div class="nav-item" onclick="switchTab(\'stats\')" id="nav-stats">\n            <span class="nav-icon">📈</span>\n            <span>إحصاء</span>\n        </div>'
)

# ==============================================================
# 2. REPLACE THE FULL FILTER SECTION (lines 407-473)
# ==============================================================
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
                <div class="pill-btn pill-active" id="tg-all" onclick="setTelegramFilter('all', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.78rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">🌍 الكل</div>
                <div class="pill-btn" id="tg-bot" onclick="setTelegramFilter('bot', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.78rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">✅ بدأ البوت</div>
                <div class="pill-btn" id="tg-group" onclick="setTelegramFilter('group', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.78rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">🏘️ انضم المجموعة</div>
                <div class="pill-btn" id="tg-none" onclick="setTelegramFilter('none', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.78rem; font-weight:700; cursor:pointer;">❌ لم يبدأ</div>
            </div>

            <!-- PAIEMENT + SOURCE: côte à côte -->
            <div style="display:flex; gap:8px; margin-bottom:8px;">
                <!-- Paiement Pill -->
                <div style="flex:1.2; display:flex; gap:0; border-radius:12px; overflow:hidden; border:1px solid var(--border);">
                    <div class="pill-btn pill-active" id="pay-all" onclick="setPayFilter('all', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.78rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">💰 الكل</div>
                    <div class="pill-btn" id="pay-paid" onclick="setPayFilter('paid', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.78rem; font-weight:700; cursor:pointer; border-left:1px solid var(--border);">🟢 مسدد</div>
                    <div class="pill-btn" id="pay-unpaid" onclick="setPayFilter('unpaid', this)" style="flex:1; text-align:center; padding:9px 4px; font-size:0.78rem; font-weight:700; cursor:pointer;">🔴 غير مسدد</div>
                </div>
                <!-- Source select compact -->
                <select id="source-select" onchange="setSourceFilter(this.value)" style="flex:1; padding:8px 6px; background:var(--bg); border:1px solid var(--border); border-radius:12px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.78rem; cursor:pointer; font-weight:700;">
                    <option value="all">📁 كل المصادر</option>
                    <option value="excel">📗 Excel</option>
                    <option value="sheet">📊 Sheet</option>
                    <option value="manuel">✍️ يدوي</option>
                </select>
                <!-- Niveau select compact -->
                <select id="level-select" onchange="setLevelFilter(this.value)" style="flex:0.7; padding:8px 6px; background:var(--bg); border:1px solid var(--border); border-radius:12px; color:var(--text1); font-family:'Tajawal'; outline:none; font-size:0.78rem; cursor:pointer; font-weight:700;">
                    <option value="all">📚 الكل</option>
                    <option value="1">سنة 1</option>
                    <option value="2">سنة 2</option>
                    <option value="3">سنة 3</option>
                    <option value="4">سنة 4</option>
                </select>
            </div>
        </div>'''

if OLD_FILTER_SECTION in html:
    html = html.replace(OLD_FILTER_SECTION, NEW_FILTER_SECTION)
    print("Filter section replaced!")
else:
    print("ERROR: Could not find old filter section - checking partial match...")
    if 'chip-gender chip-all active' in html:
        print("Found chip-gender - partial match exists")

# ==============================================================
# 3. REMOVE old color filter row + card-style-selector + view-mode dropdown
#    REPLACE with: SORT BAR + COUNT BADGE + VIEW TOGGLE
# ==============================================================
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

if OLD_CONTROLS in html:
    html = html.replace(OLD_CONTROLS, NEW_CONTROLS)
    print("Controls section replaced!")
else:
    print("WARNING: Could not find old controls section exactly - trying partial...")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Phase 1 done!")
