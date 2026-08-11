import re

def fix_duplicates():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # The goal is to clean up everything between <header class="top-nav">...</header> 
    # and <section class="reader-header">.
    # There should only be ONE video-container and ONE sommaire-trigger-wrapper.
    
    # Let's find the end of top-nav
    top_nav_end = html.find('</header>', html.find('<header class="top-nav">')) + len('</header>')
    
    # Let's find the start of reader-header
    reader_header_start = html.find('<section class="reader-header">', top_nav_end)
    
    if top_nav_end > 0 and reader_header_start > 0:
        # We replace everything in between with the correct, single block
        clean_block = """

            <!-- Header / Video Section -->
            <div class="video-container pinned" id="video-wrapper" style="position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                <div id="youtube-player"></div>
            </div>
            
            <!-- Bouton Sommaire -->
            <div class="sommaire-trigger-wrapper" id="sommaire-wrapper" style="position: sticky; top: 0; z-index: 101; display:flex; justify-content:center; align-items:center; gap:8px;">
                <button id="open-sommaire-btn" class="sommaire-btn" style="flex:1;">
                    <span class="icon">☰</span>
                    <span class="text" id="current-theme-label">Sommaire (Chapitres)</span>
                    <span class="chevron">▼</span>
                </button>
                <button class="control-btn" id="btn-sticky-toggle" title="Désépingler la vidéo" style="background:var(--surface); color:var(--text); border:1.5px solid var(--border-color); border-radius:24px; padding:10px 16px; font-size:16px;">📌</button>
            </div>

            """
        
        new_html = html[:top_nav_end] + clean_block + html[reader_header_start:]
        
        with open('reader.html', 'w', encoding='utf-8') as f:
            f.write(new_html)
        print("Cleaned up duplicates.")
    else:
        print("Could not find boundaries")

if __name__ == '__main__':
    fix_duplicates()
