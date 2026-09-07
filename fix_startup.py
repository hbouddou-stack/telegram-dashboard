with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('''            # 1. Guarantee official folder link in group_settings
            await db_conn.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS group_settings (
                    id INTEGER PRIMARY KEY,
                    general_channel_id TEXT,
                    men_group_id TEXT,
                    women_group_id TEXT,
                    folder_link TEXT,
                    updated_at TEXT
                )
            \"\"\")
            await db_conn.execute(\"\"\"
                INSERT INTO group_settings (id, folder_link, updated_at)
                VALUES (1, 'https://t.me/addlist/Yw-eXYtl1BVkYTdk', datetime('now'))
                ON CONFLICT(id) DO UPDATE SET folder_link = 'https://t.me/addlist/Yw-eXYtl1BVkYTdk'
            \"\"\")''', '''            # 1. Guarantee official folder link in group_settings
            await db_conn.execute(\"\"\"
                INSERT INTO group_settings (key, value)
                VALUES ('folder_link', 'https://t.me/addlist/Yw-eXYtl1BVkYTdk')
                ON CONFLICT(key) DO UPDATE SET value = 'https://t.me/addlist/Yw-eXYtl1BVkYTdk'
            \"\"\")''')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
