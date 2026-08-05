import re

html_path = 'dashboard/reader.html'
js_path = 'dashboard/reader.js'

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# --- 1. Toggle Button -> Segmented Control ---
old_toggle = r'<button class="control-btn" id="btn-reading-mode-toggle".*?>.*?📖 قراءة.*?</button>'
new_segmented = '''
<div class="segmented-control" style="display: flex; background: var(--surface-2, rgba(0,0,0,0.1)); border-radius: 8px; padding: 2px; border: 1px solid var(--border-color); margin-right: 4px;">
    <button class="control-btn segment-btn" id="btn-seg-video" style="border-radius: 6px; padding: 2px 10px; font-size: 0.85rem; font-weight: bold; border: none; background: transparent; color: var(--text-secondary); cursor: pointer; transition: all 0.2s;">🎥 فيديو</button>
    <button class="control-btn segment-btn active" id="btn-seg-reading" style="border-radius: 6px; padding: 2px 10px; font-size: 0.85rem; font-weight: bold; border: none; background: var(--primary); color: white; cursor: pointer; transition: all 0.2s;">📖 قراءة</button>
</div>
'''
html = re.sub(old_toggle, new_segmented, html, flags=re.DOTALL)

# Update JS logic for the segmented control
js_old_toggle_logic = r'''    const btnReadingMode = document\.getElementById\('btn-reading-mode-toggle'\);
    if \(btnReadingMode\) \{
        btnReadingMode\.addEventListener\('click', \(\) => \{
            isReadingMode = !isReadingMode;
            btnReadingMode\.style\.background = isReadingMode \? 'var\(--primary\)' : 'var\(--surface\)';
            btnReadingMode\.style\.color = isReadingMode \? 'white' : 'var\(--primary\)';
            btnReadingMode\.textContent = isReadingMode \? '🎥 فيديو' : '📖 قراءة';
            
            if \(currentLessonData\) \{
                prepareThematicData\(currentLessonData\);
                renderTabs\(\);
                switchThemeTab\(currentTabIndex, !isReadingMode\);
            \}
        \}\);
    \}'''

js_new_segmented_logic = '''
    const btnSegVideo = document.getElementById('btn-seg-video');
    const btnSegReading = document.getElementById('btn-seg-reading');
    
    function updateSegmentUI() {
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
            if (currentLessonData) {
                prepareThematicData(currentLessonData);
                renderTabs();
                switchThemeTab(currentTabIndex, !isReadingMode);
            }
        });
        
        btnSegReading.addEventListener('click', () => {
            if (isReadingMode) return;
            isReadingMode = true;
            updateSegmentUI();
            if (currentLessonData) {
                prepareThematicData(currentLessonData);
                renderTabs();
                switchThemeTab(currentTabIndex, !isReadingMode);
            }
        });
        
        // Initialize
        updateSegmentUI();
    }
'''
js = re.sub(js_old_toggle_logic, js_new_segmented_logic, js)

# Fix the duplicate logic when isReadingMode changes in switchThemeTab (if any)
js = re.sub(r'btnReadingMode\.textContent = .*?;', 'if(typeof updateSegmentUI==="function") updateSegmentUI();', js)

# --- 2. Map Button -> Icon ---
old_map = r'<button class="control-btn" style="font-weight:bold; background: var\(--surface\);" onclick="openMindMap\(\)">\s*خريطة\s*</button>'
new_map = r'<button class="control-btn font-control-btn" title="خريطة المنهج" onclick="openMindMap()">🗺️</button>'
html = re.sub(old_map, new_map, html)

# --- 3. Sticky Header Video Play Issue ---
# Remove the problematic DOMContentLoaded block entirely
bad_sticky_logic = r'''document\.addEventListener\('DOMContentLoaded', \(\) => \{\s*const stickyToggleBtn = document\.getElementById\('btn-sticky-toggle'\);\s*const stickyContainer = document\.getElementById\('sticky-header-container'\);\s*const videoWrapper = document\.getElementById\('video-wrapper'\);\s*if \(stickyToggleBtn && stickyContainer && videoWrapper\) \{\s*stickyToggleBtn\.addEventListener\('click', \(\) => \{\s*if \(videoWrapper\.style\.display === 'none'\) \{.*?\}\);\s*\}\s*\}\);'''
js = re.sub(bad_sticky_logic, '', js, flags=re.DOTALL)


# --- 4. Vertical Progress Bar ---
# Add HTML for the vertical bar
vertical_bar_html = '''
    <!-- Vertical Scroll Progress Bar -->
    <div id="vertical-scroll-progress-container" style="position: fixed; top: 0; right: 0; width: 4px; height: 100vh; background: transparent; z-index: 9999; pointer-events: none; display: none;">
        <div id="vertical-scroll-progress-fill" style="width: 100%; height: 0%; background: var(--primary); transition: height 0.1s ease-out;"></div>
    </div>
'''
if 'vertical-scroll-progress-container' not in html:
    html = html.replace('<body', vertical_bar_html + '\n<body')

# Add JS logic for the vertical progress bar
vertical_bar_js = '''
// Vertical Scroll Progress Logic
window.addEventListener('scroll', () => {
    const vContainer = document.getElementById('vertical-scroll-progress-container');
    const vFill = document.getElementById('vertical-scroll-progress-fill');
    
    if (vContainer && vFill) {
        if (typeof isReadingMode !== 'undefined' && isReadingMode) {
            vContainer.style.display = 'block';
            const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            vFill.style.height = scrolled + "%";
        } else {
            vContainer.style.display = 'none';
        }
    }
});
'''
if 'Vertical Scroll Progress Logic' not in js:
    js += '\n' + vertical_bar_js


with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("UX patching complete.")
