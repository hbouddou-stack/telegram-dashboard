with open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

migration_logic = '''        try:
            await db.execute("ALTER TABLE academy_students ADD COLUMN magic_token TEXT")
        except Exception:
            pass
            
        # POPULATE MISSING TOKENS
        try:
            async with db.execute("SELECT student_id FROM academy_students WHERE magic_token IS NULL") as cur:
                rows = await cur.fetchall()
            if rows:
                import secrets
                for row in rows:
                    token = secrets.token_urlsafe(8)
                    await db.execute("UPDATE academy_students SET magic_token = ? WHERE student_id = ?", (token, row[0]))
                await db.commit()
                print(f"Generated {len(rows)} magic tokens for existing students.")
        except Exception as e:
            print(f"Error generating tokens: {e}")
'''

text = text.replace('''        try:
            await db.execute("ALTER TABLE academy_students ADD COLUMN magic_token TEXT")
        except Exception:
            pass''', migration_logic)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
