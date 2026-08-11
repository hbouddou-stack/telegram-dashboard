import sqlite3
conn = sqlite3.connect('backup_bot.db')
print(conn.execute('SELECT * FROM programs').fetchall())
