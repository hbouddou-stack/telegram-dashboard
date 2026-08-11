import re
with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('WHERE p.alias = ? AND tn.level = 2', 'WHERE p.subject = ? AND tn.level = 2')

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
