with open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

if 'import secrets' not in text:
    text = text.replace('import json', 'import json\nimport secrets')

# import_students_excel logic
text = text.replace(
'''INSERT INTO academy_students (email, first_name, last_name, phone, gender, payment_status, year, dob)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    \", (email, first_name, last_name, phone, gender, payment_status, year, dob))''',
'''INSERT INTO academy_students (email, first_name, last_name, phone, gender, payment_status, year, dob, magic_token)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    \", (email, first_name, last_name, phone, gender, payment_status, year, dob, secrets.token_urlsafe(8)))'''
)

text = text.replace(
'''INSERT INTO academy_students (student_id, email, first_name, gender, payment_status, telegram_id, telegram_username)
                    VALUES (?, ?, ?, ?, 'PAID', ?, ?)
                    ON CONFLICT(student_id) DO UPDATE SET''',
'''INSERT INTO academy_students (student_id, email, first_name, gender, payment_status, telegram_id, telegram_username, magic_token)
                    VALUES (?, ?, ?, ?, 'PAID', ?, ?, ?)
                    ON CONFLICT(student_id) DO UPDATE SET''')
text = text.replace(
'\"\"\", (sid, email, first_name, gender, telegram_id, username))',
'\"\"\", (sid, email, first_name, gender, telegram_id, username, secrets.token_urlsafe(8)))'
)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
