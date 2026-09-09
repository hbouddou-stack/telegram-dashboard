import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    html = f.read()

# -------------------------------------------------------
# 1. Replace the old modal HTML
# -------------------------------------------------------
with io.open('modal_dup.html', 'r', encoding='utf-8') as f:
    new_modal_html = f.read()

old_modal_match = re.search(r'<!-- MODAL DOUBLONS -->.*?</div>\s*</div>\s*</div>', html, re.DOTALL)
if old_modal_match:
    html = html[:old_modal_match.start()] + new_modal_html + html[old_modal_match.end():]
    print('Modal HTML replaced')
else:
    print('ERROR: old modal not found')
    
# -------------------------------------------------------
# 2. Replace the JS block (from openDuplicateScanner to toggleDuplicateExclude end)
# -------------------------------------------------------
with io.open('new_dup_js.js', 'r', encoding='utf-8') as f:
    new_js = f.read()

idx1 = html.find('function openDuplicateScanner() {')
# Find the end of toggleDuplicateExclude
idx2 = html.find('async function toggleDuplicateExclude')
# Find the closing of toggleDuplicateExclude
idx3 = html.find('\n        }', idx2 + 100)
# and one more closing brace for the try/catch
idx4 = html.find('\n        }', idx3 + 10)
idx_end = idx4 + len('\n        }')

if idx1 != -1 and idx2 != -1:
    old_js_block = html[idx1:idx_end]
    html = html.replace(old_js_block, '\n        ' + new_js + '\n        ', 1)
    print('JS replaced')
else:
    print('ERROR: JS boundaries not found', idx1, idx2)

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Done')
