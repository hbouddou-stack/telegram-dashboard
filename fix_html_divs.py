import re
with open('dashboard/reader.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the two empty setting-group divs by removing them
text = re.sub(r'<div class="setting-group">\s*<div class="setting-group"', '<div class="setting-group"', text)

with open('dashboard/reader.html', 'w', encoding='utf-8') as w:
    w.write(text)
