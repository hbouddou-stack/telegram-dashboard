import re

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Hide roadmap timeline right border
content = re.sub(r'border-right: 2px dashed #e2e8f0;', 'border-right: none;', content)
# Hide roadmap dots
content = re.sub(r'\.roadmap-node-dot \{', '.roadmap-node-dot {\n            display: none;', content)

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Success timeline css tweak")
