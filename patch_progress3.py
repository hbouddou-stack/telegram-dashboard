import re

def patch_progress3():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Remove the old progress bars
    html = re.sub(r'<!-- Reading Progress Bar glued to bottom of Sommaire -->.*?</div>\s*</div>', '</div>', html, flags=re.DOTALL)
    
    # 2. Add the robust bottom tracker right before the bottom-nav
    bottom_nav_match = re.search(r'(<nav class="bottom-nav">)', html)
    if bottom_nav_match:
        tracker_html = """
    <!-- Robust Reader Progress Tracker (Inspired by original dashboard) -->
    <div class="reader-progress-tracker" id="reader-progress-tracker" style="display: none; position: fixed; bottom: 62px; left: 0; width: 100%; z-index: 9998; background: var(--surface); border-top: 1px solid var(--border); padding: 12px 20px; direction: rtl; flex-direction: column; gap: 8px; box-shadow: 0 -4px 15px rgba(0,0,0,0.06); padding-bottom: calc(12px + env(safe-area-inset-bottom));">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 6px;">
                <span>📌</span>
                <span id="progress-tracker-title" style="font-weight: 800; color: var(--primary); font-size: 14px;">Titre</span>
            </div>
            <span id="progress-tracker-percent" style="color: var(--text-3); font-size: 11px; font-weight: bold;">0%</span>
        </div>
        <div class="progress-chapters-dots" id="progress-tracker-dots" style="display: flex; justify-content: space-between; align-items: center; position: relative; margin: 8px 0 4px 0; padding: 0 4px;">
            <div class="progress-line-bg" style="position: absolute; top: 50%; left: 0; right: 0; height: 4px; background: var(--bg); transform: translateY(-50%); border-radius: 2px;"></div>
            <div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 4px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: 0%; transition: width 0.1s;"></div>
            <!-- dots injected dynamically -->
        </div>
    </div>
    """
        html = html.replace(bottom_nav_match.group(1), tracker_html + bottom_nav_match.group(1))

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    # 3. Update JS
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    old_scroll_logic = re.search(r'// Reading Progress Bar Logic.*?function initUIControls', js, re.DOTALL)
    
    new_scroll_logic = """// Reading Progress Bar Logic
window.addEventListener('scroll', () => {
    updateReadingProgress();
});
window.addEventListener('touchmove', () => {
    updateReadingProgress();
});

function updateReadingProgress() {
    const tracker = document.getElementById('reader-progress-tracker');
    const tabReader = document.getElementById('tab-reader');
    
    if (tracker && tabReader.classList.contains('active') && thematicData && thematicData.length > 0) {
        tracker.style.display = 'flex';
        
        const scrollTop = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
        const scrollHeight = Math.max(
            document.documentElement.scrollHeight,
            document.body.scrollHeight
        ) - window.innerHeight;
        
        let scrollPercent = 0;
        if (scrollHeight > 0) {
            scrollPercent = (scrollTop / scrollHeight) * 100;
        } else {
            scrollPercent = 100; // If content is smaller than screen, it's 100% read!
        }
        
        document.getElementById('progress-tracker-percent').textContent = Math.round(Math.min(100, Math.max(0, scrollPercent))) + '%';
        
        // The fill bar width should represent the overall lesson progress
        // But since we use tabs, we can make the fill line connect up to the current tab
        // And use the scroll percent for the space between current and next tab!
        
        const numThemes = thematicData.length;
        const segmentPercent = 100 / Math.max(1, (numThemes - 1));
        
        let baseFill = currentTabIndex * segmentPercent;
        if (numThemes === 1) baseFill = scrollPercent;
        
        // Add partial progress for current chapter
        let totalFill = baseFill;
        if (numThemes > 1) {
            totalFill = baseFill + (scrollPercent / 100) * segmentPercent;
        }
        
        document.getElementById('progress-tracker-fill').style.width = Math.min(100, totalFill) + '%';
        
        if (thematicData[currentTabIndex]) {
            document.getElementById('progress-tracker-title').textContent = thematicData[currentTabIndex].title;
        }
        
        // Update dots UI
        let dotsHtml = '';
        for(let i = 0; i < numThemes; i++) {
            const isCompleted = currentLessonData ? !!syllabusCompletion[`${currentLessonData.subject}_${currentLessonData.lessonNum}_${i}`] : false;
            const isCurrent = (i === currentTabIndex);
            const isPast = (i < currentTabIndex);
            
            let color = 'var(--border)';
            if (isCompleted || isPast) color = 'var(--primary)';
            if (isCurrent) color = 'var(--accent-color)';
            
            const scale = isCurrent ? '1.4' : (isCompleted ? '1.1' : '1');
            const shadow = isCurrent ? '0 0 0 3px var(--surface), 0 0 8px var(--accent-color)' : '0 0 0 2px var(--surface)';
            
            dotsHtml += `<div onclick="switchThemeTab(${i}); window.scrollTo({top:0});" style="width: 12px; height: 12px; border-radius: 50%; background: ${color}; position: relative; z-index: 2; cursor: pointer; transform: scale(${scale}); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: ${shadow};"></div>`;
        }
        const dotsContainer = document.getElementById('progress-tracker-dots');
        // Small optimization to avoid rebuilding HTML on every scroll if the structure didn't change
        // For dots, the colors change based on current index, which only changes on switchThemeTab
        // So we can just set it:
        dotsContainer.innerHTML = `
            <div class="progress-line-bg" style="position: absolute; top: 50%; left: 0; right: 0; height: 4px; background: var(--border); transform: translateY(-50%); border-radius: 2px;"></div>
            <div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 4px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: ${Math.min(100, totalFill)}%; transition: width 0.1s ease-out;"></div>
            ${dotsHtml}
        `;
    } else {
        if(tracker) tracker.style.display = 'none';
    }
}

function initUIControls"""

    if old_scroll_logic:
        js = js.replace(old_scroll_logic.group(0), new_scroll_logic)
        
    # Also we need to call updateReadingProgress() in switchThemeTab to refresh it immediately!
    switch_tab_logic = re.search(r'function switchThemeTab\(index, shouldSeek = true\) \{([\s\S]*?)const contentDiv = document\.getElementById\(\'reader-content\'\);', js)
    if switch_tab_logic:
        js = js.replace(switch_tab_logic.group(0), switch_tab_logic.group(0) + "\n    setTimeout(() => updateReadingProgress(), 50);\n")
    
    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    print("Progress bar logic fully overhauled to match original dashboard.")

if __name__ == '__main__':
    patch_progress3()
