import urllib.request
import json

out = []
def log(msg):
    out.append(str(msg))

try:
    url = "http://127.0.0.1:8080/transcripts.json"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
    data = json.loads(content)
    
    log(f"Fetched successfully. Length: {len(content)}")
    log(f"Total lessons in returned JSON: {len(data)}")
    
    sira_14 = None
    for l in data:
        if l.get('subject') == 'sira' and str(l.get('lessonNum')) == '14':
            sira_14 = l
            break
            
    if sira_14:
        log("Sira 14 found in response!")
        log(f"Keys: {list(sira_14.keys())}")
        log(f"lesson: {sira_14.get('lesson')}")
        log(f"lessonNum: {sira_14.get('lessonNum')}")
        log(f"thematic_blocks count: {len(sira_14.get('thematic_blocks', []))}")
        log(f"segments count: {len(sira_14.get('segments', []))}")
        
        # Check first block
        blocks = sira_14.get('thematic_blocks', [])
        if blocks:
            log(f"First block: {json.dumps(blocks[0], indent=2, ensure_ascii=False)}")
    else:
        log("Sira 14 NOT found in the HTTP response!")
except Exception as e:
    log(f"Error fetching from local server: {e}")

with open('scratch/fetch_transcripts_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
