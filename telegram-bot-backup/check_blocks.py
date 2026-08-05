import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/transcripts.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

for lesson in db:
    if lesson.get('subject') == 'sira' and lesson.get('lessonNum') == 15:
        blocks = lesson.get('thematic_blocks', [])
        print(f"Sira Lesson 15 has {len(blocks)} thematic blocks.")
        for i, b in enumerate(blocks):
            print(f"Block {i+1}: '{b.get('title')}' at {b.get('start_seconds')}s")
