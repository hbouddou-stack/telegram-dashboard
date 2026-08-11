import re

with open('telegram-bot-backup/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject helpers at the top
helpers = """
# --- DB TRANSCRIPTS HELPERS ---
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
# ------------------------------
"""
if "# --- DB TRANSCRIPTS HELPERS ---" not in content:
    content = content.replace("import logging", helpers + "\nimport logging", 1)

# 2. Patch handle_transcripts
handle_transcripts_old = """async def handle_transcripts(request):
    transcripts_path = os.path.join(DASHBOARD_DIR, 'transcripts.json')
    if not os.path.exists(transcripts_path):
        transcripts_path = os.path.join(DASHBOARD_DIR, 'transcripts.json.bak')
    return web.FileResponse(transcripts_path)"""

handle_transcripts_new = """async def handle_transcripts(request):
    try:
        lessons = await load_lessons_from_db()
        return web.json_response(lessons)
    except Exception as e:
        logger.error(f"Error serving transcripts: {e}")
        return web.json_response({"error": str(e)}, status=500)"""

content = content.replace(handle_transcripts_old, handle_transcripts_new)

# 3. Patch save_lesson_axes
content = re.sub(
    r"transcripts_path = 'dashboard/transcripts\.json'\s*if os\.path\.exists\(transcripts_path\):\s*with open\(transcripts_path, 'r', encoding='utf-8'\) as f:\s*lessons = json\.load\(f\)",
    "lessons = await load_lessons_from_db()",
    content
)

# 4. Patch git push blocks (we remove them by replacing the whole write block with DB save)
content = re.sub(
    r"with open\(transcripts_path, 'w', encoding='utf-8'\) as f:\s*json\.dump\(lessons, f, ensure_ascii=False, indent=2\)\s*prod_transcripts.*?subprocess\.run\(\[\"git\", \"push\", \"origin\", \"main\"\], cwd=\"[^\"]*\", check=True\)",
    "await save_lesson_to_db(subject, lesson_num, lesson)",
    content,
    flags=re.DOTALL
)

# Replace the simpler ones if they don't have git push (fallback)
content = re.sub(
    r"with open\(transcripts_path, 'w', encoding='utf-8'\) as f:\s*json\.dump\(lessons, f, ensure_ascii=False, indent=2\)",
    "await save_lesson_to_db(subject, lesson_num, lesson)",
    content
)


with open('telegram-bot-backup/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully.")
