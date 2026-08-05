import sys

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Insert Magic Wand Button
toolbar_target = '''<button class="axes-toolbar-btn" onclick="window.moveSelectionToPrev()" title="'''
toolbar_replacement = '''<button class="axes-toolbar-btn" onclick="window.resyncFullscreenAxis()" title="استخراج النص تلقائياً بناءً على الكرونو" style="background:var(--primary); color:white; border-color:var(--primary);">🪄 جلب النص السحري</button>\n                    <button class="axes-toolbar-btn" onclick="window.moveSelectionToPrev()" title="'''
if toolbar_target in content:
    content = content.replace(toolbar_target, toolbar_replacement)
    print('Inserted Magic Wand Button')
else:
    print('Toolbar target not found')

# 2. Insert window.resyncFullscreenAxis function right before window.moveSelectionToPrev
func_target = '''window.moveSelectionToPrev = function() {'''
func_replacement = '''window.resyncFullscreenAxis = function() {
            if (!currentAxesEditing) return;
            const block = currentAxesEditing.blocks[activeAxisIdx];
            const startSec = block.start_seconds || 0;
            
            const sortedBlocks = [...currentAxesEditing.blocks].sort((a, b) => (a.start_seconds || 0) - (b.start_seconds || 0));
            const sortedIdx = sortedBlocks.findIndex(b => b === block);
            const endSec = sortedIdx + 1 < sortedBlocks.length ? (sortedBlocks[sortedIdx + 1].start_seconds || Infinity) : Infinity;
            
            const lesson = state.transcripts.find(l => l.subject === currentAxesEditing.subject && parseInt(l.lessonNum) === parseInt(currentAxesEditing.lessonNum));
            if (!lesson || !lesson.segments) return;

            const blockSegs = lesson.segments.filter(seg => (seg.sec || 0) >= startSec && (seg.sec || 0) < endSec);
            const newText = blockSegs.map(s => s.text).join('\\n');
            
            block.search_text = newText;
            const txtArea = document.getElementById('axis-transcription-editor');
            if (txtArea) txtArea.value = newText;
            
            window.updateLiveStudentPreview();
            showToast("🪄 تم جلب النص السحري بنجاح!", "success");
        };

        window.moveSelectionToPrev = function() {'''
if func_target in content:
    content = content.replace(func_target, func_replacement)
    print('Inserted resyncFullscreenAxis function')
else:
    print('func_target not found')

with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
    f.write(content)
