import json
with open('dashboard/transcripts.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

for lesson in db:
    if 'sira' in lesson.get('subject', '').lower():
        print(f"Sira Lesson {lesson.get('lessonNum')}: {len(lesson.get('segments', []))} segments")
        blocks = lesson.get('thematic_blocks', [])
        for i, b in enumerate(blocks):
            start = b.get('start_seconds', 0)
            next_start = blocks[i+1].get('start_seconds', 99999) if i+1 < len(blocks) else 99999
            segs = [s for s in lesson.get('segments', []) if start <= s.get('sec', 0) < next_start]
            print(f"  Block {i+1}: '{b.get('title')}' at {start}s -> {len(segs)} segments")
