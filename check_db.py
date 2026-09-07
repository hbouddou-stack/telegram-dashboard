import sqlite3
c = sqlite3.connect('backup_bot.db').cursor()
print('-- crm_tickets --')
for row in c.execute("PRAGMA table_info(crm_tickets)"): print(row)
print('-- student_logs --')
for row in c.execute("PRAGMA table_info(student_logs)"): print(row)
print('-- gateway_sos --')
for row in c.execute("PRAGMA table_info(gateway_sos)"): print(row)
