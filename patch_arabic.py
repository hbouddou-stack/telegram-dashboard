import io
import re

with io.open('dashboard/admin_gateway.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the regex bug for Arabic names
text = text.replace("n = n.replace(/[^a-z0-9-]/g, '');", "n = n.replace(/\s+/g, '');")

with io.open('dashboard/admin_gateway.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed Arabic names bug')
