import re

def patch_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Create a sticky wrapper that contains both video-wrapper and sommaire-trigger-wrapper
    # Right now, video-wrapper has sticky. We will remove it and wrap.
    
    # 1. First, strip sticky from video-wrapper
    html = html.replace('<div class="video-container" id="video-wrapper" style="position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">', '<div class="video-container" id="video-wrapper">')

    # 2. Now find the whole block from video-wrapper to the end of sommaire-trigger-wrapper
    block_regex = r'(<div class="video-container" id="video-wrapper">.*?<div class="sommaire-trigger-wrapper">\s*<button id="open-sommaire-btn" class="sommaire-btn">.*?</button>\s*</div>)'
    
    match = re.search(block_regex, html, re.DOTALL)
    
    if match:
        original_block = match.group(1)
        
        # But wait, original block currently has <section class="reader-header"> IN BETWEEN video-wrapper and sommaire-trigger-wrapper!
        # Let's extract them precisely to reorder.
    else:
        print("Regex didn't match perfectly. Let's do a more robust approach.")

    # Robust approach:
    # We want the order to be:
    # <div id="sticky-media-wrapper" style="position:sticky; top:0; z-index:100; box-shadow:0 4px 12px rgba(0,0,0,0.15); background:var(--bg);">
    #    <div class="video-container" id="video-wrapper">...</div>
    #    <div class="sommaire-trigger-wrapper">...</div>
    # </div>
    # <section class="reader-header">...</div>
    
    video_re = re.search(r'<div class="video-container" id="video-wrapper">.*?</div>', html, re.DOTALL)
    header_re = re.search(r'<section class="reader-header">.*?</section>', html, re.DOTALL)
    sommaire_re = re.search(r'<div class="sommaire-trigger-wrapper">.*?</div>', html, re.DOTALL)

    if video_re and header_re and sommaire_re:
        v_str = video_re.group(0)
        h_str = header_re.group(0)
        s_str = sommaire_re.group(0)
        
        # remove them from html
        html = html.replace(v_str, '')
        html = html.replace(h_str, '')
        html = html.replace(s_str, '')
        
        # reconstruct
        new_block = f"""
        <div id="sticky-media-wrapper" style="position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.15); background: var(--bg);">
            {v_str}
            {s_str}
        </div>
        {h_str}
        """
        
        # inject it where header-content used to be (after top-nav)
        html = html.replace('<!-- Header / Video Section -->', '<!-- Header / Video Section -->\n' + new_block)
        
        with open('reader.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML successfully patched.")
    else:
        print("Could not find one of the blocks.")

if __name__ == '__main__':
    patch_html()
