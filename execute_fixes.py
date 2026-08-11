import re

def execute_fixes():
    # 1. Update HTML: Change "Sommaire (Chapitres)" to "محاور الدرس" and fix Glossary
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    html = html.replace('Sommaire (Chapitres)', 'محاور الدرس')

    old_glossary = """    <div id="glossary-popup-overlay" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:9998; backdrop-filter:blur(2px);"></div>
    <div id="glossary-popup" style="display:none; position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); width:90%; max-width:400px; background:var(--surface); border-radius:16px; box-shadow:0 10px 40px rgba(0,0,0,0.25); z-index:9999; padding:20px; border-right:4px solid var(--primary); text-align:right;">"""

    new_glossary = """    <div id="glossary-popup" style="display:none; position:fixed; bottom:30px; left:50%; transform:translateX(-50%); width:90%; max-width:400px; background:var(--surface); border-radius:16px; box-shadow:0 10px 25px rgba(0,0,0,0.15); z-index:9999; padding:16px; border-right:4px solid var(--primary); text-align:right;">"""

    if old_glossary in html:
        html = html.replace(old_glossary, new_glossary)
    else:
        print("Warning: Could not find glossary HTML")

    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=30', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=30', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # 2. Update JS: Progress bar logic, event listeners, and chapter numbering
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Remove scroll listeners for reading progress
    js = re.sub(r"window\.addEventListener\('scroll',\s*\(e\)\s*=>\s*\{\s*updateReadingProgress\(e\);\s*\},.*?\);\s*", "", js, flags=re.DOTALL)
    js = re.sub(r"window\.addEventListener\('touchmove',\s*\(e\)\s*=>\s*\{\s*updateReadingProgress\(e\);\s*\}.*?\);\s*", "", js, flags=re.DOTALL)

    # Replace updateReadingProgress with updateDashboardProgress based on video time
    old_prog = r"function updateReadingProgress\(e\) \{[\s\S]*?\}\n\}"
    
    new_prog = """function updateDashboardProgress() {
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
        }
        
        const titleEl = document.getElementById('current-theme-label');
        if (titleEl && currentTab) titleEl.textContent = (activeIdx + 1) + ". " + currentTab.title;
        
        const dotsContainer = document.getElementById('progress-tracker-dots');
        if (!dotsContainer) return;
        
        if (dotsContainer.childElementCount <= 2 || dotsContainer.getAttribute('data-lesson') !== `${currentLessonData.subject}_${currentLessonData.lessonNum}`) {
            let dotsHtml = '';
            for(let i = 0; i < numThemes; i++) {
                const isCompleted = currentLessonData ? !!syllabusCompletion[`${currentLessonData.subject}_${currentLessonData.lessonNum}_${i}`] : false;
                const isCurrent = (i === activeIdx);
                const isPast = (i < activeIdx);
                
                let color = 'var(--border-color)';
                if (isCompleted || isPast) color = 'var(--primary)';
                if (isCurrent) color = 'var(--accent-color)';
                
                const scale = isCurrent ? '1.4' : (isCompleted ? '1.1' : '1');
                const shadow = isCurrent ? '0 0 0 3px var(--surface), 0 0 8px var(--accent-color)' : '0 0 0 2px var(--surface)';
                
                const pos = (i / (numThemes > 1 ? numThemes - 1 : 1)) * 100;
                dotsHtml += `<div class="progress-dot-item" data-index="${i}" onclick="switchThemeTab(${i}); window.scrollTo({top:0});" style="position: absolute; right: ${pos}%; transform: translateX(50%) scale(${scale}); width: 12px; height: 12px; border-radius: 50%; background: ${color}; z-index: 2; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: ${shadow};"></div>`;
            }
            dotsContainer.innerHTML = `
                <div class="progress-line-bg" style="position: absolute; top: 50%; left: 0; right: 0; height: 4px; background: var(--border-color); transform: translateY(-50%); border-radius: 2px;"></div>
                <div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 4px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: ${Math.min(100, totalFill)}%; transition: width 0.1s ease-out;"></div>
                ${dotsHtml}
            `;
            dotsContainer.setAttribute('data-lesson', `${currentLessonData.subject}_${currentLessonData.lessonNum}`);
        } else {
            const fillEl = document.getElementById('progress-tracker-fill');
            if (fillEl) fillEl.style.width = Math.min(100, totalFill) + '%';
            
            const dots = dotsContainer.querySelectorAll('.progress-dot-item');
            dots.forEach((dot, i) => {
                const isCompleted = currentLessonData ? !!syllabusCompletion[`${currentLessonData.subject}_${currentLessonData.lessonNum}_${i}`] : false;
                const isCurrent = (i === activeIdx);
                const isPast = (i < activeIdx);
                
                let color = 'var(--border-color)';
                if (isCompleted || isPast) color = 'var(--primary)';
                if (isCurrent) color = 'var(--accent-color)';
                
                const scale = isCurrent ? '1.4' : (isCompleted ? '1.1' : '1');
                const shadow = isCurrent ? '0 0 0 3px var(--surface), 0 0 8px var(--accent-color)' : '0 0 0 2px var(--surface)';
                
                dot.style.background = color;
                dot.style.transform = `translateX(50%) scale(${scale})`;
                dot.style.boxShadow = shadow;
            });
        }
    }
}"""

    # We need to replace safely
    js = re.sub(old_prog, new_prog, js, count=1)

    # Call updateDashboardProgress inside setInterval Karaoke Engine
    if "let currentTime = player.getCurrentTime();" in js:
        js = js.replace("let currentTime = player.getCurrentTime();", "let currentTime = player.getCurrentTime();\n    updateDashboardProgress();")

    # Update Sommaire List numbering
    old_list = "html += `\\n                <div class=\"theme-list-item ${isActive ? 'active' : ''}\" onclick=\"switchThemeTab(${i}); closeSommaireSheet(); window.scrollTo({top:0});\">\\n                    <div class=\"theme-title\">${theme.title}</div>\\n                    <div class=\"theme-meta\">${formatTime(theme.startTime)} - ${formatTime(theme.endTime)}</div>\\n                </div>\\n            `;"
    new_list = "html += `\\n                <div class=\"theme-list-item ${isActive ? 'active' : ''}\" onclick=\"switchThemeTab(${i}); closeSommaireSheet(); window.scrollTo({top:0});\">\\n                    <div class=\"theme-title\">${i + 1}. ${theme.title}</div>\\n                    <div class=\"theme-meta\">${formatTime(theme.startTime)} - ${formatTime(theme.endTime)}</div>\\n                </div>\\n            `;"
    js = js.replace(old_list, new_list)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
        
    print("Execution complete")

if __name__ == '__main__':
    execute_fixes()
