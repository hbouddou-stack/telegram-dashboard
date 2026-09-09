import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

migration_code = """
        # --- MIGRATIONS AUTOMATIQUES ---
        async with aiosqlite.connect(DATABASE_PATH) as db_conn:
            try:
                await db_conn.execute("ALTER TABLE academy_students ADD COLUMN source_file TEXT")
                print("Added source_file column to academy_students")
            except Exception:
                pass
            try:
                await db_conn.execute("ALTER TABLE academy_students ADD COLUMN excluded INTEGER DEFAULT 0")
                print("Added excluded column to academy_students")
            except Exception:
                pass
            await db_conn.commit()
        # -------------------------------
"""

c = c.replace(
    "if hasattr(db, 'ensure_click_tracking_table'):\n            await db.ensure_click_tracking_table()",
    "if hasattr(db, 'ensure_click_tracking_table'):\n            await db.ensure_click_tracking_table()\n" + migration_code
)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Migration injected")
