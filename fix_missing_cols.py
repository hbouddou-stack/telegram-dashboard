with open("database.py", "r", encoding="utf-8") as f:
    text = f.read()

old = """        for col, col_def in [
            ('email_opened_at', 'TEXT'),
            ('email_clicked_at', 'TEXT'),
            ('whatsapp_sent', 'INTEGER DEFAULT 0'),
            ('whatsapp_sent_at', 'TEXT'),
            ('whatsapp_clicked_at', 'TEXT'),
            ('last_click_source', 'TEXT'),
            ('group_joined', 'INTEGER DEFAULT 0'),
            ('joined_at', 'TEXT')
        ]:"""

new = """        for col, col_def in [
            ('email_opened_at', 'TEXT'),
            ('email_clicked_at', 'TEXT'),
            ('whatsapp_sent', 'INTEGER DEFAULT 0'),
            ('whatsapp_sent_at', 'TEXT'),
            ('whatsapp_clicked_at', 'TEXT'),
            ('last_click_source', 'TEXT'),
            ('group_joined', 'INTEGER DEFAULT 0'),
            ('joined_at', 'TEXT'),
            ('folder_clicked_at', 'TEXT'),
            ('bot_started_at', 'TEXT'),
            ('excluded', 'INTEGER DEFAULT 0'),
            ('email_sent', 'INTEGER DEFAULT 0'),
            ('email_sent_at', 'TEXT')
        ]:"""

text = text.replace(old, new)
with open("database.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Added all possibly missing columns to init_db migration!")
