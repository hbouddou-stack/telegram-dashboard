import sys

with open('dashboard/admin.js', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''            try {
                const payload = {
                    userId: state.userId,
                    subject: currentAxesEditing.subject,
                    lessonNum: currentAxesEditing.lessonNum,
                    thematicBlocks: currentAxesEditing.blocks
                };
                console.log('[SAVE] Sending payload to /admin/save-thematic-blocks...');
                const res = await fetch('/admin/save-thematic-blocks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });'''

replacement = '''            currentAxesEditing.blocks.sort((a, b) => (a.start_seconds || 0) - (b.start_seconds || 0));

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

if target in content:
    content = content.replace(target, replacement)
    with open('dashboard/admin.js', 'w', encoding='utf-8') as f:
        f.write(content)
    print('REPLACED SUCCESSFULLY')
else:
    print('TARGET NOT FOUND')
