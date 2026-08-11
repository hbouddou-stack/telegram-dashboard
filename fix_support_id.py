import re

with open('handlers/support.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for TELEGRAM_SUPPORT_GROUP_ID checks in support.py
content = re.sub(
    r'if not TELEGRAM_SUPPORT_GROUP_ID:.*?return', 
    '', 
    content, 
    flags=re.DOTALL
)

with open('handlers/support.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Success")
