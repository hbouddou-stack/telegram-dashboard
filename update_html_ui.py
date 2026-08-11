import re

def update_ui():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Wrap the top elements in a sticky container and update sommaire-wrapper
    old_header = """              <!-- Top Navigation Bar for Reader only -->
            <header class="top-nav">
                <button class="menu-btn" style="background:#fef3c7; color:#b45309; border:1px solid #fde68a;" onclick="openMindMap()">
                    <span style="font-size: 16px;">🗺️</span> خريطة
                </button>
                <div class="reader-controls">
                    <button class="control-btn" id="btn-text-minus">A-</button>
                    <button class="control-btn" id="btn-text-plus">A+</button>
                    <button class="control-btn" id="btn-theme-toggle">🌙</button>
                    <button class="control-btn" id="btn-settings-toggle" title="Paramètres de Lecture">⚙️</button>
                </div>
            </header>

            <!-- Header / Video Section -->
            <div class="video-container pinned" id="video-wrapper" style="position: sticky; top: 0; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                <div id="youtube-player"></div>
            </div>
            
            <!-- Bouton Sommaire -->
            <div class="sommaire-trigger-wrapper" id="sommaire-wrapper"  style="position: sticky; top: 0; z-index: 101; display:flex; justify-content:center; align-items:center; gap:8px;">
            
                <button id="open-sommaire-btn" class="sommaire-btn" style="flex:1;">
                    <span class="icon">☰</span>
                    <span class="text" id="current-theme-label">Sommaire (Chapitres)</span>
                    <span class="chevron">▼</span>
                </button>
                <button class="control-btn" id="btn-sticky-toggle" title="Désépingler la vidéo" style="background:var(--surface); color:var(--text); border:1.5px solid var(--border-color); border-radius:24px; padding:10px 16px; font-size:16px;">📌</button>
            
            </div>"""

    new_header = """            <!-- STICKY HEADER CONTAINER -->
            <div id="sticky-header-container" style="position: sticky; top: 0; z-index: 102; background: var(--bg); box-shadow: 0 4px 15px rgba(0,0,0,0.08); transition: transform 0.3s ease;">
                <!-- Top Navigation Bar for Reader only -->
                <header class="top-nav" style="border-bottom: none; padding-bottom: 8px;">
                    <button class="menu-btn" style="background:#fef3c7; color:#b45309; border:1px solid #fde68a;" onclick="openMindMap()">
                        <span style="font-size: 16px;">🗺️</span> خريطة
                    </button>
                    <div class="reader-controls">
                        <button class="control-btn" id="btn-text-minus">A-</button>
                        <button class="control-btn" id="btn-text-plus">A+</button>
                        <button class="control-btn" id="btn-theme-toggle">🌙</button>
                        <button class="control-btn" id="btn-settings-toggle" title="Paramètres de Lecture">⚙️</button>
                    </div>
                </header>

                <!-- Header / Video Section -->
                <div class="video-container" id="video-wrapper" style="position: relative;">
                    <div id="youtube-player"></div>
                </div>
                
                <!-- Unified Dashboard: Sommaire + Progress -->
                <div class="sommaire-trigger-wrapper" id="sommaire-wrapper" style="padding: 10px 20px; display:flex; flex-direction:column; gap:8px; border-bottom:1px solid var(--border-color); background:var(--surface);">
                    
                    <div style="display:flex; justify-content:space-between; align-items:center; width: 100%;">
                        <button id="open-sommaire-btn" class="sommaire-btn" style="flex:1; justify-content:flex-start; background: transparent; border: none; padding: 0;">
                            <span class="icon" style="font-size: 20px;">☰</span>
                            <span class="text" id="current-theme-label" style="font-size: 14px; text-align: right; margin-right: 8px; font-weight: bold; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">Sommaire (Chapitres)</span>
                        </button>
                        <div style="display: flex; gap: 8px;">
                            <button id="prev-theme-btn" style="background:var(--surface-2); border:none; border-radius:8px; padding:6px 10px; cursor:pointer;">▲</button>
                            <button id="next-theme-btn" style="background:var(--surface-2); border:none; border-radius:8px; padding:6px 10px; cursor:pointer;">▼</button>
                            <button class="control-btn" id="btn-sticky-toggle" title="Désépingler la vidéo" style="background:var(--surface); color:var(--text); border:1px solid var(--border-color); border-radius:8px; padding:6px 10px; font-size:14px; margin-right: 4px;">📌</button>
                        </div>
                    </div>

                    <!-- Progress Dots -->
                    <div class="progress-chapters-dots" id="progress-tracker-dots" style="display: flex; justify-content: space-between; align-items: center; position: relative; margin: 4px 0; padding: 0; width: 100%;">
                        <div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 3px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: 0%; transition: width 0.1s linear;"></div>
                        <!-- Dots injected via JS -->
                    </div>
                </div>
            </div>"""

    if old_header in html:
        html = html.replace(old_header, new_header)
    else:
        print("Warning: Could not find old_header block!")

    # 2. Remove the old progress tracker from the bottom of the body
    tracker_regex = r'<div class="reader-progress-tracker" id="reader-progress-tracker"[\s\S]*?</div>\s*</div>'
    html = re.sub(tracker_regex, '', html)

    # 3. Center the Glossary Popup
    old_glossary = """    <div id="glossary-popup" style="display:none; position:fixed; bottom:80px; left:50%; transform:translateX(-50%); width:90%; max-width:400px; background:var(--surface); border-radius:16px; box-shadow:0 10px 25px rgba(0,0,0,0.15); z-index:9999; padding:16px; border-right:4px solid var(--primary);">"""
    new_glossary = """    <div id="glossary-popup-overlay" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:9998; backdrop-filter:blur(2px);"></div>
    <div id="glossary-popup" style="display:none; position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); width:90%; max-width:400px; background:var(--surface); border-radius:16px; box-shadow:0 10px 40px rgba(0,0,0,0.25); z-index:9999; padding:20px; border-right:4px solid var(--primary); text-align:right;">"""
    
    if old_glossary in html:
        html = html.replace(old_glossary, new_glossary)
    else:
        print("Warning: Could not find glossary popup!")

    # Cache bust
    html = re.sub(r'reader\.js\?v=\d+', 'reader.js?v=29', html)
    html = re.sub(r'reader\.css\?v=\d+', 'reader.css?v=29', html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Updated reader.html with UI changes")

if __name__ == '__main__':
    update_ui()
