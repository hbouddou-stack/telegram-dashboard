import sqlite3
import glob

# Find sqlite databases
dbs = glob.glob('*.db') + glob.glob('*.sqlite')
for db in dbs:
    print(db)
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print('  ', [t[0] for t in tables])
        conn.close()
    except Exception as e:
        print(e)
