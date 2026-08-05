import sqlite3
import os

dbs = ['academy.db', 'bot.db', 'backup_bot.db', 'telegram_bot.db', 'academy_bot.db', 'bot_database.db']
for db_name in dbs:
    if os.path.exists(db_name):
        print(f"=== DB: {db_name} ===")
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"Tables: {tables}")
            for t in ['settings', 'config', 'bot_settings', 'system_settings']:
                if t in tables:
                    cursor.execute(f"SELECT * FROM {t}")
                    print(f"Content of {t}: {cursor.fetchall()}")
            conn.close()
        except Exception as e:
            print("Error:", e)
