import re

def fix_theme_and_add_zen():
    # --- UPDATE reader.js ---
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Replace top-level variables
    old_top = """let isDarkMode = localStorage.getItem('readerTheme') === 'dark';
let fontSizeBase = parseInt(localStorage.getItem('readerFontSize')) || 18; 
if(isDarkMode) document.documentElement.setAttribute('data-theme', 'dark');"""

    new_top = """let currentTheme = localStorage.getItem('readerTheme') || 'light';
let fontSizeBase = parseInt(localStorage.getItem('readerFontSize')) || 18; 
if(currentTheme !== 'light') document.documentElement.setAttribute('data-theme', currentTheme);"""

    if old_top in js:
        js = js.replace(old_top, new_top)
    else:
        # Fallback if already modified
        js = re.sub(r"let isDarkMode = localStorage\.getItem\('readerTheme'\) === 'dark';\n.*?(?=document\.documentElement\.style\.setProperty)", new_top + "\n", js, flags=re.DOTALL)

    # 2. Replace themeBtn logic
    old_theme_logic = """    const themeBtn = document.getElementById('btn-theme-toggle');
    if(themeBtn) themeBtn.textContent = isDarkMode ? '☀️' : '🌙';

    if(themeBtn) {
        themeBtn.addEventListener('click', () => {
            isDarkMode = !isDarkMode;
            const newTheme = isDarkMode ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            themeBtn.textContent = isDarkMode ? '☀️' : '🌙';
            localStorage.setItem('readerTheme', newTheme);
        });
    }"""

    new_theme_logic = """    const themeBtn = document.getElementById('btn-theme-toggle');
    if(themeBtn) {
        if(currentTheme === 'dark') themeBtn.textContent = '☀️';
        else if(currentTheme === 'sepia') themeBtn.textContent = '📜';
        else themeBtn.textContent = '🌙';

        themeBtn.addEventListener('click', () => {
            if (currentTheme === 'light') currentTheme = 'sepia';
            else if (currentTheme === 'sepia') currentTheme = 'dark';
            else currentTheme = 'light';
            
            document.documentElement.setAttribute('data-theme', currentTheme);
            localStorage.setItem('readerTheme', currentTheme);
            
            if (currentTheme === 'dark') themeBtn.textContent = '☀️';
            else if (currentTheme === 'sepia') themeBtn.textContent = '📜';
            else themeBtn.textContent = '🌙';
        });
    }
    
    // ZEN MODE LOGIC
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

    if old_theme_logic in js:
        js = js.replace(old_theme_logic, new_theme_logic)
    else:
        # Fallback
        pass # If we already changed it, leave it

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    # --- UPDATE reader.html ---
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Add Zen Mode Button
    if 'id="btn-zen-toggle"' not in html:
        old_theme_btn = '<button class="control-btn" id="btn-theme-toggle" title="Modifier le thÃ¨me">ðŸŒ™</button>'
        if old_theme_btn not in html:
            # Fallback regex
            html = re.sub(r'<button class="control-btn" id="btn-theme-toggle"[^>]*>.*?</button>', 
                          lambda m: m.group(0) + '\n                            <button class="control-btn" id="btn-zen-toggle" title="Mode Zen" style="margin-right:4px;">👁️</button>', 
                          html)
        else:
            new_theme_btn = old_theme_btn + '\n                            <button class="control-btn" id="btn-zen-toggle" title="Mode Zen" style="margin-right:4px;">👁️</button>'
            html = html.replace(old_theme_btn, new_theme_btn)

    # Add Exit Zen Mode Button
    if 'id="exit-zen-btn"' not in html:
        exit_btn = '<button id="exit-zen-btn" style="display: none; position: fixed; bottom: 20px; right: 20px; z-index: 99999; background: var(--primary, var(--accent-color)); color: white; border: none; border-radius: 50%; width: 50px; height: 50px; font-size: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); cursor: pointer; align-items: center; justify-content: center; transition: transform 0.2s;">❌</button>\n'
        html = html.replace('</body>', exit_btn + '</body>')

    # Add Cache Buster
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=40', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=40', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # --- UPDATE reader.css ---
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    zen_css = """
/* --- ZEN MODE --- */
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
}
"""
    if "/* --- ZEN MODE --- */" not in css:
        css += zen_css

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    print("Sepia fixed and Zen Mode added")

if __name__ == '__main__':
    fix_theme_and_add_zen()
