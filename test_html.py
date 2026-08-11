import json
import re

def test():
    with open('transcripts.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    lesson = d[0]
    block = lesson['thematic_blocks'][0]
    blockSegments = [s for s in lesson['segments'] if s['sec']>=block['start_seconds'] and s['sec']<block['end_seconds']]
    blockText = ' '.join([f"[[TS:{s['sec']}]]" + s['text'] for s in blockSegments])
    
    # Simulate JS logic
    htmlContent = ""
    lastTs = block['start_seconds'] or 0
    
    def formatProse(text):
        if not text: return ''
        result = text
        result = re.sub(r'\{([^{}]+)\}', lambda m: f'<span class="quran-verse">﴿ {m.group(1).strip()} ﴾</span>', result)
        return result

    def injectKaraokeSpans(htmlString):
        nonlocal lastTs
        def repl(match):
            nonlocal lastTs
            lastTs = match.group(1)
            return f'</span><span class="karaoke-segment" data-start="{lastTs}">'
        res = re.sub(r'\[\[TS:(\d+(?:\.\d+)?)\]\]', repl, htmlString)
        if res.startswith('</span>'):
            res = res[7:]
        else:
            res = f'<span class="karaoke-segment" data-start="{lastTs}">' + res
        res += '</span>'
        res = re.sub(r'<span[^>]*>\s*</span>', '', res)
        return res

    poetryRegex = re.compile(r'([^\s*]+(?:\s+[^\s*]+){1,5})\s*\*\*\*\s*([^\s*]+(?:\s+[^\s*]+){1,5})')
    parts = []
    lastIndex = 0
    
    for match in poetryRegex.finditer(blockText):
        prose = blockText[lastIndex:match.start()]
        if prose: parts.append({'type': 'prose', 'content': prose})
        parts.append({
            'type': 'poetry',
            'shatr1': match.group(1),
            'shatr2': match.group(2)
        })
        lastIndex = match.end()
        
    if lastIndex < len(blockText):
        parts.append({'type': 'prose', 'content': blockText[lastIndex:]})
    if not parts:
        parts.append({'type': 'prose', 'content': blockText})
        
    for part in parts:
        if part['type'] == 'prose':
            if not part['content'].strip(): continue
            sentences = re.findall(r'[^.!?]+[.!?]*', part['content']) or [part['content']]
            pText = ""
            pCount = 0
            for sentence in sentences:
                pText += sentence.strip() + " "
                pCount += 1
                if pCount >= 4:
                    htmlContent += f'<div class="reader-paragraph">{injectKaraokeSpans(formatProse(pText))}</div>\n'
                    pText = ""
                    pCount = 0
            if pText.strip():
                htmlContent += f'<div class="reader-paragraph">{injectKaraokeSpans(formatProse(pText))}</div>\n'
        else:
            s1 = injectKaraokeSpans(formatProse(part['shatr1'].strip()))
            s2 = injectKaraokeSpans(formatProse(part['shatr2'].strip()))
            htmlContent += f'<div class="poetry-verse"><div class="shatr">{s1}</div><div class="shatr">{s2}</div></div>\n'
            
    with open('test_output.html', 'w', encoding='utf-8') as f:
        f.write(htmlContent)
    print("Generated test_output.html")

if __name__ == '__main__':
    test()
