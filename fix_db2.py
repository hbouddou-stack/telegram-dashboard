with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('''              # 1. Guarantee official folder link in group_settings
              await db_conn.execute(\"\"\"
                  INSERT INTO group_settings (key, value)
                  VALUES ('folder_link', 'https://t.me/addlist/Yw-eXYtl1BVkYTdk')
                  ON CONFLICT(key) DO UPDATE SET value = 'https://t.me/addlist/Yw-eXYtl1BVkYTdk'
              \"\"\")''', '''              # 1. Guarantee official folder link in group_settings
              try:
                  await db_conn.execute(\"\"\"
                      INSERT INTO group_settings (key, value)
                      VALUES ('folder_link', 'https://t.me/addlist/Yw-eXYtl1BVkYTdk')
                      ON CONFLICT(key) DO UPDATE SET value = 'https://t.me/addlist/Yw-eXYtl1BVkYTdk'
                  \"\"\")
              except Exception as e:
                  logger.error(f"Failed to seed group_settings: {e}")''')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
