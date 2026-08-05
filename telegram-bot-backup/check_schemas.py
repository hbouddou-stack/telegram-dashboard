import sqlite3

try:
    conn = sqlite3.connect('backup_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='thematic_nodes';")
    print(cursor.fetchone()[0])
    print("-" * 40)
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='questions';")
    print(cursor.fetchone()[0])
    conn.close()
except Exception as e:
    print(e)
