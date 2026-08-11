import json

with open('telegram-bot-backup/dashboard/transcripts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

out_lines = []
def log(msg):
    out_lines.append(str(msg))

for l in data:
    sub = l.get('subject')
    num = l.get('lessonNum')
    blocks = l.get('thematic_blocks', [])
    if blocks:
        log(f"Lesson {sub} {num} has thematic_blocks. Sample block keys: {list(blocks[0].keys())}")
        log(f"Sample block: {json.dumps(blocks[0], indent=2, ensure_ascii=False)}")
        break

# Let's inspect Sira 14 specifically
for l in data:
    sub = l.get('subject')
    num = l.get('lessonNum')
    if sub == 'sira' and (num == 14 or str(num) == '14'):
        blocks = l.get('thematic_blocks', [])
        log(f"\nSira 14 has {len(blocks)} thematic_blocks.")
        if blocks:
            log(f"Keys in Sira 14 block: {list(blocks[0].keys())}")
            log(f"Sira 14 thematic blocks list: {json.dumps(blocks, indent=2, ensure_ascii=False)}")

with open('scratch/inspect_blocks_keys.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))
