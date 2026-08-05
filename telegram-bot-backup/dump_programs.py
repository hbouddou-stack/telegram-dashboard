import sqlite3
import json

try:
    conn = sqlite3.connect('backup_bot.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM programs;")
    rows = cursor.fetchall()
    print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
    conn.close()
except Exception as e:
    print(e)
