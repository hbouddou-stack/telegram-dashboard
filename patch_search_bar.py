import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_block = r'<div style="display:flex; gap:8px;">\s*<input style="flex:1;" class="search-box" type="text" id="search-input" [^>]*>'

new_block = """<div style="display:flex; gap:8px; margin-bottom:8px;">
                <input style="flex:1; margin-bottom:0;" class="search-box" type="text" id="search-input" placeholder="🔍 Rechercher (nom, email...)" oninput="filterStudents()">
                <button onclick="openDuplicateScanner()" style="background:#8b5cf6; color:white; border:none; border-radius:12px; padding:0 15px; font-weight:bold; cursor:pointer;" title="Scanner les doublons">🔍 Doublons</button>
            </div>"""

text = re.sub(old_block, new_block, text)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed search bar and added doublons button')
