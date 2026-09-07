import sqlite3
import secrets

def generate_token():
    return secrets.token_urlsafe(8)

conn = sqlite3.connect('backup_bot.db')
cursor = conn.cursor()

cursor.execute("SELECT student_id FROM academy_students WHERE magic_token IS NULL")
students = cursor.fetchall()
for student in students:
    token = generate_token()
    cursor.execute("UPDATE academy_students SET magic_token = ? WHERE student_id = ?", (token, student[0]))

conn.commit()
conn.close()
print("Migration completed.")
