import re

js_path = 'dashboard/reader.js'

with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Ensure `let isReadingMode = false;` exists at the top.
if 'let isReadingMode' not in js and 'var isReadingMode' not in js:
    js = 'let isReadingMode = false;\n' + js

# 2. Add the segmented control logic at the bottom of the file inside a DOMContentLoaded block
# because the regex failed earlier.
segment_logic = '''
// Segmented Control Logic for Reading/Video Mode
document.addEventListener('DOMContentLoaded', () => {
    const btnSegVideo = document.getElementById('btn-seg-video');
    const btnSegReading = document.getElementById('btn-seg-reading');
    
    window.updateSegmentUI = function() {
        if (typeof isReadingMode === 'undefined') return;
        
        if (btnSegReading && btnSegVideo) {
            if (isReadingMode) {
                btnSegReading.style.background = 'var(--primary)';
                btnSegReading.style.color = 'white';
                btnSegVideo.style.background = 'transparent';
                btnSegVideo.style.color = 'var(--text-secondary)';
            } else {
                btnSegVideo.style.background = 'var(--primary)';
                btnSegVideo.style.color = 'white';
                btnSegReading.style.background = 'transparent';
                btnSegReading.style.color = 'var(--text-secondary)';
            }
        }
        
        // Hide/Show Sticky Pin and Video Speed
        const btnSticky = document.getElementById('btn-sticky-toggle');
        const btnSpeed = document.getElementById('btn-speed-toggle');
        const progTracker = document.getElementById('progress-tracker-dots');
        
        if (btnSticky) btnSticky.style.display = isReadingMode ? 'none' : 'inline-block';
        if (btnSpeed) btnSpeed.style.display = isReadingMode ? 'none' : 'inline-block';
        if (progTracker) progTracker.style.visibility = isReadingMode ? 'hidden' : 'visible'; // Keep space but hide dots
    }
    
    if (btnSegVideo && btnSegReading) {
        btnSegVideo.addEventListener('click', () => {
            if (!isReadingMode) return;
            isReadingMode = false;
            updateSegmentUI();
            if (typeof currentLessonData !== 'undefined' && currentLessonData) {
                prepareThematicData(currentLessonData);
                renderTabs();
                switchThemeTab(typeof currentTabIndex !== 'undefined' ? currentTabIndex : 0, !isReadingMode);
            }
        });
        
        btnSegReading.addEventListener('click', () => {
            if (isReadingMode) return;
            isReadingMode = true;
            updateSegmentUI();
            if (typeof currentLessonData !== 'undefined' && currentLessonData) {
                prepareThematicData(currentLessonData);
                renderTabs();
                switchThemeTab(typeof currentTabIndex !== 'undefined' ? currentTabIndex : 0, !isReadingMode);
            }
        });
        
        // Initialize
        updateSegmentUI();
    }
});
'''

if 'btnSegVideo.addEventListener' not in js:
    js += '\n' + segment_logic

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Reader JS Fixed.")
