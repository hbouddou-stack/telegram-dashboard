import re

# 1. Update reader.html
with open('dashboard/reader.html', 'r', encoding='utf-8') as f:
    html = f.read()

# remove the button
html = re.sub(r'<button class="control-btn" id="btn-zen-toggle".*?>👁️</button>\s*', '', html)

with open('dashboard/reader.html', 'w', encoding='utf-8') as f:
    f.write(html)


# 2. Update reader.js
with open('dashboard/reader.js', 'r', encoding='utf-8') as f:
    js = f.read()

# remove logic blocks
js = re.sub(r'// ZEN MODE LOGIC\s*const zenBtn = document\.getElementById\(\'btn-zen-toggle\'\);\s*if \(zenBtn\) \{.*?(?:}\s*){3}', '', js, flags=re.DOTALL)

# remove reference in toggle logic
js = re.sub(r'const btnZen = document\.getElementById\(\'btn-zen-toggle\'\);\s*', '', js)
js = re.sub(r'if \(btnZen\) btnZen\.style\.display = \'none\';\s*', '', js)
js = re.sub(r'if \(btnZen\) btnZen\.style\.display = \'flex\';\s*', '', js)
js = re.sub(r'if \(btnZen\) btnZen\.style\.display = \'inline-flex\';\s*', '', js)

with open('dashboard/reader.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Zen Mode successfully removed.")
