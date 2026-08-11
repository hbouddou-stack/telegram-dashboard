import re

def fix_rtl_progress_and_delay():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. Fix progress bar RTL (right to left)
    # Change "left: ${pos}%" to "right: ${pos}%" for dots
    js = js.replace('style="position: absolute; left: ${pos}%;', 'style="position: absolute; right: ${pos}%;')
    # Change "left: 0; right: 0" to just be normal, but for fill:
    js = js.replace('<div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; left: 0;', 
                    '<div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0;')

    # 2. Fix the delay in numbering the thematic title
    # Find `function switchThemeTab`
    # It probably has something like `currentThemeLabel.textContent = thematicData[index].title;`
    # Let's search for `currentThemeLabel.textContent` inside `switchThemeTab`.
    
    # Actually, let's just make switchThemeTab immediately call updateDashboardProgress()
    # Or find where the title is set.
    
    old_switch_logic = """function switchThemeTab(index, shouldSeek = true) {
    if (!thematicData || !thematicData[index]) return;
    
    currentTabIndex = index;"""

    new_switch_logic = """function switchThemeTab(index, shouldSeek = true) {
    if (!thematicData || !thematicData[index]) return;
    
    currentTabIndex = index;
    
    // Update title immediately to avoid delay in numbering
    const titleEl = document.getElementById('current-theme-label');
    if (titleEl) {
        titleEl.textContent = (index + 1) + ". " + thematicData[index].title;
    }"""
    
    if old_switch_logic in js:
        js = js.replace(old_switch_logic, new_switch_logic)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    # 3. Update cache buster
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=43', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=43', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Fixes applied")

if __name__ == '__main__':
    fix_rtl_progress_and_delay()
