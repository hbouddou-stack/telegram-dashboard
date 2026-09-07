with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('''              # 2. Guarantee Houssam Bouddou is always seeded and visible in table
              await db_conn.execute(\"\"\"
                  INSERT INTO academy_students (student_id, first_name, last_name, email, phone, gender, payment_status, email_sent, is_active, created_at)
                  VALUES ('104820', 'Houssam', 'Bouddou', 'h.bouddou@gmail.com', '+33668959911', 'HOMME', 'PAID', 1, 1, datetime('now'))
                  ON CONFLICT(student_id) DO UPDATE SET first_name = 'Houssam', last_name = 'Bouddou', email = 'h.bouddou@gmail.com', phone = '+33668959911', gender = 'HOMME', payment_status = 'PAID'
              \"\"\")''', '''              # 2. Guarantee Houssam Bouddou is always seeded and visible in table
              try:
                  await db_conn.execute(\"\"\"
                      INSERT INTO academy_students (student_id, first_name, last_name, email, phone, gender, payment_status, email_sent, is_active, created_at)
                      VALUES (104820, 'Houssam', 'Bouddou', 'h.bouddou@gmail.com', '+33668959911', 'HOMME', 'PAID', 1, 1, datetime('now'))
                      ON CONFLICT(student_id) DO UPDATE SET first_name = 'Houssam', last_name = 'Bouddou', email = 'h.bouddou@gmail.com', phone = '+33668959911', gender = 'HOMME', payment_status = 'PAID'
                  \"\"\")
              except Exception as e:
                  logger.error(f"Failed to seed test student: {e}")''')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
