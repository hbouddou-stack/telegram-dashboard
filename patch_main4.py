import re

with open('telegram-bot-backup/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences of "lessons = await load_lessons_from_db()" with an indented block
content = content.replace("lessons = await load_lessons_from_db()\n                \n            lesson = next", "lessons = await load_lessons_from_db()\n        if lessons is not None:\n            lesson = next")
content = content.replace("lessons = await load_lessons_from_db()\n                    \n            lesson = next", "lessons = await load_lessons_from_db()\n        if lessons is not None:\n            lesson = next")
content = content.replace("lessons = await load_lessons_from_db()\n            \n            lesson = next", "lessons = await load_lessons_from_db()\n        if True:\n            lesson = next")

with open('telegram-bot-backup/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 4 applied successfully.")
