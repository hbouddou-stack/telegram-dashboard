import re

def patch_html():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add the toggle button to top-nav
    old_nav = re.search(r'<div class="reader-controls">\s*<button class="control-btn" id="btn-text-minus">', html)
    if old_nav:
        new_nav = """<div class="reader-controls">
                    <button class="control-btn" id="btn-sticky-toggle" title="Épingler/Désépingler la vidéo" style="background:#fee2e2; color:#dc2626; border:1px solid #fecaca; margin-right:4px;">📌</button>
                    <button class="control-btn" id="btn-text-minus">"""
        html = html.replace(old_nav.group(0), new_nav)

    # 2. Fix the sticky wrapper DOM structure
    # The current buggy structure looks like this:
    # <div id="sticky-media-wrapper" style="position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.15); background: var(--bg);">
    #     <div class="video-container" id="video-wrapper">
    #             <div id="youtube-player"></div>
    #     <div class="sommaire-trigger-wrapper">
    #         <button id="open-sommaire-btn" class="sommaire-btn">
    #             <span class="icon">☰</span>
    #             <span class="text" id="current-theme-label">Sommaire (Chapitres)</span>
    #             <span class="chevron">▼</span>
    #         </button>
    #     </div>
    # </div>
    # Let's use regex to replace it with the clean sibling structure
    
    wrapper_re = r'<div id="sticky-media-wrapper".*?</div>\s*</div>\s*</div>' # Wait, there are nested divs.
    # It's safer to just extract everything between <div id="sticky-media-wrapper"... and <section class="reader-header">
    match = re.search(r'<div id="sticky-media-wrapper"[^>]*>([\s\S]*?)<section class="reader-header">', html)
    if match:
        # Replace the whole block
        new_block = """
              <!-- Header / Video Section -->
              <div class="video-container pinned" id="video-wrapper" style="position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                  <div id="youtube-player"></div>
              </div>
              
              <!-- Bouton Sommaire -->
              <div class="sommaire-trigger-wrapper" id="sommaire-wrapper" style="position: sticky; top: 0; z-index: 101;">
                  <button id="open-sommaire-btn" class="sommaire-btn">
                      <span class="icon">☰</span>
                      <span class="text" id="current-theme-label">Sommaire (Chapitres)</span>
                      <span class="chevron">▼</span>
                  </button>
              </div>

              <section class="reader-header">"""
        html = html.replace(match.group(0), new_block)
    else:
        print("Could not find sticky-media-wrapper block")

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML successfully patched.")

if __name__ == '__main__':
    patch_html()
