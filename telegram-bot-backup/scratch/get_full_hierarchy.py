import sqlite3
import json

db_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\backup_bot.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT DISTINCT subject, theme, sub_theme FROM questions WHERE theme IS NOT NULL AND theme != ''")
rows = c.fetchall()

hierarchy = {}
for sub, th, sth in rows:
    if sub not in hierarchy:
        hierarchy[sub] = {}
    if th not in hierarchy[sub]:
        hierarchy[sub][th] = set()
    if sth and sth.strip():
        hierarchy[sub][th].add(sth)

# Convert sets to lists
for sub in hierarchy:
    for th in hierarchy[sub]:
        hierarchy[sub][th] = list(hierarchy[sub][th])

with open(r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\scratch\full_theme_hierarchy.json', 'w', encoding='utf-8') as f:
    json.dump(hierarchy, f, ensure_ascii=False, indent=2)
