import re

file_path = "admin.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_panel_html = """
                <div class="axes-full-transcript-panel" id="axes-full-transcript-panel" style="display: none; flex-direction: column; width: 350px; background: var(--bg-card); border-left: 1px solid var(--border); padding: 15px; border-radius: 8px 0 0 8px; box-shadow: -2px 0 5px rgba(0,0,0,0.05); z-index: 10; margin-left: 10px;">
                    <div style="font-weight: bold; color: var(--gold); margin-bottom: 10px; font-size: 1.1rem; border-bottom: 2px solid var(--gold); padding-bottom: 8px;">📖 التفريغ الكامل للدرس</div>
                    <textarea id="full-transcript-textarea" style="flex: 1; width: 100%; border: 1px solid var(--border); border-radius: 6px; padding: 10px; font-family: inherit; font-size: 0.95rem; line-height: 1.6; resize: none; background: rgba(0,0,0,0.02);" readonly></textarea>
                    
                    <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px;">
                        <span style="font-size: 0.8rem; color: var(--text-secondary); text-align: center;">حدد نصاً من الأعلى ثم اختر إجراءً:</span>
                        <button class="btn btn-primary btn-sm" style="background: #10b981; border-color: #10b981; color: white;" onclick="window.importSelectionToNewSubTheme()">➕ إنشاء "sous-thématique" من التحديد</button>
                        <button class="btn btn-secondary btn-sm" onclick="window.importSelectionToNewAxis()">➕ إنشاء محور رئيسي من التحديد</button>
                    </div>
                </div>
"""

search_str = """<div class="axes-editor-content">
                <!-- Sidebar -->"""

if search_str in content:
    content = content.replace(search_str, '<div class="axes-editor-content">' + new_panel_html + '                <!-- Sidebar -->')
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched admin.html with axes-full-transcript-panel")
else:
    print("Could not find insertion point in admin.html")
