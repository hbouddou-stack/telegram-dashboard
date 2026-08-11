import re

def fix_all_features():
    # --- UPDATE reader.js ---
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Remove scroll listener for updateDashboardProgress
    js = js.replace("window.addEventListener('scroll', () => { updateDashboardProgress(); }, { passive: true, capture: true });", "")
    js = js.replace("window.addEventListener('touchmove', () => { updateDashboardProgress(); }, { passive: true });", "")

    # 2. Update Zen Mode logic
    old_zen_logic = """    // ZEN MODE LOGIC
    const zenBtn = document.getElementById('btn-zen-toggle');
    const exitZenBtn = document.getElementById('exit-zen-btn');
    if (zenBtn && exitZenBtn) {
        zenBtn.addEventListener('click', () => {
            document.body.classList.add('zen-mode');
            exitZenBtn.style.display = 'block';
            
            // Si on veut aussi cacher les contoles youtube (optionnel mais demandÃ© plus tÃ´t)
            if (player && typeof player.setOption === 'function') {
               // player.setOption('controls', 0); // Not always supported on the fly by YT API
            }
        });
        
        exitZenBtn.addEventListener('click', () => {
            document.body.classList.remove('zen-mode');
            exitZenBtn.style.display = 'none';
        });
    }"""
    
    new_zen_logic = """    // ZEN MODE LOGIC
    const zenBtn = document.getElementById('btn-zen-toggle');
    if (zenBtn) {
        zenBtn.addEventListener('click', () => {
            document.body.classList.toggle('zen-mode');
            if (document.body.classList.contains('zen-mode')) {
                zenBtn.style.color = 'var(--primary, var(--accent-color))';
            } else {
                zenBtn.style.color = '';
            }
        });
    }"""
    
    if old_zen_logic in js:
        js = js.replace(old_zen_logic, new_zen_logic)

    # 3. Rewrite updateDashboardProgress
    old_update_progress = """function updateDashboardProgress() {
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
        
        // La ligne bleue se remplit de 0 Ã  100% selon le dÃ©filement global
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
                
                // Repartir les points sur la longueur, MAIS diviser par numThemes pour que le dernier point ne soit pas Ã  100%
                const pos = (i / numThemes) * 100;
                
                dotsHtml += `
                <div class="progress-dot-item" style="position: absolute; left: ${pos}%; top: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; z-index: 2; transition: all 0.3s; cursor:pointer;" onclick="switchThemeTab(${i});">
                    <div style="width: 12px; height: 12px; border-radius: 50%; background: ${color}; border: 2px solid var(--surface); box-shadow: ${shadow}; transform: scale(${scale}); transition: all 0.3s;"></div>
                </div>`;
            }
            dotsHtml += `
            <div class="progress-line-bg" style="position: absolute; top: 50%; left: 0; right: 0; height: 4px; background: var(--surface-2); transform: translateY(-50%); border-radius: 2px; z-index: 0;"></div>
            <div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; left: 0; height: 4px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: ${Math.min(100, totalFill)}%; transition: width 0.1s ease-out; z-index: 1;"></div>
            `;
            dotsContainer.innerHTML = dotsHtml;
            dotsContainer.setAttribute('data-lesson', `${currentLessonData.subject}_${currentLessonData.lessonNum}`);
        } else {
            const fillEl = document.getElementById('progress-tracker-fill');
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
                
                const dotCircle = dot.firstElementChild;
                dotCircle.style.background = color;
                dotCircle.style.boxShadow = shadow;
                dotCircle.style.transform = `scale(${scale})`;
            });
            
            if (fillEl) fillEl.style.width = `${Math.min(100, totalFill)}%`;
        }
    }
}"""

    # We will use regex to replace updateDashboardProgress because it might have slight variations
    new_update_progress = """function updateDashboardProgress() {
    if (!thematicData || thematicData.length === 0) return;
    
    let currentTime = 0;
    let duration = 1;
    if (player && typeof player.getCurrentTime === 'function') {
        currentTime = player.getCurrentTime() || 0;
        duration = player.getDuration() || 1;
    }

    const numThemes = thematicData.length;
    let activeIdx = currentTabIndex;

    // Calculate progress fraction based on Video Time relative to chapters
    let totalFill = 0;
    
    if (numThemes <= 1) {
        totalFill = (currentTime / duration) * 100;
    } else {
        let blockIndex = 0;
        for (let i = 0; i < numThemes; i++) {
            if (currentTime >= thematicData[i].startTime && (i === numThemes - 1 || currentTime < thematicData[i+1].startTime)) {
                blockIndex = i;
                break;
            }
        }
        
        let blockStart = thematicData[blockIndex].startTime;
        let blockEnd = (blockIndex === numThemes - 1) ? duration : thematicData[blockIndex+1].startTime;
        let blockDuration = blockEnd - blockStart;
        if (blockDuration <= 0) blockDuration = 1;
        
        let fractionInBlock = (currentTime - blockStart) / blockDuration;
        fractionInBlock = Math.max(0, Math.min(1, fractionInBlock));
        
        let spacePerBlock = 100 / (numThemes - 1);
        totalFill = (blockIndex * spacePerBlock) + (fractionInBlock * spacePerBlock);
    }
    totalFill = Math.max(0, Math.min(100, totalFill));

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
            
            let bgClass = isPast || isCurrent || isCompleted ? 'var(--primary, var(--accent-color))' : 'var(--surface-2)';
            let borderColor = isPast || isCurrent || isCompleted ? 'var(--primary, var(--accent-color))' : 'var(--border-color)';
            
            const scale = isCurrent ? '1.4' : (isCompleted ? '1.1' : '1');
            const pos = numThemes <= 1 ? 0 : (i / (numThemes - 1)) * 100;
            
            dotsHtml += `
            <div class="progress-dot-item" style="position: absolute; left: ${pos}%; top: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; z-index: 2; transition: all 0.3s; cursor:pointer;" onclick="switchThemeTab(${i});">
                <div style="width: 12px; height: 12px; border-radius: 50%; background: ${bgClass}; border: 2px solid var(--surface); box-shadow: 0 0 0 1px ${borderColor}; transform: scale(${scale}); transition: all 0.3s;"></div>
            </div>`;
        }
        dotsHtml += `
        <div class="progress-line-bg" style="position: absolute; top: 50%; left: 0; right: 0; height: 4px; background: var(--surface-2); transform: translateY(-50%); border-radius: 2px; z-index: 0;"></div>
        <div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; left: 0; height: 4px; background: var(--primary, var(--accent-color)); transform: translateY(-50%); border-radius: 2px; width: ${totalFill}%; transition: width 0.1s linear; z-index: 1;"></div>
        `;
        dotsContainer.innerHTML = dotsHtml;
        dotsContainer.setAttribute('data-lesson', `${currentLessonData.subject}_${currentLessonData.lessonNum}`);
    } else {
        const fillEl = document.getElementById('progress-tracker-fill');
        const dots = dotsContainer.querySelectorAll('.progress-dot-item');
        dots.forEach((dot, i) => {
            const isCompleted = currentLessonData ? !!syllabusCompletion[`${currentLessonData.subject}_${currentLessonData.lessonNum}_${i}`] : false;
            const isCurrent = (i === activeIdx);
            const isPast = (i < activeIdx);
            
            let bgClass = isPast || isCurrent || isCompleted ? 'var(--primary, var(--accent-color))' : 'var(--surface-2)';
            let borderColor = isPast || isCurrent || isCompleted ? 'var(--primary, var(--accent-color))' : 'var(--border-color)';
            
            const scale = isCurrent ? '1.4' : (isCompleted ? '1.1' : '1');
            
            const dotCircle = dot.firstElementChild;
            dotCircle.style.background = bgClass;
            dotCircle.style.boxShadow = `0 0 0 1px ${borderColor}`;
            dotCircle.style.transform = `scale(${scale})`;
        });
        
        if (fillEl) {
            fillEl.style.width = `${totalFill}%`;
            fillEl.style.background = 'var(--primary, var(--accent-color))';
        }
    }
}"""
    
    js = re.sub(r'function updateDashboardProgress\(\) \{.*?(?=function|\/\/ ---)', new_update_progress + "\n\n", js, flags=re.DOTALL)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    # --- UPDATE reader.css ---
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # Update Zen Mode CSS
    old_zen_css = """/* --- ZEN MODE --- */
body.zen-mode .sticky-header {
    display: none !important;
}
body.zen-mode .bottom-nav {
    display: none !important;
}
body.zen-mode .floating-back-btn {
    display: none !important;
}
body.zen-mode #reader-content {
    margin-bottom: 20px !important;
    padding-top: 10px !important;
}"""

    new_zen_css = """/* --- ZEN MODE (LECTURE SEULE) --- */
body.zen-mode #video-wrapper {
    height: 0 !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    opacity: 0 !important;
}
body.zen-mode .bottom-nav {
    display: none !important;
}
body.zen-mode .floating-back-btn {
    display: none !important;
}
body.zen-mode #reader-content {
    margin-bottom: 20px !important;
    padding-top: 10px !important;
}"""
    
    if old_zen_css in css:
        css = css.replace(old_zen_css, new_zen_css)

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # --- UPDATE reader.html ---
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Remove exit-zen-btn
    html = re.sub(r'<button id="exit-zen-btn"[^>]*>❌</button>', '', html)

    # Cache buster
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=42', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=42', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Success")

if __name__ == '__main__':
    fix_all_features()
