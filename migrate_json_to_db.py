import sqlite3
import json
import os

DB_PATH = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\telegram-bot-backup\backup_bot.db'
JSON_PATH = r'C:\Users\Houssam\Desktop\Telegram-Bot-Assets\transcripts.json'

def migrate():
    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table
    print("Creating course_transcripts table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_transcripts (
            subject TEXT,
            lesson_num INTEGER,
            lesson_data TEXT,
            PRIMARY KEY (subject, lesson_num)
        )
    ''')

    # Load JSON
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} not found.")
        return

    print("Loading transcripts.json...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        lessons = json.load(f)

    # Insert data
    inserted = 0
    updated = 0
    for lesson in lessons:
        subject = lesson.get('subject')
        lesson_num = lesson.get('lessonNum')
        
        if not subject or lesson_num is None:
            print("Skipping invalid lesson entry.")
            continue
            
        try:
            lesson_num_int = int(lesson_num)
        except ValueError:
            print(f"Skipping lesson with invalid number: {lesson_num}")
            continue

        lesson_data = json.dumps(lesson, ensure_ascii=False)

        cursor.execute("SELECT 1 FROM course_transcripts WHERE subject = ? AND lesson_num = ?", (subject, lesson_num_int))
        if cursor.fetchone():
            cursor.execute("UPDATE course_transcripts SET lesson_data = ? WHERE subject = ? AND lesson_num = ?", (lesson_data, subject, lesson_num_int))
            updated += 1
        else:
            cursor.execute("INSERT INTO course_transcripts (subject, lesson_num, lesson_data) VALUES (?, ?, ?)", (subject, lesson_num_int, lesson_data))
            inserted += 1

    conn.commit()
    conn.close()
    
    print(f"Migration completed! Inserted: {inserted}, Updated: {updated}.")

if __name__ == '__main__':
    migrate()
