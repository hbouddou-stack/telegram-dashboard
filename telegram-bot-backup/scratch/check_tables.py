import sqlite3
import json

db_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\backup_bot.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]

data = {'tables': tables}
if 'programs' in tables:
    c.execute("SELECT * FROM programs LIMIT 10")
    data['programs'] = c.fetchall()

with open(r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\scratch\tables_dump.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
