import sys

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: openAxesEditor
search1 = '''                    is_sub_theme: !!b.is_sub_theme,
                    explanation: b.explanation || '','''
replace1 = '''                    is_sub_theme: !!b.is_sub_theme,
                    reading_text: b.reading_text || '',
                    explanation: b.explanation || '','''
content = content.replace(search1, replace1)

# Fix 2: addNewAxis
search2 = '''                is_sub_theme: false,
                explanation: '','''
replace2 = '''                is_sub_theme: false,
                reading_text: '',
                explanation: '','''
content = content.replace(search2, replace2)

# Fix 3: splitAxisAtSelection
search3 = '''                is_sub_theme: false,
                explanation: '','''
replace3 = '''                is_sub_theme: false,
                reading_text: '',
                explanation: '','''
content = content.replace(search3, replace3)

# Fix 4: saveAxesChanges (modified & unmodified blocks)
search4 = '''                            is_sub_theme: !!block.is_sub_theme,
                            explanation: block.explanation,'''
replace4 = '''                            is_sub_theme: !!block.is_sub_theme,
                            reading_text: block.reading_text,
                            explanation: block.explanation,'''
content = content.replace(search4, replace4)

# Fix 5: loadActiveAxis Grid UI
search5 = '''                <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; flex: 1; min-height: 400px; margin-bottom: 20px;">
                    <!-- Left: Transcription Text -->
                    <div class="editor-card" style="flex: 1; display: flex; flex-direction: column; border-color: var(--primary);">
                        <div class="editor-card-title" style="color: var(--primary);">📝 نص التفريغ</div>
                        <textarea id="axis-transcription-editor" class="axes-textarea" style="flex: 1; min-height: 250px;" placeholder="اكتب نص التفريغ الحرفي الكامل هنا..." oninput="currentAxesEditing.blocks[activeAxisIdx].search_text = this.value; currentAxesEditing.blocks[activeAxisIdx]._isModified = true; window.updateLiveStudentPreview();">${escapeHtml(block.search_text || '')}</textarea>
                    </div>'''
replace5 = '''                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; flex: 1; min-height: 400px; margin-bottom: 20px;">
                    <!-- Left: Transcription Text -->
                    <div class="editor-card" style="flex: 1; display: flex; flex-direction: column; border-color: var(--primary);">
                        <div class="editor-card-title" style="color: var(--primary);">🎥 التفريغ الحرفي</div>
                        <textarea id="axis-transcription-editor" class="axes-textarea" style="flex: 1; min-height: 250px;" placeholder="اكتب نص التفريغ الحرفي الكامل هنا..." oninput="currentAxesEditing.blocks[activeAxisIdx].search_text = this.value; currentAxesEditing.blocks[activeAxisIdx]._isModified = true; window.updateLiveStudentPreview();">${escapeHtml(block.search_text || '')}</textarea>
                    </div>

                    <!-- Middle: Reading Mode Text -->
                    <div class="editor-card" style="flex: 1; display: flex; flex-direction: column; border-color: #10b981;">
                        <div class="editor-card-title" style="color: #10b981; display: flex; justify-content: space-between; align-items: center; padding-right: 4px;">
                           <span>📖 محتوى وضع القراءة</span>
                           <button onclick="window.copyTranscriptionToReading()" style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; color: #047857; border-radius: 6px; padding: 2px 8px; font-size: 0.8rem; cursor: pointer; white-space: nowrap;">استنساخ التفريغ 👇</button>
                        </div>
                        <textarea id="axis-reading-editor" class="axes-textarea" style="flex: 1; min-height: 250px;" placeholder="اكتب النص المنظم والمنسق لوضع القراءة هنا... (إذا تركته فارغاً سيتم استخدام التفريغ الحرفي)" oninput="currentAxesEditing.blocks[activeAxisIdx].reading_text = this.value; currentAxesEditing.blocks[activeAxisIdx]._isModified = true; window.updateLiveStudentPreview();">${escapeHtml(block.reading_text || '')}</textarea>
                    </div>'''
content = content.replace(search5, replace5)

# Fix 6: Live Student Preview to prioritize reading_text
search6 = '''            const escapedSearchText = escapeHtml(block.search_text || 'لا يوجد نص تفريغ لهذا المحور...');'''
replace6 = '''            const actualReadingText = (block.reading_text && block.reading_text.trim() !== '') ? block.reading_text : block.search_text;
            const escapedSearchText = escapeHtml(actualReadingText || 'لا يوجد نص تفريغ لهذا المحور...');'''
content = content.replace(search6, replace6)

# Fix 7: Add copy function
search7 = '''        window.updateLiveStudentPreview = function() {'''
replace7 = '''        window.copyTranscriptionToReading = function() {
            if (!currentAxesEditing) return;
            const block = currentAxesEditing.blocks[activeAxisIdx];
            if (block.reading_text && block.reading_text.trim() !== '' && !confirm("⚠️ وضع القراءة يحتوي على نص بالفعل، هل تريد استبداله بنص التفريغ؟")) return;
            block.reading_text = block.search_text;
            block._isModified = true;
            document.getElementById('axis-reading-editor').value = block.search_text || '';
            window.updateLiveStudentPreview();
            showToast("✅ تم استنساخ نص التفريغ إلى وضع القراءة", "success");
        };

        window.updateLiveStudentPreview = function() {'''
content = content.replace(search7, replace7)

with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
    f.write(content)
