with open('sync_sheets.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add import secrets if not exists
if 'import secrets' not in text:
    text = text.replace('import json', 'import json\nimport secrets')

# Replace INSERT
text = text.replace(
'''INSERT INTO academy_students (student_id, academic_id, first_name, last_name, email, phone, gender, payment_status, dob, year, source, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'google_sheets', 1, datetime('now'))
                \", (academic_id, academic_id, first_name, last_name, email, phone, gender, payment_status, dob, year))''',
'''INSERT INTO academy_students (student_id, academic_id, first_name, last_name, email, phone, gender, payment_status, dob, year, source, magic_token, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'google_sheets', ?, 1, datetime('now'))
                \", (academic_id, academic_id, first_name, last_name, email, phone, gender, payment_status, dob, year, secrets.token_urlsafe(8)))'''
)

with open('sync_sheets.py', 'w', encoding='utf-8') as f:
    f.write(text)
