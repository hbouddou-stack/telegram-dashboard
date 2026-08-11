import sqlite3
import json

db_path = 'telegram-bot-backup/backup_bot.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT lesson_data FROM course_transcripts WHERE LOWER(subject) = 'sira' AND lesson_num = 14")
row = cursor.fetchone()
conn.close()

out_lines = []
def log(msg):
    out_lines.append(str(msg))

if row:
    lesson_data = json.loads(row[0])
    log("Keys in lesson_data from DB:")
    log(list(lesson_data.keys()))
    log(f"lesson: {lesson_data.get('lesson')}")
    log(f"lessonNum: {lesson_data.get('lessonNum')}")
    log(f"subject: {lesson_data.get('subject')}")
    
    segments = lesson_data.get('segments', [])
    log(f"Number of segments: {len(segments)}")
    if segments:
        log("Sample segments:")
        log(json.dumps(segments[:5], indent=2, ensure_ascii=False))
        
    thematic_blocks = lesson_data.get('thematic_blocks', [])
    log(f"Number of thematic_blocks: {len(thematic_blocks)}")
    if thematic_blocks:
        log("Sample thematic_blocks:")
        log(json.dumps(thematic_blocks[:5], indent=2, ensure_ascii=False))
        
    full_text = lesson_data.get('full_text', '')
    log(f"Length of full_text: {len(full_text)}")
    log(f"Snippet of full_text: {full_text[:300]}...")
else:
    log("Sira Lesson 14 not found in course_transcripts table!")

with open('scratch/inspect_db_sira_14.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))
