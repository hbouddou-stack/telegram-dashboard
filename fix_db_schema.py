with open("database.py", "r", encoding="utf-8") as f:
    text = f.read()

# First, remove the bad injection
import re
bad_block_pattern = re.compile(r"(\s*if 'last_click_source' not in cols:\s*await db\.execute\('ALTER TABLE academy_students ADD COLUMN last_click_source TEXT'\))\s*try:\s*await db\.execute\('ALTER TABLE academy_students ADD COLUMN email_opened_at TEXT'\).*?try:\s*await db\.execute\('ALTER TABLE academy_students ADD COLUMN joined_at TEXT'\)\s*except Exception:\s*pass", re.DOTALL)

text = bad_block_pattern.sub(r"\1", text)

# Now, inject properly at the end of init_db()
# Find the end of init_db()
# It has `await db.commit()` at the end of `async with aiosqlite.connect(DATABASE_PATH) as db:` block

injection = """
        for col, col_def in [
            ('email_opened_at', 'TEXT'),
            ('email_clicked_at', 'TEXT'),
            ('whatsapp_sent', 'INTEGER DEFAULT 0'),
            ('whatsapp_sent_at', 'TEXT'),
            ('whatsapp_clicked_at', 'TEXT'),
            ('last_click_source', 'TEXT'),
            ('group_joined', 'INTEGER DEFAULT 0'),
            ('joined_at', 'TEXT')
        ]:
            try:
                await db.execute(f'ALTER TABLE academy_students ADD COLUMN {col} {col_def}')
            except Exception:
                pass
"""

target = "        await db.commit()"

text = text.replace(target, injection + "\n" + target, 1)

with open("database.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Schema patched perfectly!")
