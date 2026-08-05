import sys

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update loadActiveAxis to flag _isModified
target_oninput = '''                txtArea.oninput = function() {
                    block.search_text = txtArea.value;
                    window.updateLiveStudentPreview();
                };'''
replacement_oninput = '''                txtArea.oninput = function() {
                    block.search_text = txtArea.value;
                    block._isModified = true;
                    window.updateLiveStudentPreview();
                };'''

if target_oninput in content:
    content = content.replace(target_oninput, replacement_oninput)
    print("Replaced oninput")

# 2. Update Magic Wand to flag _isModified
target_magic = '''            block.search_text = newText;
            const txtArea = document.getElementById('axis-transcription-editor');'''
replacement_magic = '''            block.search_text = newText;
            block._isModified = true;
            const txtArea = document.getElementById('axis-transcription-editor');'''

if target_magic in content:
    content = content.replace(target_magic, replacement_magic)
    print("Replaced magic wand")

# 3. Rewrite saveAxesChanges
target_save = '''            currentAxesEditing.blocks.sort((a, b) => (a.start_seconds || 0) - (b.start_seconds || 0));

            const lesson = state.transcripts.find(l => l.subject === currentAxesEditing.subject && parseInt(l.lessonNum) === parseInt(currentAxesEditing.lessonNum));
            let cleanedSegments = [];
            
            if (lesson) {
                const newSegments = [];
                currentAxesEditing.blocks.forEach((block, bIdx) => {
                    const isSira = currentAxesEditing.subject.includes('sira');
                    const sentences = isSira ? (block.search_text || '').split('\\n') : smartSplitSentences(block.search_text || '');
                    const firstSec = block.start_seconds || 0;
                    const nextBlock = currentAxesEditing.blocks[bIdx + 1];
                    const lastSec = nextBlock ? (nextBlock.start_seconds || Infinity) : Infinity;
                    
                    const count = Math.max(sentences.length, 1);
                    let secSpan = count * 4;
                    if (lastSec !== Infinity) {
                        secSpan = Math.max(lastSec - firstSec, count * 4);
                    }

                    sentences.forEach((sentence, i) => {
                        if (!sentence.trim()) return;
                        const secOffset = Math.round((i / count) * secSpan);
                        const sec = firstSec + secOffset;
                        newSegments.push({
                            ts: secToTs(sec),
                            sec: sec,
                            text: sentence.trim(),
                            video_link: block.video_link ? rebuildVideoLink(block.video_link, sec) : ''
                        });
                    });
                });

                cleanedSegments = newSegments.filter(s => (s.text || '').trim() !== '').sort((a, b) => a.sec - b.sec);
            }

            try {
                console.log('[SAVE] Sending payload to /admin/save-full-transcript...');
                const res = await fetch('/admin/save-full-transcript', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        userId: state.userId,
                        subject: currentAxesEditing.subject,
                        lessonNum: currentAxesEditing.lessonNum,
                        segments: cleanedSegments.length > 0 ? cleanedSegments : (lesson ? lesson.segments : []),
                        thematicBlocks: currentAxesEditing.blocks
                    })
                });'''

replacement_save = '''            currentAxesEditing.blocks.sort((a, b) => (a.start_seconds || 0) - (b.start_seconds || 0));

            const lesson = state.transcripts.find(l => l.subject === currentAxesEditing.subject && parseInt(l.lessonNum) === parseInt(currentAxesEditing.lessonNum));
            
            let finalSegments = lesson ? JSON.parse(JSON.stringify(lesson.segments || [])) : [];
            let segmentsChanged = false;

            if (lesson) {
                currentAxesEditing.blocks.forEach((block, bIdx) => {
                    if (block._isModified) {
                        segmentsChanged = true;
                        const firstSec = block.start_seconds || 0;
                        const nextBlock = currentAxesEditing.blocks[bIdx + 1];
                        const lastSec = nextBlock ? (nextBlock.start_seconds || Infinity) : Infinity;

                        // Remove ALL existing segments in this block's time window
                        finalSegments = finalSegments.filter(s => s.sec < firstSec || s.sec >= lastSec);

                        const isSira = currentAxesEditing.subject.includes('sira');
                        const sentences = isSira ? (block.search_text || '').split('\\n') : smartSplitSentences(block.search_text || '');
                        
                        const count = Math.max(sentences.length, 1);
                        let secSpan = count * 4;
                        if (lastSec !== Infinity) {
                            secSpan = Math.max(lastSec - firstSec, count * 4);
                        }

                        sentences.forEach((sentence, i) => {
                            if (!sentence.trim()) return;
                            const secOffset = Math.round((i / count) * secSpan);
                            const sec = firstSec + secOffset;
                            finalSegments.push({
                                ts: secToTs(sec),
                                sec: sec,
                                text: sentence.trim(),
                                video_link: block.video_link ? rebuildVideoLink(block.video_link, sec) : ''
                            });
                        });
                    }
                });

                if (segmentsChanged) {
                    finalSegments = finalSegments.filter(s => (s.text || '').trim() !== '').sort((a, b) => a.sec - b.sec);
                }
            }

            try {
                console.log('[SAVE] Sending payload to /admin/save-full-transcript...');
                const res = await fetch('/admin/save-full-transcript', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        userId: state.userId,
                        subject: currentAxesEditing.subject,
                        lessonNum: currentAxesEditing.lessonNum,
                        segments: finalSegments,
                        thematicBlocks: currentAxesEditing.blocks
                    })
                });'''

if target_save in content:
    content = content.replace(target_save, replacement_save)
    print("Replaced save logic")
else:
    print("TARGET SAVE NOT FOUND")

with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
    f.write(content)
