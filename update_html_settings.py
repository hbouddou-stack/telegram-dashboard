import re

def update_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add settings button
    if 'id="btn-settings-toggle"' not in html:
        old_buttons = """                    <button class="control-btn" id="btn-text-minus">A-</button>
                    <button class="control-btn" id="btn-text-plus">A+</button>
                    <button class="control-btn" id="btn-theme-toggle">🌙</button>"""
        new_buttons = """                    <button class="control-btn" id="btn-text-minus">A-</button>
                    <button class="control-btn" id="btn-text-plus">A+</button>
                    <button class="control-btn" id="btn-theme-toggle">🌙</button>
                    <button class="control-btn" id="btn-settings-toggle" title="Paramètres de Lecture">⚙️</button>"""
        html = html.replace(old_buttons, new_buttons)

    # 2. Add settings bottom sheet
    if 'id="settings-sheet"' not in html:
        settings_html = """
    <!-- Settings Bottom Sheet -->
    <div class="bottom-sheet-overlay" id="settings-overlay"></div>
    <div class="bottom-sheet" id="settings-sheet">
        <div class="bottom-sheet-header">
            <h3>Paramètres de Lecture</h3>
            <button class="close-sheet" id="close-settings-btn">✕</button>
        </div>
        <div class="bottom-sheet-content" id="settings-content" style="padding: 20px; direction: rtl; text-align: right;">
            <div class="setting-group" style="margin-bottom: 30px;">
                <h4 style="margin: 0 0 8px 0; font-size: 17px; color: var(--text);">وضع التمرير (Scroll Mode)</h4>
                <p style="font-size: 13px; color: var(--text-2); margin-top: 0; margin-bottom: 16px;">كيف تتفاعل الصفحة أثناء قراءة الأستاذ.</p>
                
                <label style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; cursor: pointer; padding: 10px; border-radius: 10px; background: var(--surface); border: 1px solid var(--border-color);">
                    <input type="radio" name="scrollMode" value="zone" style="width: 22px; height: 22px; accent-color: var(--primary);">
                    <div>
                        <div style="font-weight: bold; font-size: 15px; color: var(--text);">وضع الكتاب (موصى به)</div>
                        <div style="font-size: 13px; color: var(--text-2);">تمرير طبيعي، تتحرك الصفحة فقط عند الحاجة.</div>
                    </div>
                </label>
                
                <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; padding: 10px; border-radius: 10px; background: var(--surface); border: 1px solid var(--border-color);">
                    <input type="radio" name="scrollMode" value="teleprompter" style="width: 22px; height: 22px; accent-color: var(--primary);">
                    <div>
                        <div style="font-weight: bold; font-size: 15px; color: var(--text);">وضع التلقين (Teleprompter)</div>
                        <div style="font-size: 13px; color: var(--text-2);">تبقى الجملة المقروءة دائماً في أعلى الشاشة.</div>
                    </div>
                </label>
            </div>
            
            <div class="setting-group">
                <h4 style="margin: 0 0 8px 0; font-size: 17px; color: var(--text);">وضع التركيز (Focus Mode)</h4>
                <p style="font-size: 13px; color: var(--text-2); margin-top: 0; margin-bottom: 16px;">إخفاء باقي النص لتجنب التشتت أثناء الاستماع.</p>
                
                <label style="display: flex; align-items: center; justify-content: space-between; cursor: pointer; background: var(--surface); padding: 16px; border-radius: 12px; border: 1px solid var(--border-color);">
                    <div style="font-weight: bold; font-size: 15px; color: var(--text);">تعتيم النص غير المقروء</div>
                    <label class="switch" style="position: relative; display: inline-block; width: 44px; height: 24px;">
                      <input type="checkbox" id="focusModeToggle" style="opacity: 0; width: 0; height: 0;">
                      <span class="slider round" style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 24px;"></span>
                    </label>
                </label>
            </div>
        </div>
    </div>
"""
        # Inject right after sommaire sheet
        sheet_regex = r'<div class="bottom-sheet" id="sommaire-sheet">[\s\S]*?</div>[\s\S]*?</div>'
        match = re.search(sheet_regex, html)
        if match:
            html = html[:match.end()] + settings_html + html[match.end():]
        else:
            print("Could not find insertion point for settings sheet")
            return

    # Cache bust v=28
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=28', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=28', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Updated reader.html with settings UI")

if __name__ == '__main__':
    update_html()
