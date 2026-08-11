import re

def update_js_ui():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Update updateScrollProgress()
    old_func = """function updateScrollProgress() {
    if (!thematicData || thematicData.length === 0) return;
    const tracker = document.getElementById('reader-progress-tracker');
    if (!tracker) return;
    
    // Only show if video is sticky or scrolled down
    const videoWrap = document.getElementById('video-wrapper');
    const isSticky = videoWrap && window.scrollY > (videoWrap.offsetTop || 0);
    tracker.style.display = isSticky ? 'flex' : 'none';

    if (isSticky) {
        let scrollPercent = 0;
        const currentTabId = `karaoke-tab-${currentTabIndex}`;
        const tabEl = document.getElementById(currentTabId);
        if (tabEl) {
             const scrollTop = window.scrollY || document.documentElement.scrollTop;
             const windowHeight = window.innerHeight;
             const docHeight = document.documentElement.scrollHeight;
             
             // Approximate overall progress through the document
             scrollPercent = (scrollTop / (docHeight - windowHeight)) * 100;
        }
        
        document.getElementById('progress-tracker-percent').textContent = Math.round(Math.min(100, Math.max(0, scrollPercent))) + '%';
        
        // Render Dots
        if (thematicData[currentTabIndex]) {
            document.getElementById('progress-tracker-title').textContent = thematicData[currentTabIndex].title;
            
            const totalTabs = thematicData.length;
            const currentTab = currentTabIndex;
            
            const dotsContainer = document.getElementById('progress-tracker-dots');
            if (dotsContainer.getAttribute('data-rendered') !== 'true') {
                let dotsHtml = '';
                for (let i = 0; i < totalTabs; i++) {
                    // Position dots evenly
                    const pos = (i / (totalTabs > 1 ? totalTabs - 1 : 1)) * 100;
                    dotsHtml += `<div class="progress-chapter-dot" data-index="${i}" style="position: absolute; right: ${pos}%; transform: translateX(50%); width: 8px; height: 8px; border-radius: 50%; background: var(--border-color); z-index: 2; transition: background 0.3s ease;"></div>`;
                }
                
                // Add fill line
                const fillWidth = (currentTab / (totalTabs > 1 ? totalTabs - 1 : 1)) * 100;
                // Add tiny extra width for the current playing portion
                const currentTabProgress = (scrollPercent / 100) * (100 / (totalTabs > 1 ? totalTabs - 1 : 1));
                const totalFill = fillWidth + currentTabProgress;
                
                dotsHtml += `<div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 4px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: ${Math.min(100, totalFill)}%; transition: width 0.1s ease-out;"></div>`;
                
                dotsContainer.innerHTML = dotsHtml;
                dotsContainer.setAttribute('data-rendered', 'true');
            } else {
                const fillEl = document.getElementById('progress-tracker-fill');
                if (fillEl) {
                    const fillWidth = (currentTab / (totalTabs > 1 ? totalTabs - 1 : 1)) * 100;
                    const currentTabProgress = (scrollPercent / 100) * (100 / (totalTabs > 1 ? totalTabs - 1 : 1));
                    const totalFill = fillWidth + currentTabProgress;
                    fillEl.style.width = Math.min(100, totalFill) + '%';
                }
            }
            
            // Colorize dots
            const dots = dotsContainer.querySelectorAll('.progress-chapter-dot');
            dots.forEach((dot, idx) => {
                if (idx <= currentTab) {
                    dot.style.background = 'var(--primary)';
                    dot.style.boxShadow = '0 0 0 2px var(--surface)';
                } else {
                    dot.style.background = 'var(--border-color)';
                    dot.style.boxShadow = 'none';
                }
            });
        }
    }
}"""

    new_func = """function updateScrollProgress() {
    if (!thematicData || thematicData.length === 0) return;
    
    let scrollPercent = 0;
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const windowHeight = window.innerHeight;
    const docHeight = document.documentElement.scrollHeight;
    
    if (docHeight > windowHeight) {
        scrollPercent = (scrollTop / (docHeight - windowHeight)) * 100;
    }
    
    // Render Dots in the Sommaire wrapper
    if (thematicData[currentTabIndex]) {
        const titleEl = document.getElementById('current-theme-label');
        if (titleEl) titleEl.textContent = thematicData[currentTabIndex].title;
        
        const totalTabs = thematicData.length;
        const currentTab = currentTabIndex;
        
        const dotsContainer = document.getElementById('progress-tracker-dots');
        if (dotsContainer) {
            if (dotsContainer.getAttribute('data-rendered') !== 'true') {
                let dotsHtml = '';
                for (let i = 0; i < totalTabs; i++) {
                    const pos = (i / (totalTabs > 1 ? totalTabs - 1 : 1)) * 100;
                    dotsHtml += `<div class="progress-chapter-dot" data-index="${i}" onclick="switchThemeTab(${i}, true)" style="position: absolute; right: ${pos}%; transform: translateX(50%); width: 10px; height: 10px; border-radius: 50%; background: var(--border-color); z-index: 2; transition: background 0.3s ease; cursor: pointer;"></div>`;
                }
                
                const fillWidth = (currentTab / (totalTabs > 1 ? totalTabs - 1 : 1)) * 100;
                const currentTabProgress = (scrollPercent / 100) * (100 / (totalTabs > 1 ? totalTabs - 1 : 1));
                const totalFill = fillWidth + currentTabProgress;
                
                dotsHtml += `<div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 3px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: ${Math.min(100, totalFill)}%; transition: width 0.1s ease-out;"></div>`;
                
                dotsContainer.innerHTML = dotsHtml;
                dotsContainer.setAttribute('data-rendered', 'true');
            } else {
                const fillEl = document.getElementById('progress-tracker-fill');
                if (fillEl) {
                    const fillWidth = (currentTab / (totalTabs > 1 ? totalTabs - 1 : 1)) * 100;
                    const currentTabProgress = (scrollPercent / 100) * (100 / (totalTabs > 1 ? totalTabs - 1 : 1));
                    const totalFill = fillWidth + currentTabProgress;
                    fillEl.style.width = Math.min(100, totalFill) + '%';
                }
            }
            
            // Colorize dots
            const dots = dotsContainer.querySelectorAll('.progress-chapter-dot');
            dots.forEach((dot, idx) => {
                if (idx <= currentTab) {
                    dot.style.background = 'var(--primary)';
                    dot.style.boxShadow = '0 0 0 3px var(--surface)';
                } else {
                    dot.style.background = 'var(--border-color)';
                    dot.style.boxShadow = 'none';
                }
            });
        }
    }
}"""

    if old_func in js:
        js = js.replace(old_func, new_func)
    else:
        print("Warning: Could not find updateScrollProgress function")

    # 2. Add event listeners for prev/next buttons
    listeners_code = """
document.addEventListener('DOMContentLoaded', () => {
    const prevBtn = document.getElementById('prev-theme-btn');
    const nextBtn = document.getElementById('next-theme-btn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentTabIndex > 0) switchThemeTab(currentTabIndex - 1, true);
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (thematicData && currentTabIndex < thematicData.length - 1) {
                switchThemeTab(currentTabIndex + 1, true);
            }
        });
    }
});
"""
    js += listeners_code

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        
    print("Updated reader.js UI logic")

if __name__ == '__main__':
    update_js_ui()
