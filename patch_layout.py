import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add Telegram WebApp expand
if 'Telegram.WebApp.expand()' not in c:
    tg_script = '<script src="https://telegram.org/js/telegram-web-app.js"></script>\n<script>if(window.Telegram && window.Telegram.WebApp) { Telegram.WebApp.expand(); }</script>\n'
    c = c.replace('</head>', tg_script + '</head>')
    print("Added Telegram WebApp Expand")

# 2. Move Year and School Level to General Tab
year_chip = '<div class="chip" id="profile-year" style="background:rgba(255,159,10,0.15); border-color:#ff9f0a; color:#ff9f0a; display:flex; justify-content:flex-start; align-items:center; gap:8px;">  : <span id="profile-year-text">-</span></div>'
level_chip = '<div class="chip" id="profile-school-level" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">   : <span id="profile-school-level-text">-</span></div>'

# Remove them from Academy tab
# We use regex to find the chip div blocks, since they contain arabic characters that may have been mangled in python.
c = re.sub(r'<div class="chip" id="profile-year".*?</div>', '', c)
c = re.sub(r'<div class="chip" id="profile-school-level".*?</div>', '', c)

# Insert them into General tab after DOB
dob_regex = r'(<div class="chip" id="profile-dob".*?</div>)'
match = re.search(dob_regex, c)
if match:
    # Use Arabic strings safely as bytes
    new_chips_html = '''
    <div class="chip" id="profile-year" style="background:rgba(255,159,10,0.15); border-color:#ff9f0a; color:#ff9f0a; display:flex; justify-content:flex-start; align-items:center; gap:8px;">🎓 Niveau / Année : <span id="profile-year-text" style="font-weight:bold;">-</span></div>
    <div class="chip" id="profile-school-level" style="background:var(--surface); display:flex; justify-content:flex-start; align-items:center; gap:8px;">🏫 Niveau scolaire : <span id="profile-school-level-text" style="font-weight:bold;">-</span></div>
    '''
    c = c[:match.end()] + new_chips_html + c[match.end():]
    print("Moved Year and Level to General tab")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)

print("SUCCESS")
