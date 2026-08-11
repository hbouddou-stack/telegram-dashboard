import re

with open('telegram-bot-backup/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_helpers = """# --- DB TRANSCRIPTS HELPERS ---
async def load_lessons_from_db():
    import aiosqlite, json
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT lesson_data FROM course_transcripts") as cur:
            rows = await cur.fetchall()
    return [json.loads(r[0]) for r in rows]

async def save_lesson_to_db(subject, lesson_num, lesson_data):
    import aiosqlite, json
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE course_transcripts SET lesson_data = ? WHERE subject = ? AND lesson_num = ?", 
            (json.dumps(lesson_data, ensure_ascii=False), subject, int(lesson_num)))
        await db.commit()
# ------------------------------"""

new_helpers = """# --- DB TRANSCRIPTS HELPERS ---
async def load_lessons_from_db():
    import aiosqlite, json
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT lesson_data FROM course_transcripts") as cur:
            rows = await cur.fetchall()
    return [json.loads(r[0]) for r in rows]

async def update_static_json_cache():
    import json, os
    all_lessons = await load_lessons_from_db()
    root_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'transcripts.json')
    dash_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'transcripts.json')
    try:
        with open(root_path, 'w', encoding='utf-8') as f:
            json.dump(all_lessons, f, ensure_ascii=False)
        with open(dash_path, 'w', encoding='utf-8') as f:
            json.dump(all_lessons, f, ensure_ascii=False)
    except Exception as e:
        import logging
        logging.error(f"Failed to update static JSON cache: {e}")

async def save_lesson_to_db(subject, lesson_num, lesson_data):
    import aiosqlite, json
    from config import DATABASE_PATH
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE course_transcripts SET lesson_data = ? WHERE subject = ? AND lesson_num = ?", 
            (json.dumps(lesson_data, ensure_ascii=False), subject, int(lesson_num)))
        await db.commit()
    await update_static_json_cache()

async def init_static_cache():
    import asyncio
    asyncio.create_task(update_static_json_cache())
# ------------------------------"""

content = content.replace(old_helpers, new_helpers)

# Add init_static_cache() in the main startup block
if "await runner.setup()" in content and "await init_static_cache()" not in content:
    content = content.replace("await runner.setup()", "await runner.setup()\n    await init_static_cache()")

with open('telegram-bot-backup/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 6 applied successfully.")
