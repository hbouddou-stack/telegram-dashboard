import sqlite3
import json
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 1. Load the SQLite Data (The user's edited version with 5 blocks but only 9 segments)
conn = sqlite3.connect('C:/Users/Houssam/Desktop/Telegram-Bot-Assets/telegram-bot-backup/backup_bot.db')
cur = conn.cursor()
cur.execute('SELECT lesson_data FROM course_transcripts WHERE subject="sira" AND lesson_num=15')
row = cur.fetchone()
if not row:
    print('Error: SQLite data not found.')
    sys.exit(1)
edited_lesson = json.loads(row[0])
edited_blocks = edited_lesson.get('thematic_blocks', [])

# 2. Load the Restored Backup Data (The version with 235 full segments but old blocks)
backup_path = 'C:/Users/Houssam/Desktop/Telegram-Bot-Assets/dashboard/transcripts.json'
with open(backup_path, 'r', encoding='utf-8') as f:
    db = json.load(f)

target_lesson = None
for lesson in db:
    if lesson.get('subject') == 'sira' and lesson.get('lessonNum') == 15:
        # Keep the 235 segments!
        full_segments = lesson.get('segments', [])
        
        # Replace the thematic blocks with the user's edited blocks!
        lesson['thematic_blocks'] = edited_blocks
        target_lesson = lesson
        print(f"Merged {len(edited_blocks)} edited blocks with {len(full_segments)} original segments!")
        break

# 3. Save it back to all 3 locations
with open('C:/Users/Houssam/Desktop/Telegram-Bot-Assets/dashboard/transcripts.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, ensure_ascii=False)
with open('C:/Users/Houssam/Desktop/Telegram-Bot-Assets/telegram-bot-backup/dashboard/transcripts.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, ensure_ascii=False)
with open('C:/Users/Houssam/Desktop/telegram-dashboard/transcripts.json', 'w', encoding='utf-8') as f:
    json.dump(db, f, ensure_ascii=False)

# 4. Update SQLite with the merged lesson
cur.execute('UPDATE course_transcripts SET lesson_data = ? WHERE subject="sira" AND lesson_num=15', (json.dumps(target_lesson, ensure_ascii=False),))
conn.commit()
conn.close()

print('Data recovery and merge complete.')
