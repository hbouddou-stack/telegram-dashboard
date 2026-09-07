import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

ghost_section = '''    <div id="tab-ghosts" class="tab-content" style="display:none; flex-direction:column; height:100%; overflow:hidden; background:var(--bg);">
        <!-- Header -->
        <div style="padding:15px 15px 10px; background:var(--surface); border-bottom:1px solid var(--border); flex-shrink:0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h2 style="margin:0; font-size:1.1rem; color:var(--text1);">👻 الزوار المجهولون</h2>
                    <p style="margin:4px 0 0; font-size:0.8rem; color:var(--text2);">مستخدمون بدأوا البوت لكن لم يربطوا حسابهم بعد</p>
                </div>
                <button class="btn btn-primary" onclick="loadGhostVisitors()" style="padding:8px 15px; border-radius:8px; font-size:0.85rem;">🔄 تحديث</button>
            </div>
            <div id="ghost-count-badge" style="margin-top:10px; display:none;">
                <span id="ghost-count-text" style="background:rgba(239,68,68,0.15); color:#ef4444; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight:bold;"></span>
            </div>
        </div>
        <!-- List -->
        <div id="ghost-list" style="flex:1; overflow-y:auto; padding:10px;">
            <div style="text-align:center; padding:40px; color:var(--text2);">
                <div style="font-size:3rem; margin-bottom:10px;">👻</div>
                <div>اضغط على "تحديث" لتحميل القائمة</div>
            </div>
        </div>
    </div>

'''

# Inject before tab-settings
target = '\n    <div id="tab-settings" class="tab-content">'
if 'tab-ghosts' not in c:
    if target in c:
        c = c.replace(target, '\n' + ghost_section + '    <div id="tab-settings" class="tab-content">')
        print("Injected before tab-settings")
    else:
        # Try without newline
        target2 = '<div id="tab-settings" class="tab-content">'
        if target2 in c:
            c = c.replace(target2, ghost_section + target2)
            print("Injected before tab-settings (no newline)")
        else:
            print("Could not find tab-settings!")
            for m in re.finditer(r'id="tab-\w+"', c):
                print(c[m.start()-5:m.end()+60].encode('utf-8'))
else:
    print("tab-ghosts already exists")

# Also update switchTab sections array
old_arr = "['overview', 'students', 'sos', 'actions', 'logs', 'settings']"
new_arr = "['overview', 'students', 'sos', 'actions', 'logs', 'settings', 'ghosts']"
if old_arr in c:
    c = c.replace(old_arr, new_arr)
    print("switchTab sections updated")
else:
    # Find the sections array whatever form it takes
    m = re.search(r"const sections = \[.*?\]", c)
    if m:
        print("Found sections:", m.group(0)[:100])
        if 'ghosts' not in m.group(0):
            new_sections = m.group(0).replace(']', ", 'ghosts']")
            c = c.replace(m.group(0), new_sections)
            print("Updated sections")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
