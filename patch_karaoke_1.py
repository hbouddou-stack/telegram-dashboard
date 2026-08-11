import re

def patch_karaoke_data():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 1. We need to modify `prepareThematicData` to inject TS markers
    
    # Locate the block loop
    old_block_loop = re.search(r'let blockText = blockSegments\.map\(s => s\.text\)\.join\(\' \'\);', js)
    if not old_block_loop:
        print("Could not find blockText map")
        return
        
    new_block_loop = """let blockText = blockSegments.map(s => `[[TS:${s.sec}]]${s.text}`).join(' ');
        let lastTs = block.start_seconds || 0;
        
        function injectKaraokeSpans(htmlString) {
            let res = htmlString.replace(/\\[\\[TS:(\\d+(?:\\.\\d+)?)\\]\\]/g, (match, sec) => {
                lastTs = sec;
                return `</span><span class="karaoke-segment" data-start="${sec}">`;
            });
            if (res.startsWith('</span>')) {
                res = res.substring(7);
            } else {
                res = `<span class="karaoke-segment" data-start="${lastTs}">` + res;
            }
            res = res + `</span>`;
            // Clean up empty spans
            res = res.replace(/<span[^>]*>\\s*<\\/span>/g, '');
            return res;
        }"""
        
    js = js.replace(old_block_loop.group(0), new_block_loop)
    
    # 2. Modify the HTML generation to use injectKaraokeSpans
    
    # prose paragraph
    js = js.replace('htmlContent += `<div class="reader-paragraph">${formatProse(pText)}</div>`;', 
                    'htmlContent += `<div class="reader-paragraph">${injectKaraokeSpans(formatProse(pText))}</div>`;')
    
    # poetry shatrs
    old_shatr = """const s1 = formatProse(part.shatr1.trim());
                const s2 = formatProse(part.shatr2.trim());"""
    new_shatr = """const s1 = injectKaraokeSpans(formatProse(part.shatr1.trim()));
                const s2 = injectKaraokeSpans(formatProse(part.shatr2.trim()));"""
    js = js.replace(old_shatr, new_shatr)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("Patched prepareThematicData successfully.")

if __name__ == '__main__':
    patch_karaoke_data()
