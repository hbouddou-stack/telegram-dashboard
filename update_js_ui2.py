import re

def update_js_ui2():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Update updateReadingProgress()
    old_func = """function updateReadingProgress(e) {
    const tracker = document.getElementById('reader-progress-tracker');
    const tabReader = document.getElementById('tab-reader');
    
    if (tracker && tabReader.classList.contains('active') && thematicData && thematicData.length > 0) {
        tracker.style.display = 'flex';
        
        // Find the actual scrolling element!
        let target = (e && e.target) ? e.target : document.documentElement;
        if (target === document) target = document.documentElement;
        
        let scrollTop = target.scrollTop || window.scrollY || window.pageYOffset || document.body.scrollTop || 0;
        let scrollHeight = (target.scrollHeight || document.documentElement.scrollHeight) - (target.clientHeight || window.innerHeight);
        
        // If we captured a scroll on something small, fallback to global
        if (scrollHeight <= 0) {
            scrollTop = window.scrollY || document.documentElement.scrollTop;
            scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        }
        
        let scrollPercent = 0;
        if (scrollHeight > 0) {
            scrollPercent = (scrollTop / scrollHeight) * 100;
        } else {
            scrollPercent = 100;
        }
        
        document.getElementById('progress-tracker-percent').textContent = Math.round(Math.min(100, Math.max(0, scrollPercent))) + '%';
        
        const numThemes = thematicData.length;
        if (numThemes > 0) {
            let activeIdx = currentTabIndex;
            
            document.getElementById('progress-tracker-title').textContent = thematicData[activeIdx].title;
            
            const dotsContainer = document.getElementById('progress-tracker-dots');
            
            // Only rebuild dots if necessary
            if (dotsContainer.getAttribute('data-rendered') !== 'true') {
                let dotsHtml = '';
                for (let i = 0; i < numThemes; i++) {
                    const pos = (i / (numThemes > 1 ? numThemes - 1 : 1)) * 100;
                    dotsHtml += `<div class="progress-chapter-dot" data-index="${i}" onclick="switchThemeTab(${i}, true)" style="position: absolute; right: ${pos}%; transform: translateX(50%); width: 10px; height: 10px; border-radius: 50%; background: var(--border-color); z-index: 2; transition: background 0.3s ease; cursor: pointer;"></div>`;
                }
                
                dotsHtml += `<div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 4px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: 0%; transition: width 0.1s ease-out;"></div>`;
                dotsContainer.innerHTML = dotsHtml;
                dotsContainer.setAttribute('data-rendered', 'true');
            }
            
            // Update fill and colors
            const fillEl = document.getElementById('progress-tracker-fill');
            if (fillEl) {
                const fillWidth = (activeIdx / (numThemes > 1 ? numThemes - 1 : 1)) * 100;
                const currentTabProgress = (scrollPercent / 100) * (100 / (numThemes > 1 ? numThemes - 1 : 1));
                const totalFill = fillWidth + currentTabProgress;
                fillEl.style.width = Math.min(100, totalFill) + '%';
            }
            
            const dots = dotsContainer.querySelectorAll('.progress-chapter-dot');
            dots.forEach((dot, idx) => {
                if (idx <= activeIdx) {
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

    new_func = """function updateReadingProgress(e) {
    const tabReader = document.getElementById('tab-reader');
    
    if (tabReader && tabReader.classList.contains('active') && thematicData && thematicData.length > 0) {
        
        let target = (e && e.target) ? e.target : document.documentElement;
        if (target === document) target = document.documentElement;
        
        let scrollTop = target.scrollTop || window.scrollY || window.pageYOffset || document.body.scrollTop || 0;
        let scrollHeight = (target.scrollHeight || document.documentElement.scrollHeight) - (target.clientHeight || window.innerHeight);
        
        if (scrollHeight <= 0) {
            scrollTop = window.scrollY || document.documentElement.scrollTop;
            scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        }
        
        let scrollPercent = 0;
        if (scrollHeight > 0) {
            scrollPercent = (scrollTop / scrollHeight) * 100;
        } else {
            scrollPercent = 100;
        }
        
        const numThemes = thematicData.length;
        if (numThemes > 0) {
            let activeIdx = currentTabIndex;
            
            const titleEl = document.getElementById('current-theme-label');
            if (titleEl) titleEl.textContent = thematicData[activeIdx].title;
            
            const dotsContainer = document.getElementById('progress-tracker-dots');
            if (!dotsContainer) return;
            
            if (dotsContainer.getAttribute('data-rendered') !== 'true') {
                let dotsHtml = '';
                for (let i = 0; i < numThemes; i++) {
                    const pos = (i / (numThemes > 1 ? numThemes - 1 : 1)) * 100;
                    dotsHtml += `<div class="progress-chapter-dot" data-index="${i}" onclick="switchThemeTab(${i}, true)" style="position: absolute; right: ${pos}%; transform: translateX(50%); width: 10px; height: 10px; border-radius: 50%; background: var(--border-color); z-index: 2; transition: background 0.3s ease; cursor: pointer;"></div>`;
                }
                
                dotsHtml += `<div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 4px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: 0%; transition: width 0.1s ease-out;"></div>`;
                dotsContainer.innerHTML = dotsHtml;
                dotsContainer.setAttribute('data-rendered', 'true');
            }
            
            const fillEl = document.getElementById('progress-tracker-fill');
            if (fillEl) {
                const fillWidth = (activeIdx / (numThemes > 1 ? numThemes - 1 : 1)) * 100;
                const currentTabProgress = (scrollPercent / 100) * (100 / (numThemes > 1 ? numThemes - 1 : 1));
                const totalFill = fillWidth + currentTabProgress;
                fillEl.style.width = Math.min(100, totalFill) + '%';
            }
            
            const dots = dotsContainer.querySelectorAll('.progress-chapter-dot');
            dots.forEach((dot, idx) => {
                if (idx <= activeIdx) {
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
        print("Warning: Could not find updateReadingProgress")

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        
    print("Updated reader.js updateReadingProgress")

if __name__ == '__main__':
    update_js_ui2()
