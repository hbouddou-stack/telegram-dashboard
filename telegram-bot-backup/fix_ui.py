import sys

# --- 1. Fix admin.html ---
with open('dashboard/admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

search_header = '''                <div style="display: flex; gap: 10px; align-items: center;">
                    <button class="btn btn-secondary btn-sm" style="background: rgba(212, 175, 55, 0.15); color: var(--gold); border-color: var(--gold); font-weight: bold;" onclick="window.toggleFullTranscriptPanel()">📖 عرض التفريغ الكامل للدرس</button>
                    <button class="btn btn-secondary btn-sm" onclick="window.closeAxesEditor()">✖ إغلاق اللوحة</button>
                </div>'''
replace_header = '''                <div style="display: flex; gap: 10px; align-items: center;">
                    <button class="btn btn-secondary btn-sm" id="btn-toggle-sidebar" onclick="window.toggleAxesSidebar()" style="font-weight: bold;" title="إخفاء أو إظهار قائمة المحاور الجانبية لتوسيع مساحة العمل">☰ قائمة المحاور</button>
                    <button class="btn btn-secondary btn-sm" style="background: rgba(212, 175, 55, 0.15); color: var(--gold); border-color: var(--gold); font-weight: bold;" onclick="window.toggleFullTranscriptPanel()">📖 عرض التفريغ الكامل للدرس</button>
                    <button class="btn btn-secondary btn-sm" onclick="window.closeAxesEditor()">✖ إغلاق اللوحة</button>
                </div>'''
html = html.replace(search_header, replace_header)

search_sidebar = '''                <!-- Sidebar -->
                <div class="axes-sidebar">'''
replace_sidebar = '''                <!-- Sidebar -->
                <div class="axes-sidebar" id="axes-sidebar-container" style="transition: all 0.3s ease;">'''
html = html.replace(search_sidebar, replace_sidebar)

with open('dashboard/admin.html', 'w', encoding='utf-8') as f:
    f.write(html)


# --- 2. Fix admin.js ---
with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Fix Tabs styling
search_tabs = '''                <!-- TABS -->
                <div style="display: flex; gap: 10px; margin-bottom: 15px; border-bottom: 2px solid rgba(212, 175, 55, 0.2); padding-bottom: 10px;">
                    <button class="btn btn-primary" id="tab-btn-video" onclick="window.switchEditorTab('video')" style="background: var(--primary); color: white;">🎥 تحرير التفريغ (Karaoké)</button>
                    <button class="btn" id="tab-btn-reading" onclick="window.switchEditorTab('reading')" style="background: transparent; border: 1px solid var(--primary); color: var(--text-color);">📖 تحرير وضع القراءة (Lecture)</button>
                </div>'''
replace_tabs = '''                <!-- TABS -->
                <div style="display: flex; gap: 10px; margin-bottom: 15px; border-bottom: 2px solid rgba(212, 175, 55, 0.2); padding-bottom: 10px;">
                    <button class="btn" id="tab-btn-video" onclick="window.switchEditorTab('video')" style="background: var(--text-primary, #333); color: var(--bg-primary, #fff); border: 1px solid var(--text-primary, #333); font-weight: bold; font-size: 1.05rem;">🎥 تحرير التفريغ (Karaoké)</button>
                    <button class="btn" id="tab-btn-reading" onclick="window.switchEditorTab('reading')" style="background: transparent; color: var(--text-primary, #333); border: 1px solid var(--text-primary, #333); font-weight: bold; font-size: 1.05rem;">📖 تحرير وضع القراءة (Lecture)</button>
                </div>'''
js = js.replace(search_tabs, replace_tabs)

search_tab_logic = '''            if (tabName === 'video') {
                btnVideo.style.background = 'var(--primary)';
                btnVideo.style.color = 'white';
                btnReading.style.background = 'transparent';
                btnReading.style.color = 'var(--text-color)';'''
replace_tab_logic = '''            if (tabName === 'video') {
                btnVideo.style.background = 'var(--text-primary, #333)';
                btnVideo.style.color = 'var(--bg-primary, #fff)';
                btnReading.style.background = 'transparent';
                btnReading.style.color = 'var(--text-primary, #333)';'''
js = js.replace(search_tab_logic, replace_tab_logic)

search_tab_logic2 = '''            } else {
                btnReading.style.background = 'var(--primary)';
                btnReading.style.color = 'white';
                btnVideo.style.background = 'transparent';
                btnVideo.style.color = 'var(--text-color)';'''
replace_tab_logic2 = '''            } else {
                btnReading.style.background = 'var(--text-primary, #333)';
                btnReading.style.color = 'var(--bg-primary, #fff)';
                btnVideo.style.background = 'transparent';
                btnVideo.style.color = 'var(--text-primary, #333)';'''
js = js.replace(search_tab_logic2, replace_tab_logic2)

# Fix Chrono and Title
search_title_chrono = '''                <div style="display: flex; gap: 15px; margin-bottom: 15px; flex-wrap: wrap;">
                    <div class="editor-card" style="flex: 1; min-width: 250px; margin-bottom: 0;">
                        <div class="editor-card-title">📌 عنوان المحور</div>
                        <input type="text" class="axes-input" value="${escapeHtml(block.title)}" placeholder="اكتب عنوان المحور هنا..." oninput="currentAxesEditing.blocks[activeAxisIdx].title = this.value; window.updateAxisSidebarTitle(activeAxisIdx); window.updateLiveStudentPreview();">
                        <label style="display: flex; align-items: center; gap: 8px; margin-top: 10px; cursor: pointer; font-weight: bold; color: var(--text-secondary);">
                            <input type="checkbox" onchange="currentAxesEditing.blocks[activeAxisIdx].is_sub_theme = this.checked;" ${block.is_sub_theme ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer; accent-color: var(--primary);">
                            <span>هذا المحور هو محور فرعي (Sous-thématique)</span>
                        </label>
                    </div>

                    <div class="editor-card" style="min-width: 200px; margin-bottom: 0;">
                        <div class="editor-card-title">⏱ الكرونو (بداية المحور)</div>
                        <div style="display: flex; gap: 8px; align-items: center; justify-content: center; background: var(--bg-primary); padding: 5px 10px; border-radius: 8px; border: 1px solid var(--border-color);">
                            <input type="number" id="chrono-mm" class="axes-input" value="${mm}" style="width: 60px; text-align: center; font-family: monospace; padding: 5px; margin: 0; background: transparent; border: none; font-size: 1.1rem;" placeholder="دقيقة" min="0" max="180" oninput="window.updateChronoFromInputs()">
                            <span style="font-weight: bold; color: var(--text-secondary);">:</span>
                            <input type="number" id="chrono-ss" class="axes-input" value="${ss}" style="width: 60px; text-align: center; font-family: monospace; padding: 5px; margin: 0; background: transparent; border: none; font-size: 1.1rem;" placeholder="ثانية" min="0" max="59" oninput="window.updateChronoFromInputs()">
                        </div>
                    </div>
                </div>'''

replace_title_chrono = '''                <div style="display: flex; gap: 15px; margin-bottom: 15px; align-items: flex-start; flex-wrap: wrap; background: rgba(0,0,0,0.02); padding: 10px; border-radius: 8px; border: 1px solid var(--border-color);">
                    <div style="flex: 1; min-width: 250px;">
                        <label style="font-weight: bold; color: var(--text-secondary); display: block; margin-bottom: 6px; font-size: 0.95rem;">📌 عنوان المحور (Titre)</label>
                        <input type="text" value="${escapeHtml(block.title)}" placeholder="اكتب عنوان المحور هنا..." oninput="currentAxesEditing.blocks[activeAxisIdx].title = this.value; window.updateAxisSidebarTitle(activeAxisIdx); window.updateLiveStudentPreview();" style="width: 100%; padding: 8px 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; background: #fff; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1); color: #333;">
                        <label style="display: flex; align-items: center; gap: 8px; margin-top: 8px; cursor: pointer; font-weight: bold; color: var(--text-secondary); font-size: 0.85rem;">
                            <input type="checkbox" onchange="currentAxesEditing.blocks[activeAxisIdx].is_sub_theme = this.checked;" ${block.is_sub_theme ? 'checked' : ''} style="width: 16px; height: 16px; cursor: pointer; accent-color: var(--primary);">
                            <span>هذا المحور هو محور فرعي (Sous-thématique)</span>
                        </label>
                    </div>

                    <div style="min-width: 150px;">
                        <label style="font-weight: bold; color: var(--text-secondary); display: block; margin-bottom: 6px; font-size: 0.95rem;">⏱ الكرونو (MM:SS)</label>
                        <div style="display: flex; gap: 4px; align-items: center; background: #fff; padding: 4px 8px; border-radius: 6px; border: 1px solid #ccc; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1); direction: ltr; justify-content: center;">
                            <input type="number" id="chrono-mm" value="${mm}" style="width: 50px; text-align: center; font-family: monospace; padding: 4px; margin: 0; background: transparent; border: none; font-size: 1.1rem; color: #333; outline: none;" placeholder="MM" min="0" max="180" oninput="window.updateChronoFromInputs()">
                            <span style="font-weight: bold; color: #666; font-size: 1.2rem;">:</span>
                            <input type="number" id="chrono-ss" value="${ss}" style="width: 50px; text-align: center; font-family: monospace; padding: 4px; margin: 0; background: transparent; border: none; font-size: 1.1rem; color: #333; outline: none;" placeholder="SS" min="0" max="59" oninput="window.updateChronoFromInputs()">
                        </div>
                    </div>
                </div>'''
js = js.replace(search_title_chrono, replace_title_chrono)

# Add toggleAxesSidebar function
search_toggle_func = '''        window.closeAxesEditor = function() {'''
replace_toggle_func = '''        window.toggleAxesSidebar = function() {
            const sidebar = document.getElementById('axes-sidebar-container');
            const btn = document.getElementById('btn-toggle-sidebar');
            if (sidebar.style.display === 'none') {
                sidebar.style.display = 'flex';
                btn.style.background = '';
                btn.style.color = '';
            } else {
                sidebar.style.display = 'none';
                btn.style.background = 'var(--primary)';
                btn.style.color = 'white';
            }
        };

        window.closeAxesEditor = function() {'''
js = js.replace(search_toggle_func, replace_toggle_func)

with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
    f.write(js)
