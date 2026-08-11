import json

output_lines = []

def log(msg):
    output_lines.append(str(msg))

try:
    with open('telegram-bot-backup/dashboard/transcripts.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    log("Successfully parsed transcripts.json")
    
    # Find Sira lessons
    sira_lessons = []
    for item in data:
        sub = str(item.get('subject', '')).lower()
        les = str(item.get('lesson', '')).lower()
        if 'sira' in sub or 'sira' in les:
            sira_lessons.append(item)
            
    log(f"Found {len(sira_lessons)} Sira lessons:")
    for l in sira_lessons:
        num = l.get('lessonNum')
        name = l.get('lesson')
        themes = l.get('themes', [])
        # Also look for any other keys like thematic_blocks or thematic_nodes
        thematic_blocks = l.get('thematic_blocks', [])
        segments = l.get('segments', [])
        log(f"Lesson {num}: {name} -> themes: {len(themes)}, thematic_blocks: {len(thematic_blocks)}, segments: {len(segments)}")
except Exception as e:
    log(f"Error reading transcripts.json: {e}")

with open('scratch/inspect_sira_14.txt', 'w', encoding='utf-8') as out_f:
    out_f.write('\n'.join(output_lines))
