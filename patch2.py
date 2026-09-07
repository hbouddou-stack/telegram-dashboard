import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(r"document.getElementById(\'students-count-display\');", "document.getElementById('students-count-display');")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Patch applied')
