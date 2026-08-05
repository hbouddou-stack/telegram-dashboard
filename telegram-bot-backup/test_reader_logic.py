import json
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/transcripts.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

for lesson in db:
    if lesson.get('subject') == 'sira' and lesson.get('lessonNum') == 15:
        blocks = lesson.get('thematic_blocks', [])
        b = blocks[-1]
        start = b.get('start_seconds', 0)
        segs = [s for s in lesson.get('segments', []) if start <= s.get('sec', 0) < 99999]
        
        blockText = ' '.join([f"[[TS:{s.get('sec')}]]" + s.get('text') for s in segs])
        
        poetryRegex = r"\[POEME(?::(\d+))?\](.*?)\[\/POEME\]"
        
        parts = []
        # Simulate the regex match
        matches = list(re.finditer(poetryRegex, blockText))
        lastIndex = 0
        for match in matches:
            prose = blockText[lastIndex:match.start()]
            if prose:
                parts.append({'type': 'prose', 'content': prose})
            # ... we know there are no matches for Uhud anyway
            
        if lastIndex < len(blockText):
            parts.append({'type': 'prose', 'content': blockText[lastIndex:]})
        if not parts:
            parts.append({'type': 'prose', 'content': blockText})
            
        htmlContent = ""
        for part in parts:
            if part['type'] == 'prose':
                content = part['content']
                if not content.strip():
                    continue
                sentences = re.findall(r'[^.!?]+[.!?]*', content)
                if not sentences:
                    sentences = [content]
                
                pText = ""
                pCount = 0
                for sentence in sentences:
                    pText += sentence.strip() + " "
                    pCount += 1
                    if pCount >= 4:
                        htmlContent += f"<div class=\"reader-paragraph\">[PARAGRAPH: {pText}]</div>\n"
                        pText = ""
                        pCount = 0
                if pText.strip():
                    htmlContent += f"<div class=\"reader-paragraph\">[PARAGRAPH: {pText}]</div>\n"
                    
        print("--- GENERATED HTML CONTENT ---")
        print(htmlContent)
