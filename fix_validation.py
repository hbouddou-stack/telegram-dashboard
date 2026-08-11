import re

def implement_validation():
    # --- UPDATE reader.css ---
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    new_css = """
/* --- VALIDATION BUTTONS --- */
.validate-chapter-btn {
    background: var(--surface-2);
    color: var(--text);
    border: 2px solid var(--border-color);
    padding: 12px 24px;
    border-radius: 30px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin: 20px auto;
}
.validate-chapter-btn.completed {
    background: var(--primary, var(--accent-color));
    border-color: var(--primary, var(--accent-color));
    color: white;
}
.sommaire-check-btn {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 2px solid var(--border-color);
    background: transparent;
    color: white;
    font-size: 14px;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    transition: all 0.3s;
    flex-shrink: 0;
    margin-right: 12px;
}
.sommaire-check-btn.completed {
    background: var(--primary, var(--accent-color));
    border-color: var(--primary, var(--accent-color));
}
"""
    if "/* --- VALIDATION BUTTONS --- */" not in css:
        css += "\n" + new_css
        with open('reader.css', 'w', encoding='utf-8') as f:
            f.write(css)

    # --- UPDATE reader.js ---
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Update renderSommaire
    old_sommaire = """function renderSommaire() {
    const listContainer = document.getElementById('sommaire-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';
    
    const sheetTitle = document.querySelector('#sommaire-sheet .bottom-sheet-header h3');
    if (sheetTitle && currentLessonData) {
        sheetTitle.textContent = `محاور الدرس ${currentLessonData.lessonNum}`;
    }

    thematicData.forEach((data, index) => {
        let item = document.createElement('div');
        item.className = 'theme-item';
        if (data.level === 2) {
            item.classList.add('level-2');
        }
        item.textContent = `${index + 1}. ${data.title}`;
        item.onclick = () => {
            switchThemeTab(index, true);
            document.getElementById('sommaire-overlay').classList.remove('show');
            document.getElementById('sommaire-sheet').classList.remove('open');
        };
        listContainer.appendChild(item);
    });
}"""

    new_sommaire = """function renderSommaire() {
    const listContainer = document.getElementById('sommaire-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';
    
    const sheetTitle = document.querySelector('#sommaire-sheet .bottom-sheet-header h3');
    if (sheetTitle && currentLessonData) {
        sheetTitle.textContent = `محاور الدرس ${currentLessonData.lessonNum}`;
    }

    thematicData.forEach((data, index) => {
        let item = document.createElement('div');
        item.className = 'theme-item';
        if (data.level === 2) item.classList.add('level-2');
        
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.justifyContent = 'space-between';
        
        const compKey = `${currentLessonData.subject}_${currentLessonData.lessonNum}_${index}`;
        let isComp = !!syllabusCompletion[compKey];
        
        item.innerHTML = `<span style="flex:1; text-align:right;">${index + 1}. ${data.title}</span>`;
        
        let checkBtn = document.createElement('button');
        checkBtn.className = 'sommaire-check-btn ' + (isComp ? 'completed' : '');
        checkBtn.innerHTML = isComp ? '✓' : '';
        checkBtn.onclick = (e) => {
            e.stopPropagation();
            isComp = !isComp;
            syllabusCompletion[compKey] = isComp;
            localStorage.setItem('academy_syllabus_completions', JSON.stringify(syllabusCompletion));
            checkBtn.className = 'sommaire-check-btn ' + (isComp ? 'completed' : '');
            checkBtn.innerHTML = isComp ? '✓' : '';
            
            updateDashboardProgress();
            
            if (currentTabIndex === index) {
                const vBtn = document.querySelector('.validate-chapter-btn');
                if (vBtn) {
                    vBtn.className = isComp ? 'validate-chapter-btn completed' : 'validate-chapter-btn';
                    vBtn.innerHTML = isComp ? '✓ تم إنجاز المحور' : 'تعليم كمقروء';
                }
            }
        };
        
        item.appendChild(checkBtn);
        
        item.onclick = (e) => {
            if (e.target === checkBtn) return;
            switchThemeTab(index, true);
            document.getElementById('sommaire-overlay').classList.remove('show');
            document.getElementById('sommaire-sheet').classList.remove('open');
        };
        listContainer.appendChild(item);
    });
}"""

    # Because regex with arabic is flaky, we replace the block directly or use a very precise regex
    js = re.sub(r'function renderSommaire\(\) \{.*?(?=function switchThemeTab)', new_sommaire + "\n\n", js, flags=re.DOTALL)

    # 2. Update switchThemeTab to append the validation button
    # Let's find: `contentDiv.appendChild(textWrapper);` inside `switchThemeTab`
    old_switch_text = "contentDiv.appendChild(textWrapper);"
    new_switch_text = """contentDiv.appendChild(textWrapper);
    
    // --- Add Validation Button ---
    if (currentLessonData) {
        const compKey = `${currentLessonData.subject}_${currentLessonData.lessonNum}_${index}`;
        let isComp = !!syllabusCompletion[compKey];
        
        let validateBtnWrapper = document.createElement('div');
        validateBtnWrapper.style.margin = "30px 0";
        validateBtnWrapper.style.display = "flex";
        validateBtnWrapper.style.justifyContent = "center";
        
        let validateBtn = document.createElement('button');
        validateBtn.className = isComp ? 'validate-chapter-btn completed' : 'validate-chapter-btn';
        validateBtn.innerHTML = isComp ? '✓ تم إنجاز المحور' : 'تعليم كمقروء';
        validateBtn.onclick = () => {
            isComp = !isComp;
            syllabusCompletion[compKey] = isComp;
            localStorage.setItem('academy_syllabus_completions', JSON.stringify(syllabusCompletion));
            validateBtn.className = isComp ? 'validate-chapter-btn completed' : 'validate-chapter-btn';
            validateBtn.innerHTML = isComp ? '✓ تم إنجاز المحور' : 'تعليم كمقروء';
            
            updateDashboardProgress();
            renderSommaire();
        };
        validateBtnWrapper.appendChild(validateBtn);
        contentDiv.appendChild(validateBtnWrapper);
    }
"""
    if "validate-chapter-btn" not in js:
        js = js.replace(old_switch_text, new_switch_text)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    # --- Cache Buster ---
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=46', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=46', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Success")

if __name__ == '__main__':
    implement_validation()
