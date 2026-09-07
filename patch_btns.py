import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

old_btns = r'<div style="display:flex; gap:10px; margin-bottom:18px;">\s*<button class="btn btn-danger" id="profile-unlink-btn" onclick="manualUnlink\(\)" style="padding:10px; font-size:0.85rem;">.*?</button>\s*<button class="btn btn-primary" onclick="document.getElementById\(\'student-logs-modal\'\)\.style\.display=\'flex\'" style="padding:10px; font-size:0.85rem; flex:1;">.*?</button>\s*</div>'

match = re.search(old_btns, c, flags=re.DOTALL)
if match:
    new_btns = '''<div style="display:flex; flex-direction:column; gap:8px; margin-bottom:18px; width: 100%; box-sizing:border-box;">
                  <button class="btn btn-primary" onclick="document.getElementById('student-logs-modal').style.display='flex'" style="padding:12px; font-size:0.95rem; width:100%; box-sizing:border-box;">📜 عرض السجل (Historique)</button>
                  <button class="btn btn-danger" id="profile-unlink-btn" onclick="manualUnlink()" style="padding:12px; font-size:0.95rem; width:100%; box-sizing:border-box;">فك ربط تيليجرام (Unlink)</button>
              </div>'''
    c = c[:match.start()] + new_btns + c[match.end():]
    with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Fixed Buttons!')
else:
    print('Failed to find buttons')
