import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('C:/Users/Houssam/Desktop/telegram-dashboard/transcripts.json', 'r', encoding='utf-8') as f:
    db = json.load(f)
for lesson in db:
    if lesson.get('subject') == 'sira' and lesson.get('lessonNum') == 15:
        b = lesson.get('thematic_blocks', [])[-1]
        start = b.get('start_seconds', 0)
        segs = [s for s in lesson.get('segments', []) if start <= s.get('sec', 0) < 99999]
        print(f"Prod DB has {len(segs)} segments for Uhud.")
