import sqlite3
import sys

try:
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='questions';")
    result = cursor.fetchone()
    if result:
        print(result[0])
    else:
        print("Table 'questions' not found.")
    conn.close()
except Exception as e:
    print("Error:", e)
    sys.exit(1)
