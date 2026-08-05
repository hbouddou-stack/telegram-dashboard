import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/transcripts.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

for lesson in db:
    if 'uhud' in json.dumps(lesson, ensure_ascii=False).lower() or 'أحد' in json.dumps(lesson, ensure_ascii=False):
        print(f"Found Uhud in Subject: {lesson.get('subject')} - Lesson: {lesson.get('lessonNum')}")
