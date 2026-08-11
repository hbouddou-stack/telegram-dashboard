import re

def fix_fonts_and_settings():
    # --- 1. Fix reader.css ---
    with open('reader.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # Replace hardcoded Tajawal in .karaoke-segment etc.
    css = re.sub(r"font-family:\s*'Tajawal',\s*sans-serif;", "font-family: var(--main-font, 'Tajawal', sans-serif);", css)

    # Add active class for font and speed buttons
    active_btn_css = """
.settings-btn-group .btn {
    flex: 1;
    padding: 10px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background: var(--surface);
    color: var(--text);
    cursor: pointer;
    transition: all 0.2s;
    font-weight: bold;
}
.settings-btn-group .btn.active {
    background: var(--primary);
    color: #ffffff;
    border-color: var(--primary);
}
"""
    if ".settings-btn-group" not in css:
        css += active_btn_css

    with open('reader.css', 'w', encoding='utf-8') as f:
        f.write(css)

    # --- 2. Fix reader.html ---
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Change settings-content padding-bottom to 90px
    html = html.replace('id="settings-content" style="padding: 20px;', 'id="settings-content" style="padding: 20px; padding-bottom: 90px;')

    # Replace Font buttons to use new classes
    old_fonts_group = """                <div style="display: flex; gap: 10px; direction: rtl;">
                    <button class="font-select-btn" data-font="'Tajawal', sans-serif" style="flex:1; padding:10px; border-radius:8px; border:1px solid var(--border-color); background:var(--surface); color:var(--text); font-family:'Tajawal', sans-serif; font-size:16px; cursor:pointer;">حديث</button>
                    <button class="font-select-btn" data-font="'Amiri', serif" style="flex:1; padding:10px; border-radius:8px; border:1px solid var(--border-color); background:var(--surface); color:var(--text); font-family:'Amiri', serif; font-size:18px; cursor:pointer;">تقليدي</button>
                    <button class="font-select-btn" data-font="'Cairo', sans-serif" style="flex:1; padding:10px; border-radius:8px; border:1px solid var(--border-color); background:var(--surface); color:var(--text); font-family:'Cairo', sans-serif; font-size:16px; cursor:pointer;">واضح</button>
                </div>"""
    
    new_fonts_group = """                <div class="settings-btn-group" style="display: flex; gap: 10px; direction: rtl;">
                    <button class="btn font-select-btn" data-font="'Tajawal', sans-serif" style="font-family:'Tajawal', sans-serif; font-size:16px;">حديث</button>
                    <button class="btn font-select-btn" data-font="'Amiri', serif" style="font-family:'Amiri', serif; font-size:18px;">تقليدي</button>
                    <button class="btn font-select-btn" data-font="'Cairo', sans-serif" style="font-family:'Cairo', sans-serif; font-size:16px;">واضح</button>
                </div>"""
    
    if old_fonts_group in html:
        html = html.replace(old_fonts_group, new_fonts_group)

    # Add Speed setting below font
    speed_group = """
            <div class="setting-group" style="margin-bottom: 24px;">
                <h4 style="margin: 0 0 8px 0; font-size: 17px; color: var(--text);">سرعة القراءة (Vitesse)</h4>
                <p style="font-size: 13px; color: var(--text-2); margin-top: 0; margin-bottom: 12px;">تغيير سرعة الفيديو.</p>
                <div class="settings-btn-group" style="display: flex; gap: 8px; direction: ltr;">
                    <button class="btn speed-select-btn" data-speed="0.75">0.75x</button>
                    <button class="btn speed-select-btn active" data-speed="1">1x</button>
                    <button class="btn speed-select-btn" data-speed="1.25">1.25x</button>
                    <button class="btn speed-select-btn" data-speed="1.5">1.5x</button>
                    <button class="btn speed-select-btn" data-speed="2">2x</button>
                </div>
            </div>
    """
    
    if "سرعة القراءة" not in html:
        # Insert speed group before focus group
        focus_group_start = '<div class="setting-group">\n                <h4 style="margin: 0 0 8px 0; font-size: 17px; color: var(--text);">تعتيم النص غير المقروء</h4>'
        if focus_group_start not in html:
            focus_group_start = '<h4 style="margin: 0 0 8px 0; font-size: 17px; color: var(--text);">وضع التركيز (Focus Mode)</h4>'
        
        # Need to safely insert before setting-group containing focus_group_start
        # Easier with regex or string find
        parts = html.split('<div class="setting-group">')
        for i, p in enumerate(parts):
            if 'تعتيم النص غير المقروء' in p or 'وضع التركيز (Focus Mode)' in p:
                parts[i] = speed_group + '\n            <div class="setting-group">' + p
                break
        html = '<div class="setting-group">'.join(parts)
        
    # Remove old speed button from sticky header if it's there
    old_speed_btn = '<button class="control-btn" id="btn-speed-toggle" title="Vitesse" style="background:var(--surface); color:var(--text); border:1px solid var(--border-color); border-radius:8px; padding:6px 10px; font-size:14px; margin-right: 4px; font-weight: bold; width: 45px;">1x</button>'
    html = html.replace(old_speed_btn, "")

    # Increment cache buster
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=37', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=37', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)


    # --- 3. Fix reader.js ---
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Fix applyFontFamily
    old_apply_font = """function applyFontFamily() {
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
}"""

    new_apply_font = """function applyFontFamily() {
    document.documentElement.style.setProperty('--main-font', readerSettings.fontFamily);
    
    // Update active button state
    document.querySelectorAll('.font-select-btn').forEach(btn => {
        if (btn.getAttribute('data-font') === readerSettings.fontFamily) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}"""

    js = js.replace(old_apply_font, new_apply_font)

    # Fix Speed logic in JS
    old_speed_logic = """let currentPlaybackRate = 1;
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
});"""

    new_speed_logic = """let currentPlaybackRate = 1;
document.addEventListener('DOMContentLoaded', () => {
    const speedBtns = document.querySelectorAll('.speed-select-btn');
    speedBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            currentPlaybackRate = parseFloat(e.target.getAttribute('data-speed'));
            
            // Update active state
            speedBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            if (player && typeof player.setPlaybackRate === 'function') {
                player.setPlaybackRate(currentPlaybackRate);
            }
        });
    });
});"""

    if old_speed_logic in js:
        js = js.replace(old_speed_logic, new_speed_logic)
    elif "const speedBtns = document.querySelectorAll('.speed-select-btn');" not in js:
        js += "\n" + new_speed_logic

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    print("Fixes applied successfully")

if __name__ == '__main__':
    fix_fonts_and_settings()
