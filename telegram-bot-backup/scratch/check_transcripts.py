import json
import os

paths = [
    'transcripts.json',
    'dashboard/transcripts.json',
    'telegram-bot-backup/dashboard/transcripts.json',
    'telegram-bot-backup/transcripts.json'
]

for p in paths:
    if os.path.exists(p):
        print(f"=== File: {p} ===")
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Valid JSON. Number of items: {len(data)}")
            # Search for lesson 14 of sira
            lesson_14 = [l for l in data if l.get('subject') == 'sira' and l.get('lessonNum') == 14]
            if lesson_14:
                print("Lesson 14 found in JSON!")
                l = lesson_14[0]
                print(f"Title: {l.get('title')}")
                print(f"Has thematic_blocks: {'thematic_blocks' in l} (Count: {len(l.get('thematic_blocks', []))})")
                print(f"Has segments: {'segments' in l} (Count: {len(l.get('segments', []))})")
            else:
                print("Lesson 14 NOT found in Sira!")
        except Exception as e:
            print("Error parsing JSON:", e)
    else:
        print(f"File {p} does not exist.")
