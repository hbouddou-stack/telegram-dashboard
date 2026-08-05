import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('C:/Users/Houssam/Desktop/telegram-dashboard/transcripts.json', 'r', encoding='utf-8') as f:
    db = json.load(f)
for lesson in db:
    if lesson.get('subject') == 'sira' and lesson.get('lessonNum') == 15:
        segs = lesson.get('segments', [])
        print(f"Prod DB has {len(segs)} TOTAL segments for Sira 15.")
        blocks = lesson.get('thematic_blocks', [])
        for i, b in enumerate(blocks):
            start = b.get('start_seconds', 0)
            next_start = blocks[i+1].get('start_seconds', 99999) if i+1 < len(blocks) else 99999
            block_segs = [s for s in segs if start <= s.get('sec', 0) < next_start]
            print(f"Block '{b.get('title')}' starts at {start}s has {len(block_segs)} segments.")
