import re

with open('telegram-bot-backup/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r"lessons = await load_lessons_from_db\(\)\s+lesson = next\(",
    "lessons = await load_lessons_from_db()\n        if True:\n            lesson = next(",
    content
)

with open('telegram-bot-backup/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 5 applied successfully.")
