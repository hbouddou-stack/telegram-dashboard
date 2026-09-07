import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find switchTab function body
m = re.search(r'function switchTab\(tab\) \{.*?(?=\n\s{0,8}function |\n\s{0,8}async function )', c, re.DOTALL)
if m:
    print(m.group(0)[:1500].encode('utf-8'))
else:
    # Find it another way
    idx = c.find('function switchTab(')
    print(c[idx:idx+800].encode('utf-8'))
