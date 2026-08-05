import sys

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: openAxesEditor
search1 = '''                    title: b.title || '',
                    explanation: b.explanation || '','''
replace1 = '''                    title: b.title || '',
                    is_sub_theme: !!b.is_sub_theme,
                    explanation: b.explanation || '','''
content = content.replace(search1, replace1)

# Fix 2: addNewAxis
search2 = '''                title: 'محور جديد',
                explanation: '','''
replace2 = '''                title: 'محور جديد',
                is_sub_theme: false,
                explanation: '','''
content = content.replace(search2, replace2)

# Fix 3: splitAxisAtSelection
search3 = '''                title: `${currentAxesEditing.blocks[activeAxisIdx].title || 'المحور'} (تابع)`,
                explanation: '','''
replace3 = '''                title: `${currentAxesEditing.blocks[activeAxisIdx].title || 'المحور'} (تابع)`,
                is_sub_theme: false,
                explanation: '','''
content = content.replace(search3, replace3)

# Fix 4: saveAxesChanges (modified blocks)
search4 = '''                        const finalBlock = {
                            title: block.title,
                            explanation: block.explanation,'''
replace4 = '''                        const finalBlock = {
                            title: block.title,
                            is_sub_theme: !!block.is_sub_theme,
                            explanation: block.explanation,'''
content = content.replace(search4, replace4)

# Fix 5: saveAxesChanges (unmodified blocks)
search5 = '''                        finalBlocksToSave.push({
                            title: block.title,
                            explanation: block.explanation,'''
replace5 = '''                        finalBlocksToSave.push({
                            title: block.title,
                            is_sub_theme: !!block.is_sub_theme,
                            explanation: block.explanation,'''
content = content.replace(search5, replace5)

# Fix 6: loadActiveAxis UI
search6 = '''                        <div class="editor-card-title">📌 عنوان المحور</div>
                        <input type="text" class="axes-input" value="${escapeHtml(block.title)}" placeholder="اكتب عنوان المحور هنا..." oninput="currentAxesEditing.blocks[activeAxisIdx].title = this.value; window.updateAxisSidebarTitle(activeAxisIdx); window.updateLiveStudentPreview();">
                    </div>'''
replace6 = '''                        <div class="editor-card-title">📌 عنوان المحور</div>
                        <input type="text" class="axes-input" value="${escapeHtml(block.title)}" placeholder="اكتب عنوان المحور هنا..." oninput="currentAxesEditing.blocks[activeAxisIdx].title = this.value; window.updateAxisSidebarTitle(activeAxisIdx); window.updateLiveStudentPreview();">
                        <label style="display: flex; align-items: center; gap: 8px; margin-top: 10px; cursor: pointer; font-weight: bold; color: var(--text-secondary);">
                            <input type="checkbox" onchange="currentAxesEditing.blocks[activeAxisIdx].is_sub_theme = this.checked;" ${block.is_sub_theme ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer; accent-color: var(--primary);">
                            <span>هذا المحور هو محور فرعي (Sous-thématique)</span>
                        </label>
                    </div>'''
content = content.replace(search6, replace6)

with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
    f.write(content)
