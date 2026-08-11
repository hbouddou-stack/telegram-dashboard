import re

def implement_sepia_and_spacing():
    # 1. Update reader.css
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    sepia_css = """
/* --- SEPIA THEME --- */
[data-theme='sepia'] {
    --bg: #f4ecd8;
    --surface: #fdf6e3;
    --surface-2: #eee8d5;
    --text: #4a3c31;
    --text-secondary: #706254;
    --border-color: #e5dac1;
    --primary: #b45309;
    --primary-hover: #92400e;
    --highlight-bg: rgba(180, 83, 9, 0.15);
    --highlight-text: #b45309;
}
[data-theme='sepia'] .karaoke-segment.active-karaoke {
    background-color: var(--highlight-bg);
    color: var(--highlight-text);
    -webkit-text-stroke: 0.6px var(--highlight-text);
}
"""
    if "[data-theme='sepia']" not in css:
        css += sepia_css

    spacing_css = """
/* --- ESPACEMENT AÉRÉ --- */
#reader-content.spacing-aere .text-paragraph {
    line-height: 2.6 !important;
    margin-bottom: 32px !important;
}
#reader-content.spacing-aere .karaoke-segment {
    line-height: 2.6 !important;
}
"""
    if "spacing-aere" not in css:
        css += spacing_css

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # 2. Update reader.html
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Add Espacement Aéré toggle in settings sheet
    spacing_toggle = """            <div class="settings-group">
                <h4>Mode Focus (Concentration)</h4>
                <div class="setting-item">
                    <span>Estomper le texte inactif</span>
                    <label class="switch">
                        <input type="checkbox" id="focus-mode-toggle">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>
            
            <div class="settings-group">
                <h4>Espacement du texte</h4>
                <div class="setting-item">
                    <span>Aérer les lignes (Lecture facile)</span>
                    <label class="switch">
                        <input type="checkbox" id="spacing-toggle">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>"""
    
    # We replace the old focus mode block with the new one containing spacing
    old_focus = """            <div class="settings-group">
                <h4>Mode Focus (Concentration)</h4>
                <div class="setting-item">
                    <span>Estomper le texte inactif</span>
                    <label class="switch">
                        <input type="checkbox" id="focus-mode-toggle">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>"""
    
    if old_focus in html and 'id="spacing-toggle"' not in html:
        html = html.replace(old_focus, spacing_toggle)

    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=33', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=33', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # 3. Update reader.js
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Update readerSettings
    if "spacingAere: false" not in js:
        js = js.replace("scrollMode: 'zone', // 'zone' or 'teleprompter'\n    focusMode: false", "scrollMode: 'zone',\n    focusMode: false,\n    spacingAere: false")

    # Update loadSettings
    if "spacingAere = saved.spacingAere" not in js:
        load_settings_patch = """
        if (saved.spacingAere !== undefined) readerSettings.spacingAere = saved.spacingAere;
        
        applyFocusMode();
        applySpacing();
        
        // Update UI
        const spacingToggle = document.getElementById('spacing-toggle');
        if (spacingToggle) spacingToggle.checked = readerSettings.spacingAere;
"""
        js = js.replace("applyFocusMode();", load_settings_patch)

    # Add applySpacing function
    if "function applySpacing" not in js:
        apply_spacing_func = """
function applySpacing() {
    const rc = document.getElementById('reader-content');
    if (rc) {
        if (readerSettings.spacingAere) {
            rc.classList.add('spacing-aere');
        } else {
            rc.classList.remove('spacing-aere');
        }
    }
}
"""
        js += apply_spacing_func

    # Update initSettingsUI
    if "spacingToggle.addEventListener" not in js:
        init_ui_patch = """
    const spacingToggle = document.getElementById('spacing-toggle');
    if (spacingToggle) {
        spacingToggle.addEventListener('change', (e) => {
            readerSettings.spacingAere = e.target.checked;
            saveSettings();
            applySpacing();
        });
    }
"""
        js = js.replace("saveSettings();\n        });\n    }", "saveSettings();\n        });\n    }\n" + init_ui_patch)

    # Theme toggling logic
    # Find btn-theme-toggle
    old_theme_logic = """    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    if (btnThemeToggle) {
        btnThemeToggle.addEventListener('click', () => {
            let currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            let newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            btnThemeToggle.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        });
    }"""
    
    new_theme_logic = """    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    if (btnThemeToggle) {
        btnThemeToggle.addEventListener('click', () => {
            let currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            let newTheme;
            if (currentTheme === 'light') newTheme = 'sepia';
            else if (currentTheme === 'sepia') newTheme = 'dark';
            else newTheme = 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            if (newTheme === 'dark') btnThemeToggle.textContent = '☀️';
            else if (newTheme === 'sepia') btnThemeToggle.textContent = '📜';
            else btnThemeToggle.textContent = '🌙';
        });
        
        // Initial icon setup
        let currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        if (currentTheme === 'dark') btnThemeToggle.textContent = '☀️';
        else if (currentTheme === 'sepia') btnThemeToggle.textContent = '📜';
        else btnThemeToggle.textContent = '🌙';
    }"""
    
    if old_theme_logic in js:
        js = js.replace(old_theme_logic, new_theme_logic)
    elif "btnThemeToggle.addEventListener('click'" in js:
        # manual replace if exact block mismatch
        js = re.sub(r"const btnThemeToggle = document\.getElementById\('btn-theme-toggle'\);.*?\}\);[^\}]*\}", new_theme_logic, js, flags=re.DOTALL)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    print("Execution complete for Sepia and Spacing")

if __name__ == '__main__':
    implement_sepia_and_spacing()
