import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/transcripts.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

for lesson in db:
    if lesson.get('subject') == 'sira_nabawiya_1' and lesson.get('lessonNum') == 15:
        blocks = lesson.get('thematic_blocks', [])
        b = blocks[-1]
        start = b.get('start_seconds', 0)
        segs = [s for s in lesson.get('segments', []) if s.get('sec', 0) >= start]
        print(f"Block '{b.get('title')}' has {len(segs)} segments.")
        for i, s in enumerate(segs[:5]):
            print(f"Seg {i}: {s.get('text')}")
        if len(segs) > 5:
            print("...")
            print(f"Seg {len(segs)-1}: {segs[-1].get('text')}")
