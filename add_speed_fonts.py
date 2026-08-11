import re

def add_speed_and_fonts():
    # --- UPDATE reader.html ---
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Update Google Fonts
    old_fonts = 'family=Amiri:wght@400;700&family=Tajawal:wght@400;500;700;800&display=swap'
    new_fonts = 'family=Amiri:wght@400;700&family=Cairo:wght@400;600;700&family=Tajawal:wght@400;500;700;800&display=swap'
    html = html.replace(old_fonts, new_fonts)

    # Add Speed Button
    old_btns = '<button class="control-btn" id="btn-sticky-toggle" title="Désépingler la vidéo" style="background:var(--surface); color:var(--text); border:1px solid var(--border-color); border-radius:8px; padding:6px 10px; font-size:14px; margin-right: 4px;">📌</button>'
    new_btns = '<button class="control-btn" id="btn-speed-toggle" title="Vitesse" style="background:var(--surface); color:var(--text); border:1px solid var(--border-color); border-radius:8px; padding:6px 10px; font-size:14px; margin-right: 4px; font-weight: bold; width: 45px;">1x</button>\n' + old_btns
    html = html.replace(old_btns, new_btns)

    # Add Font Selection to Settings Sheet
    font_html = """
            <div class="setting-group" style="margin-bottom: 24px;">
                <h4 style="margin: 0 0 8px 0; font-size: 17px; color: var(--text);">نوع الخط (Police)</h4>
                <p style="font-size: 13px; color: var(--text-2); margin-top: 0; margin-bottom: 12px;">اختر الخط الأنسب للقراءة.</p>
                <div style="display: flex; gap: 10px; direction: rtl;">
                    <button class="font-select-btn" data-font="'Tajawal', sans-serif" style="flex:1; padding:10px; border-radius:8px; border:1px solid var(--border-color); background:var(--surface); color:var(--text); font-family:'Tajawal', sans-serif; font-size:16px; cursor:pointer;">حديث</button>
                    <button class="font-select-btn" data-font="'Amiri', serif" style="flex:1; padding:10px; border-radius:8px; border:1px solid var(--border-color); background:var(--surface); color:var(--text); font-family:'Amiri', serif; font-size:18px; cursor:pointer;">تقليدي</button>
                    <button class="font-select-btn" data-font="'Cairo', sans-serif" style="flex:1; padding:10px; border-radius:8px; border:1px solid var(--border-color); background:var(--surface); color:var(--text); font-family:'Cairo', sans-serif; font-size:16px; cursor:pointer;">واضح</button>
                </div>
            </div>
    """
    # Insert before focusModeToggle group
    focus_group_start = '<div class="setting-group">\n                <h4 style="margin: 0 0 8px 0; font-size: 17px; color: var(--text);">تعتيم النص غير المقروء</h4>'
    if focus_group_start not in html:
        # Check actual HTML for focus mode title
        focus_group_start = '<h4 style="margin: 0 0 8px 0; font-size: 17px; color: var(--text);">وضع التركيز (Focus Mode)</h4>'
        
    html = html.replace(focus_group_start, font_html + '\n            <div class="setting-group">\n                ' + focus_group_start)

    # Increment cache buster
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=36', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=36', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)


    # --- UPDATE reader.js ---
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Add fontFamily to default settings
    if "fontFamily:" not in js:
        js = js.replace("spacingAere: false", "spacingAere: false,\n    fontFamily: \"'Tajawal', sans-serif\"")

    # Add load logic
    if "parsed.fontFamily" not in js:
        js = js.replace("if (parsed.spacingAere !== undefined) readerSettings.spacingAere = parsed.spacingAere;", "if (parsed.spacingAere !== undefined) readerSettings.spacingAere = parsed.spacingAere;\n            if (parsed.fontFamily !== undefined) readerSettings.fontFamily = parsed.fontFamily;")

    # Add applyFontFamily() function
    if "function applyFontFamily" not in js:
        apply_font_func = """
function applyFontFamily() {
    const rc = document.getElementById('reader-content');
    if (rc) {
        rc.style.fontFamily = readerSettings.fontFamily;
    }
    
    // Update active button state
    document.querySelectorAll('.font-select-btn').forEach(btn => {
        if (btn.getAttribute('data-font') === readerSettings.fontFamily) {
            btn.style.background = 'var(--primary)';
            btn.style.color = 'white';
            btn.style.borderColor = 'var(--primary)';
        } else {
            btn.style.background = 'var(--surface)';
            btn.style.color = 'var(--text)';
            btn.style.borderColor = 'var(--border-color)';
        }
    });
}
"""
        js += apply_font_func

    # Add applyFontFamily to loadSettings()
    if "applyFontFamily();" not in js:
        js = js.replace("applySpacing();\n}", "applySpacing();\n    applyFontFamily();\n    initFontButtons();\n}")

    # Add initFontButtons()
    if "function initFontButtons" not in js:
        init_font_func = """
function initFontButtons() {
    document.querySelectorAll('.font-select-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            readerSettings.fontFamily = e.target.getAttribute('data-font');
            saveSettings();
            applyFontFamily();
        });
    });
}
"""
        js += init_font_func

    # Add Speed logic
    if "btn-speed-toggle" not in js:
        speed_logic = """
let currentPlaybackRate = 1;
document.addEventListener('DOMContentLoaded', () => {
    const btnSpeed = document.getElementById('btn-speed-toggle');
    if (btnSpeed) {
        btnSpeed.addEventListener('click', () => {
            if (currentPlaybackRate === 1) currentPlaybackRate = 1.25;
            else if (currentPlaybackRate === 1.25) currentPlaybackRate = 1.5;
            else if (currentPlaybackRate === 1.5) currentPlaybackRate = 2;
            else currentPlaybackRate = 1;
            
            btnSpeed.textContent = currentPlaybackRate + 'x';
            if (player && typeof player.setPlaybackRate === 'function') {
                player.setPlaybackRate(currentPlaybackRate);
            }
        });
    }
});
"""
        js += speed_logic

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    print("Added speed and fonts")

if __name__ == '__main__':
    add_speed_and_fonts()
