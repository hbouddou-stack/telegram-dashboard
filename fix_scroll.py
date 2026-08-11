import re

def fix_scroll_progress():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Restore scroll event listener for progress bar
    if "window.addEventListener('scroll', () => { updateDashboardProgress(); }" not in js:
        js += "\nwindow.addEventListener('scroll', () => { updateDashboardProgress(); }, { passive: true, capture: true });\n"
        js += "window.addEventListener('touchmove', () => { updateDashboardProgress(); }, { passive: true });\n"

    # Revert updateDashboardProgress to use scroll position for the inner fraction
    old_func = """function updateDashboardProgress() {
    if (!thematicData || thematicData.length === 0 || !player || !player.getCurrentTime) return;
    
    const numThemes = thematicData.length;
    if (numThemes > 0) {
        let activeIdx = currentTabIndex;
        const segmentPercent = 100 / Math.max(1, (numThemes - 1));
        
        // Calculate progress within current chapter
        let chapterProgress = 0;
        let currentTime = player.getCurrentTime();
        let currentTab = thematicData[activeIdx];
        if (currentTab) {
            let duration = currentTab.endTime - currentTab.startTime;
            if (duration > 0) {
                chapterProgress = (currentTime - currentTab.startTime) / duration;
                chapterProgress = Math.max(0, Math.min(1, chapterProgress));
            }
        }
        
        let baseFill = activeIdx * segmentPercent;
        if (numThemes === 1) baseFill = chapterProgress * 100;
        
        let totalFill = baseFill;
        if (numThemes > 1) {
            totalFill = baseFill + (chapterProgress * segmentPercent);
        }"""

    new_func = """function updateDashboardProgress() {
    if (!thematicData || thematicData.length === 0) return;
    
    // Get scroll position for the fraction
    let scrollTop = document.documentElement.scrollTop || window.scrollY || 0;
    let scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    let scrollPercent = 0;
    if (scrollHeight > 0) {
        scrollPercent = (scrollTop / scrollHeight) * 100;
        scrollPercent = Math.max(0, Math.min(100, scrollPercent));
    }

    const numThemes = thematicData.length;
    if (numThemes > 0) {
        let activeIdx = currentTabIndex;
        const segmentPercent = 100 / Math.max(1, (numThemes - 1));
        
        let baseFill = activeIdx * segmentPercent;
        if (numThemes === 1) baseFill = scrollPercent;
        
        let totalFill = baseFill;
        if (numThemes > 1) {
            // Fraction based on global scroll position!
            totalFill = baseFill + (scrollPercent / 100) * segmentPercent;
        }"""

    if old_func in js:
        js = js.replace(old_func, new_func)
    else:
        print("Warning: old updateDashboardProgress not found")

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        
    print("Execution complete for scroll fix")

if __name__ == '__main__':
    fix_scroll_progress()
