import sqlite3
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('C:/Users/Houssam/Desktop/Telegram-Bot-Assets/telegram-bot-backup/bot_database.db')
cur = conn.cursor()
cur.execute('SELECT lesson_data FROM course_transcripts WHERE subject="sira" AND lesson_num=15')
row = cur.fetchone()
if row:
    lesson = json.loads(row[0])
    print(f"SQLite DB has {len(lesson.get('segments', []))} segments for Sira 15")
    blocks = lesson.get('thematic_blocks', [])
    print(f"SQLite DB has {len(blocks)} thematic blocks")
    for b in blocks:
        print(f"  - {b.get('title')} (start: {b.get('start_seconds')}s)")
        print(f"    search_text snippet: {b.get('search_text', '')[:100]}")
else:
    print('Not found in SQLite')
