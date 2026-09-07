import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the full bottom-nav block
nav_match = re.search(r'<div class="bottom-nav">.*?</div>\s*</div>', c, re.DOTALL)
if nav_match:
    print(nav_match.group(0).encode('utf-8'))
