import re

def fix_js():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # We need to fix the updateReadingProgress function
    old_func_match = re.search(r'function updateReadingProgress\(\) \{[\s\S]*?function initUIControls', js)
    
    if old_func_match:
        new_func = """function updateReadingProgress() {
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
            scrollPercent = 100;
        }
        
        document.getElementById('progress-tracker-percent').textContent = Math.round(Math.min(100, Math.max(0, scrollPercent))) + '%';
        
        const numThemes = thematicData.length;
        const segmentPercent = 100 / Math.max(1, (numThemes - 1));
        
        let baseFill = currentTabIndex * segmentPercent;
        if (numThemes === 1) baseFill = scrollPercent;
        
        let totalFill = baseFill;
        if (numThemes > 1) {
            totalFill = baseFill + (scrollPercent / 100) * segmentPercent;
        }
        
        if (thematicData[currentTabIndex]) {
            document.getElementById('progress-tracker-title').textContent = thematicData[currentTabIndex].title;
        }
        
        // Optimize: do not recreate innerHTML on every scroll!
        // Just update the fill bar width.
        const dotsContainer = document.getElementById('progress-tracker-dots');
        
        // If the dots are not initialized for the current lesson, initialize them
        if (dotsContainer.childElementCount <= 2 || dotsContainer.getAttribute('data-lesson') !== `${currentLessonData.subject}_${currentLessonData.lessonNum}`) {
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
                
                dotsHtml += `<div class="progress-dot-item" data-index="${i}" onclick="switchThemeTab(${i}); window.scrollTo({top:0});" style="width: 12px; height: 12px; border-radius: 50%; background: ${color}; position: relative; z-index: 2; cursor: pointer; transform: scale(${scale}); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: ${shadow};"></div>`;
            }
            dotsContainer.innerHTML = `
                <div class="progress-line-bg" style="position: absolute; top: 50%; left: 0; right: 0; height: 4px; background: var(--border); transform: translateY(-50%); border-radius: 2px;"></div>
                <div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 4px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: ${Math.min(100, totalFill)}%; transition: width 0.1s ease-out;"></div>
                ${dotsHtml}
            `;
            dotsContainer.setAttribute('data-lesson', `${currentLessonData.subject}_${currentLessonData.lessonNum}`);
        } else {
            // Already initialized, just update the bar width and the active dot
            const fillEl = document.getElementById('progress-tracker-fill');
            if (fillEl) fillEl.style.width = Math.min(100, totalFill) + '%';
            
            // Update dots classes
            const dots = dotsContainer.querySelectorAll('.progress-dot-item');
            dots.forEach((dot, i) => {
                const isCompleted = currentLessonData ? !!syllabusCompletion[`${currentLessonData.subject}_${currentLessonData.lessonNum}_${i}`] : false;
                const isCurrent = (i === currentTabIndex);
                const isPast = (i < currentTabIndex);
                
                let color = 'var(--border)';
                if (isCompleted || isPast) color = 'var(--primary)';
                if (isCurrent) color = 'var(--accent-color)';
                
                const scale = isCurrent ? '1.4' : (isCompleted ? '1.1' : '1');
                const shadow = isCurrent ? '0 0 0 3px var(--surface), 0 0 8px var(--accent-color)' : '0 0 0 2px var(--surface)';
                
                dot.style.background = color;
                dot.style.transform = `scale(${scale})`;
                dot.style.boxShadow = shadow;
            });
        }
    } else {
        if(tracker) tracker.style.display = 'none';
    }
}

function initUIControls"""
        
        js = js.replace(old_func_match.group(0), new_func)
        with open('reader.js', 'w', encoding='utf-8') as f:
            f.write(js)
        print("Fixed JS logic")

if __name__ == '__main__':
    fix_js()
