import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('C:\\Users\\Houssam\\Desktop\\temp.json', 'r', encoding='utf-8') as f:
    db = json.load(f)
for lesson in db:
    if lesson.get('subject') == 'sira' and lesson.get('lessonNum') == 15:
        b = lesson.get('thematic_blocks', [])[-1]
        print(f"Serveo DB has {len(lesson.get('segments', []))} segments for Sira 15")
        print(f"Serveo DB last block starts at {b.get('start_seconds')}")
