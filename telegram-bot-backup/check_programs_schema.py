import sqlite3

try:
    conn = sqlite3.connect('backup_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='programs';")
    print(cursor.fetchone()[0])
    conn.close()
except Exception as e:
    print(e)
