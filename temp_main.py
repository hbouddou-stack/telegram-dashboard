with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

import secrets

if 'import secrets' not in text:
    text = text.replace('import asyncio', 'import asyncio\nimport secrets')

# Manual Add
text = text.replace(
'''INSERT INTO academy_students (student_id, email, dob, first_name, last_name, year, gender, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        \", (student_id, email, dob, first_name, last_name, '1', 'homme', 'manual'))''',
'''INSERT INTO academy_students (student_id, email, dob, first_name, last_name, year, gender, source, magic_token)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        \", (student_id, email, dob, first_name, last_name, '1', 'homme', 'manual', secrets.token_urlsafe(8)))'''
)

text = text.replace(
'''INSERT INTO academy_students (email, dob, first_name, last_name, year, gender, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        \", (email, dob, first_name, last_name, '1', 'homme', 'manual'))''',
'''INSERT INTO academy_students (email, dob, first_name, last_name, year, gender, source, magic_token)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        \", (email, dob, first_name, last_name, '1', 'homme', 'manual', secrets.token_urlsafe(8)))'''
)

# Excel Import (main.py)
text = text.replace(
'''INSERT INTO academy_students (student_id, first_name, last_name, email, phone, gender, payment_status, dob, year, source, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'excel', 1, datetime('now'))
                    \", (student_id, first_name, last_name, email, phone, gender, payment_status, dob, year))''',
'''INSERT INTO academy_students (student_id, first_name, last_name, email, phone, gender, payment_status, dob, year, source, magic_token, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'excel', ?, 1, datetime('now'))
                    \", (student_id, first_name, last_name, email, phone, gender, payment_status, dob, year, secrets.token_urlsafe(8)))'''
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
