import re

def fix_all():
    # --- UPDATE reader.css ---
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # Fix .btn.active
    old_active = """.settings-btn-group .btn.active {
    background: var(--primary) !important;
    color: #ffffff !important;
    border-color: var(--primary) !important;
}"""
    new_active = """.settings-btn-group .btn.active {
    background: var(--primary, var(--accent-color)) !important;
    color: #ffffff !important;
    border-color: var(--primary, var(--accent-color)) !important;
}"""
    
    if old_active in css:
        css = css.replace(old_active, new_active)
    elif "background: var(--primary) !important;" in css:
        # Fallback regex
        css = css.replace("background: var(--primary) !important;", "background: var(--primary, var(--accent-color)) !important;")
        css = css.replace("border-color: var(--primary) !important;", "border-color: var(--primary, var(--accent-color)) !important;")

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # --- UPDATE reader.js ---
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Fix renderSommaire
    old_render = """function renderSommaire() {
    const listContainer = document.getElementById('sommaire-list');
    if (!listContainer) return;
    listContainer.innerHTML = '';

    thematicData.forEach((data, index) => {
        let item = document.createElement('div');
        item.className = 'theme-item';
        if (data.level === 2) {
            item.classList.add('level-2');
        }
        item.textContent = data.title;
        item.onclick = () => {
            switchThemeTab(index, true);
            document.getElementById('sommaire-overlay').classList.remove('show');
            document.getElementById('sommaire-sheet').classList.remove('open');
        };
        listContainer.appendChild(item);
    });
}"""

    new_render = """function renderSommaire() {
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

    if old_render in js:
        js = js.replace(old_render, new_render)
    else:
        # Fallback replacement if exact string doesn't match
        js = re.sub(
            r"item\.textContent = data\.title;",
            "item.textContent = `${index + 1}. ${data.title}`;",
            js
        )
        if "sheetTitle.textContent =" not in js:
            js = js.replace("listContainer.innerHTML = '';", "listContainer.innerHTML = '';\n    const sheetTitle = document.querySelector('#sommaire-sheet .bottom-sheet-header h3');\n    if (sheetTitle && typeof currentLessonData !== 'undefined' && currentLessonData) {\n        sheetTitle.textContent = `محاور الدرس ${currentLessonData.lessonNum}`;\n    }")

    # Ensure updateSpeedUI handles initial load
    # No change needed, updateSpeedUI is called in DOMContentLoaded

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    # --- UPDATE reader.html Cache Buster ---
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=39', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=39', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Fixes applied successfully")

if __name__ == '__main__':
    fix_all()
