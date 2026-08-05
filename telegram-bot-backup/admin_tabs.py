import sys

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    content = f.read()

search = '''                <!-- Helper Toolbar -->
                <div class="axes-toolbar">
                    <span class="axes-toolbar-title">🛠️ أدوات تحديد ونقل نص التفريغ:</span>
                    <button class="axes-toolbar-btn" onclick="window.resyncFullscreenAxis()" title="استخراج النص تلقائياً بناءً على الكرونو" style="background:var(--primary); color:white; border-color:var(--primary);">🪄 جلب النص السحري</button>
                    <button class="axes-toolbar-btn" onclick="window.moveSelectionToPrev()" title="نقل النص المحدد إلى نهاية المحور السابق">➡️ السابق</button>
                    <button class="axes-toolbar-btn" onclick="window.moveSelectionToNext()" title="نقل النص المحدد إلى بداية المحور التالي">⬅️ التالي</button>
                    <button class="axes-toolbar-btn" onclick="window.splitAxisAtSelection()" title="تقسيم المحور عند تحديد النص أو موقع المؤشر">✂️ تقسيم المحور</button>
                    <button class="axes-toolbar-btn" onclick="window.wrapSelectionInPoetry()" title="تغليف النص المحدد بعلامات الشعر">📜 وسم كشعر</button>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; flex: 1; min-height: 400px; margin-bottom: 20px;">
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
                    </div>

                    <!-- Right: Explanation + Poetry stacked -->'''

replace = '''                <!-- TABS -->
                <div style="display: flex; gap: 10px; margin-bottom: 15px; border-bottom: 2px solid rgba(212, 175, 55, 0.2); padding-bottom: 10px;">
                    <button class="btn btn-primary" id="tab-btn-video" onclick="window.switchEditorTab('video')" style="background: var(--primary); color: white;">🎥 تحرير التفريغ (Karaoké)</button>
                    <button class="btn" id="tab-btn-reading" onclick="window.switchEditorTab('reading')" style="background: transparent; border: 1px solid var(--primary); color: var(--text-color);">📖 تحرير وضع القراءة (Lecture)</button>
                </div>

                <!-- Helper Toolbar (Video mode only) -->
                <div id="axes-video-toolbar" class="axes-toolbar">
                    <span class="axes-toolbar-title">🛠️ أدوات تحديد ونقل نص التفريغ:</span>
                    <button class="axes-toolbar-btn" onclick="window.resyncFullscreenAxis()" title="استخراج النص تلقائياً بناءً على الكرونو" style="background:var(--primary); color:white; border-color:var(--primary);">🪄 جلب النص السحري</button>
                    <button class="axes-toolbar-btn" onclick="window.moveSelectionToPrev()" title="نقل النص المحدد إلى نهاية المحور السابق">➡️ السابق</button>
                    <button class="axes-toolbar-btn" onclick="window.moveSelectionToNext()" title="نقل النص المحدد إلى بداية المحور التالي">⬅️ التالي</button>
                    <button class="axes-toolbar-btn" onclick="window.splitAxisAtSelection()" title="تقسيم المحور عند تحديد النص أو موقع المؤشر">✂️ تقسيم المحور</button>
                    <button class="axes-toolbar-btn" onclick="window.wrapSelectionInPoetry()" title="تغليف النص المحدد بعلامات الشعر">📜 وسم كشعر</button>
                </div>

                <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; flex: 1; min-height: 400px; margin-bottom: 20px;">
                    
                    <!-- Left Column: Switches between Video and Reading -->
                    <div style="display: flex; flex-direction: column; flex: 1;">
                        
                        <!-- TAB CONTENT: VIDEO -->
                        <div id="editor-tab-video" class="editor-card" style="flex: 1; display: flex; flex-direction: column; border-color: var(--primary); margin-bottom: 0;">
                            <div class="editor-card-title" style="color: var(--primary);">🎥 التفريغ الحرفي للفيديو</div>
                            <textarea id="axis-transcription-editor" class="axes-textarea" style="flex: 1; min-height: 250px;" placeholder="اكتب نص التفريغ الحرفي الكامل هنا..." oninput="currentAxesEditing.blocks[activeAxisIdx].search_text = this.value; currentAxesEditing.blocks[activeAxisIdx]._isModified = true; window.updateLiveStudentPreview();">${escapeHtml(block.search_text || '')}</textarea>
                        </div>

                        <!-- TAB CONTENT: READING -->
                        <div id="editor-tab-reading" class="editor-card" style="flex: 1; display: none; flex-direction: column; border-color: #10b981; margin-bottom: 0;">
                            <div class="editor-card-title" style="color: #10b981; display: flex; justify-content: space-between; align-items: center; padding-right: 4px;">
                            <span>📖 محتوى وضع القراءة</span>
                            <button onclick="window.copyTranscriptionToReading()" style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; color: #047857; border-radius: 6px; padding: 2px 8px; font-size: 0.8rem; cursor: pointer; white-space: nowrap;">استنساخ التفريغ 👇</button>
                            </div>
                            <textarea id="axis-reading-editor" class="axes-textarea" style="flex: 1; min-height: 250px;" placeholder="اكتب النص المنظم والمنسق لوضع القراءة هنا... (إذا تركته فارغاً سيتم استخدام التفريغ الحرفي)" oninput="currentAxesEditing.blocks[activeAxisIdx].reading_text = this.value; currentAxesEditing.blocks[activeAxisIdx]._isModified = true; window.updateLiveStudentPreview();">${escapeHtml(block.reading_text || '')}</textarea>
                        </div>
                    </div>

                    <!-- Right: Explanation + Poetry stacked -->'''

content = content.replace(search, replace)

search2 = '''        window.copyTranscriptionToReading = function() {'''
replace2 = '''        window.switchEditorTab = function(tabName) {
            const btnVideo = document.getElementById('tab-btn-video');
            const btnReading = document.getElementById('tab-btn-reading');
            const tabVideo = document.getElementById('editor-tab-video');
            const tabReading = document.getElementById('editor-tab-reading');
            const toolbar = document.getElementById('axes-video-toolbar');
            
            if (!btnVideo || !btnReading) return;
            
            if (tabName === 'video') {
                btnVideo.style.background = 'var(--primary)';
                btnVideo.style.color = 'white';
                btnReading.style.background = 'transparent';
                btnReading.style.color = 'var(--text-color)';
                tabVideo.style.display = 'flex';
                tabReading.style.display = 'none';
                toolbar.style.display = 'flex';
            } else {
                btnReading.style.background = 'var(--primary)';
                btnReading.style.color = 'white';
                btnVideo.style.background = 'transparent';
                btnVideo.style.color = 'var(--text-color)';
                tabReading.style.display = 'flex';
                tabVideo.style.display = 'none';
                toolbar.style.display = 'none';
            }
        };

        window.copyTranscriptionToReading = function() {'''

content = content.replace(search2, replace2)

with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
    f.write(content)
