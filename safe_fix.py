with open("main.py", "r", encoding="utf-8") as f:
    text = f.read()

import secrets

text = "import secrets\n" + text

text = text.replace(
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    1
).replace(
    "(student_id, email, dob, first_name, last_name, '1', 'homme', 'manual'))",
    "(student_id, email, dob, first_name, last_name, '1', 'homme', 'manual', secrets.token_urlsafe(8)))",
    1
)

text = text.replace(
    "VALUES (?, ?, ?, ?, ?, ?, ?)",
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    1
).replace(
    "(email, dob, first_name, last_name, '1', 'homme', 'manual'))",
    "(email, dob, first_name, last_name, '1', 'homme', 'manual', secrets.token_urlsafe(8)))",
    1
)

text = text.replace(
    "year, source, is_active, created_at)",
    "year, source, magic_token, is_active, created_at)",
    1
).replace(
    "'excel', 1, datetime('now'))",
    "'excel', ?, 1, datetime('now'))",
    1
).replace(
    "dob, year))",
    "dob, year, secrets.token_urlsafe(8)))",
    1
)

text = text.replace(
'''            # 1. Guarantee official folder link in group_settings
            await db_conn.execute("""
                CREATE TABLE IF NOT EXISTS group_settings (
                    id INTEGER PRIMARY KEY,
                    general_channel_id TEXT,
                    men_group_id TEXT,
                    women_group_id TEXT,
                    folder_link TEXT,
                    updated_at TEXT
                )
            """)
            await db_conn.execute("""
                INSERT INTO group_settings (id, folder_link, updated_at)
                VALUES (1, 'https://t.me/addlist/Yw-eXYtl1BVkYTdk', datetime('now'))
                ON CONFLICT(id) DO UPDATE SET folder_link = 'https://t.me/addlist/Yw-eXYtl1BVkYTdk'
            """)''',
'''            # 1. Guarantee official folder link in group_settings
            try:
                await db_conn.execute("""
                    INSERT INTO group_settings (key, value)
                    VALUES ('folder_link', 'https://t.me/addlist/Yw-eXYtl1BVkYTdk')
                    ON CONFLICT(key) DO UPDATE SET value = 'https://t.me/addlist/Yw-eXYtl1BVkYTdk'
                """)
            except Exception: pass'''
)

text = text.replace(
'''            # 2. Guarantee Houssam Bouddou is always seeded and visible in table
            await db_conn.execute("""
                INSERT INTO academy_students (student_id, first_name, last_name, email, phone, gender, payment_status, email_sent, is_active, created_at)
                VALUES ('104820', 'Houssam', 'Bouddou', 'h.bouddou@gmail.com', '+33668959911', 'HOMME', 'PAID', 1, 1, datetime('now'))
                ON CONFLICT(student_id) DO UPDATE SET first_name = 'Houssam', last_name = 'Bouddou', email = 'h.bouddou@gmail.com', phone = '+33668959911', gender = 'HOMME', payment_status = 'PAID'
            """)''',
'''            # 2. Guarantee Houssam Bouddou is always seeded and visible in table
            try:
                await db_conn.execute("""
                    INSERT INTO academy_students (student_id, first_name, last_name, email, phone, gender, payment_status, email_sent, is_active, created_at)
                    VALUES ('104820', 'Houssam', 'Bouddou', 'h.bouddou@gmail.com', '+33668959911', 'HOMME', 'PAID', 1, 1, datetime('now'))
                    ON CONFLICT(student_id) DO UPDATE SET first_name = 'Houssam', last_name = 'Bouddou', email = 'h.bouddou@gmail.com', phone = '+33668959911', gender = 'HOMME', payment_status = 'PAID'
                """)
            except Exception: pass'''
)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(text)
