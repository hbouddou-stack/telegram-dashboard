import re

with open('telegram-bot-backup/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("await save_lesson_to_db(subject, lesson_num, lesson), indent=4)", "await save_lesson_to_db(subject, lesson_num, lesson)")

with open('telegram-bot-backup/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 3 applied successfully.")
