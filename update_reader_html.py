import re

with open('dashboard/reader.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the bottom nav
old_nav = '''        <button class="nav-btn" id="btn-nav-practice" style="display:none;" onclick="switchTab('practice', this)">
            <span class="icon">🎯</span><span>التدريبات</span>
        </button>'''
new_nav = '''        <button class="nav-btn" id="btn-nav-exams" onclick="switchTab('exams', this)">
            <span class="icon">📝</span><span>الامتحانات</span>
        </button>'''
content = content.replace(old_nav, new_nav)
content = content.replace('id="btn-nav-practice" onclick="switchTab(''practice'', this)"', 'id="btn-nav-exams" onclick="switchTab(''exams'', this)"')

# 2. Add the exam generator tab before tab-practice
exam_tab = '''
    <!-- TAB: EXAMS WIZARD -->
    <div class="tab-panel" id="tab-exams" style="background: var(--bg); min-height: 100vh; padding-bottom: 80px;">
        <div style="padding: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h2 style="margin:0; color:var(--text); font-size:24px;">مولد الامتحانات</h2>
                <button onclick="examWizard.reset()" style="background:transparent; border:none; color:var(--primary); font-weight:bold; cursor:pointer;">إعادة ضبط</button>
            </div>
            
            <!-- STEP 1: SUBJECT -->
            <div id="exam-step-1" style="display:block;">
                <h3 style="color:var(--text-2); margin-bottom:12px; font-size:16px;">1. اختر المادة</h3>
                <div id="exam-subject-grid" style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
                    <div class="exam-subject-card" data-subject="sira" onclick="examWizard.selectSubject('sira')" style="background:var(--surface); border-radius:12px; padding:16px; text-align:center; cursor:pointer; box-shadow:var(--shadow-sm); border:2px solid transparent;">
                        <div style="font-size:32px; margin-bottom:8px;">📜</div>
                        <div style="font-weight:bold;">السيرة</div>
                    </div>
                    <div class="exam-subject-card" data-subject="fiqh" onclick="examWizard.selectSubject('fiqh')" style="background:var(--surface); border-radius:12px; padding:16px; text-align:center; cursor:pointer; box-shadow:var(--shadow-sm); border:2px solid transparent;">
                        <div style="font-size:32px; margin-bottom:8px;">⚖️</div>
                        <div style="font-weight:bold;">الفقه</div>
                    </div>
                    <div class="exam-subject-card" data-subject="aqeeda" onclick="examWizard.selectSubject('aqeeda')" style="background:var(--surface); border-radius:12px; padding:16px; text-align:center; cursor:pointer; box-shadow:var(--shadow-sm); border:2px solid transparent;">
                        <div style="font-size:32px; margin-bottom:8px;">🕋</div>
                        <div style="font-weight:bold;">العقيدة</div>
                    </div>
                    <div class="exam-subject-card" data-subject="nahw" onclick="examWizard.selectSubject('nahw')" style="background:var(--surface); border-radius:12px; padding:16px; text-align:center; cursor:pointer; box-shadow:var(--shadow-sm); border:2px solid transparent;">
                        <div style="font-size:32px; margin-bottom:8px;">📝</div>
                        <div style="font-weight:bold;">النحو</div>
                    </div>
                    <div class="exam-subject-card" data-subject="tajweed" onclick="examWizard.selectSubject('tajweed')" style="background:var(--surface); border-radius:12px; padding:16px; text-align:center; cursor:pointer; box-shadow:var(--shadow-sm); border:2px solid transparent;">
                        <div style="font-size:32px; margin-bottom:8px;">📖</div>
                        <div style="font-weight:bold;">التجويد</div>
                    </div>
                </div>
            </div>

            <!-- STEP 2: MODE -->
            <div id="exam-step-2" style="display:none;">
                <h3 style="color:var(--text-2); margin-bottom:12px; font-size:16px;">2. اختر نمط الأسئلة</h3>
                <div id="exam-mode-cards" style="display:flex; flex-direction:column; gap:12px;">
                    <div class="exam-mode-card" onclick="examWizard.selectMode('lessons')" style="background:var(--surface); border-radius:12px; padding:16px; display:flex; align-items:center; cursor:pointer; box-shadow:var(--shadow-sm);">
                        <div style="font-size:24px; margin-left:16px; background:var(--primary-light); padding:10px; border-radius:12px;">📚</div>
                        <div>
                            <div style="font-weight:bold; font-size:16px; color:var(--text);">أسئلة الدروس</div>
                            <div style="font-size:12px; color:var(--text-3);">الأسئلة الرسمية الخاصة بكل درس</div>
                        </div>
                    </div>
                    <div class="exam-mode-card" onclick="examWizard.selectMode('themes')" style="background:var(--surface); border-radius:12px; padding:16px; display:flex; align-items:center; cursor:pointer; box-shadow:var(--shadow-sm);">
                        <div style="font-size:24px; margin-left:16px; background:#fef3c7; padding:10px; border-radius:12px;">🎯</div>
                        <div>
                            <div style="font-weight:bold; font-size:16px; color:var(--text);">أسئلة المحاور</div>
                            <div style="font-size:12px; color:var(--text-3);">تدريب شامل ومخصص حسب المحور</div>
                        </div>
                    </div>
                    <div class="exam-mode-card" id="exam-mode-years" onclick="examWizard.selectMode('years')" style="background:var(--surface); border-radius:12px; padding:16px; display:flex; align-items:center; cursor:pointer; box-shadow:var(--shadow-sm); display:none;">
                        <div style="font-size:24px; margin-left:16px; background:#dcfce7; padding:10px; border-radius:12px;">⏳</div>
                        <div>
                            <div style="font-weight:bold; font-size:16px; color:var(--text);">أسئلة السنوات</div>
                            <div style="font-size:12px; color:var(--text-3);">تدريب حسب السنة الهجرية (للسيرة فقط)</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- STEP 3: SELECTION & SETTINGS -->
            <div id="exam-step-3" style="display:none;">
                <h3 id="exam-step-3-title" style="color:var(--text-2); margin-bottom:12px; font-size:16px;">3. التحديد</h3>
                
                <div id="exam-selection-items" style="background:var(--surface); border-radius:12px; padding:8px 16px; max-height:300px; overflow-y:auto; box-shadow:var(--shadow-sm); margin-bottom:20px; display:flex; flex-direction:column; gap:12px;">
                    <!-- Checkboxes injected here -->
                </div>
                
                <h3 style="color:var(--text-2); margin-bottom:12px; font-size:16px;">عدد الأسئلة</h3>
                <input type="number" id="exam-limit-input" value="10" min="5" max="50" style="width:100%; padding:14px; border-radius:12px; border:1px solid var(--border-color); font-size:16px; margin-bottom:24px; text-align:center;">
                
                <button id="exam-start-btn" onclick="examWizard.startQuiz()" disabled style="background:var(--primary); color:white; border:none; padding:16px 32px; border-radius:12px; font-size:18px; font-weight:bold; width:100%; cursor:pointer; box-shadow: 0 4px 15px rgba(79,70,229,0.3); opacity:0.5; transition: opacity 0.3s;">🚀 بدء الامتحان</button>
            </div>
        </div>
    </div>
'''

content = content.replace('    <!-- TAB: PRACTICE -->', exam_tab + '\n    <!-- TAB: PRACTICE -->')

# 3. Add CSS for active subject
css = '''
    <style>
        .exam-subject-card.active { border-color: var(--primary) !important; background: var(--primary-light) !important; }
        .exam-selection-row { padding: 8px 0; border-bottom: 1px solid var(--border-color); }
        .exam-selection-row:last-child { border-bottom: none; }
    </style>
'''
content = content.replace('</head>', css + '\n</head>')

# 4. Include exam.js script
script = '<script src="exam.js?v=1"></script>'
content = content.replace('</body>', script + '\n</body>')

with open('dashboard/reader.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
