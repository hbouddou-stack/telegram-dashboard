import sqlite3
import json

db_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\backup_bot.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT DISTINCT theme, sub_theme FROM questions WHERE subject='fiqh' AND theme IS NOT NULL AND theme != ''")
rows = c.fetchall()

with open(r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\scratch\fiqh_theme_hierarchy.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
