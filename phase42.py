import re

def execute_phase4_fixes():
    # 1. Update reader.html
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Translate "Chapitres de la leçon" -> "محاور الدرس" in bottom sheet
    html = html.replace('<h3>Chapitres de la leçon</h3>', '<h3>محاور الدرس</h3>')

    # Update cache buster
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=31', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=31', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # 2. Update reader.css
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # Make Sommaire list more compact
    old_theme_list = """.theme-list-item {
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;
    transition: background-color 0.2s;
}"""
    new_theme_list = """.theme-list-item {
    padding: 12px 16px; /* Reduced padding */
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;
    transition: background-color 0.2s;
}"""
    if old_theme_list in css:
        css = css.replace(old_theme_list, new_theme_list)
        
    old_theme_title = """.theme-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
}"""
    new_theme_title = """.theme-title {
    font-size: 14px; /* Reduced font size */
    font-weight: 600;
    color: var(--text);
    margin-bottom: 2px;
}"""
    if old_theme_title in css:
        css = css.replace(old_theme_title, new_theme_title)

    # Adjust Glossary popup Safe Area
    old_glossary_css = """#glossary-popup {
    bottom: 30px;"""
    new_glossary_css = """#glossary-popup {
    bottom: 80px; /* Safe Area for multiple lines */
    max-height: 40vh;
    overflow-y: auto;"""
    if old_glossary_css in css:
        css = css.replace(old_glossary_css, new_glossary_css)
    else:
        # If inline style was used in HTML, we will add CSS rules anyway to override
        css += """\n#glossary-popup { bottom: 80px !important; max-height: 40vh !important; overflow-y: auto !important; padding-bottom: 24px !important; }\n"""

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # 3. Update reader.js
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Fix progress bar math
    old_progress = """function updateDashboardProgress() {
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

    new_progress = """function updateDashboardProgress() {
    if (!thematicData || thematicData.length === 0) return;
    
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
        
        // La ligne bleue se remplit de 0 à 100% selon le défilement global
        let totalFill = scrollPercent;

        const titleEl = document.getElementById('current-theme-label');
        let currentTab = thematicData[activeIdx];
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
                
                // Repartir les points sur la longueur, MAIS diviser par numThemes pour que le dernier point ne soit pas à 100%
                const pos = (i / numThemes) * 100;
                // right: pos% (vu qu'on est en RTL, le point commence à droite et va vers la gauche)
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
}
"""

    # We need to use regex since we are replacing a block that might not exactly match due to my previous patch
    old_prog_regex = r"function updateDashboardProgress\(\) \{.*?\}\n\}\n"
    js = re.sub(old_prog_regex, new_progress, js, flags=re.DOTALL)

    # Pin button logic
    pin_logic = """
document.addEventListener('DOMContentLoaded', () => {
    const stickyToggleBtn = document.getElementById('btn-sticky-toggle');
    const stickyContainer = document.getElementById('sticky-header-container');
    
    if (stickyToggleBtn && stickyContainer) {
        stickyToggleBtn.addEventListener('click', () => {
            if (stickyContainer.style.position === 'relative') {
                stickyContainer.style.position = 'sticky';
                stickyToggleBtn.style.background = 'var(--surface)';
                stickyToggleBtn.style.color = 'var(--text)';
                stickyToggleBtn.setAttribute('title', 'Désépingler la vidéo');
            } else {
                stickyContainer.style.position = 'relative';
                stickyToggleBtn.style.background = 'var(--primary)';
                stickyToggleBtn.style.color = 'white';
                stickyToggleBtn.setAttribute('title', 'Épingler la vidéo');
            }
        });
    }
});
"""
    if "stickyToggleBtn.addEventListener" not in js:
        js += pin_logic

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    print("Execution complete for Phase 4.2")

if __name__ == '__main__':
    execute_phase4_fixes()
