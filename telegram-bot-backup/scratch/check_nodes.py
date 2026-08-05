import sqlite3
import json
db_path = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\backup_bot.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("PRAGMA table_info(thematic_nodes)")
columns = [row[1] for row in c.fetchall()]

c.execute("SELECT * FROM thematic_nodes LIMIT 10")
rows = c.fetchall()
data = {'columns': columns, 'rows': rows}

with open(r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\scratch\nodes_dump.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
