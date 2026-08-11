import re

def rewrite_tracker():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Remove the existing reader-progress-tracker
    html = re.sub(r'<!-- Robust Reader Progress Tracker.*?</div>\s*</div>\s*<nav class="bottom-nav">', '<nav class="bottom-nav">', html, flags=re.DOTALL)
    html = re.sub(r'<div class="reader-progress-tracker" id="reader-progress-tracker"([^>]*)>[\s\S]*?</div>\s*</div>\s*<nav class="bottom-nav">', '<nav class="bottom-nav">', html, flags=re.DOTALL)

    # 2. Add it INSIDE bottom-nav
    bottom_nav_match = re.search(r'(<nav class="bottom-nav">)', html)
    if bottom_nav_match:
        tracker_html = """<nav class="bottom-nav" style="position: relative;">
        <!-- Reader Progress Tracker -->
        <div class="reader-progress-tracker" id="reader-progress-tracker" style="display: none; position: absolute; bottom: 100%; left: 0; width: 100%; z-index: 9998; background: var(--surface); border-top: 1px solid var(--border); padding: 12px 20px; direction: rtl; flex-direction: column; gap: 8px; box-shadow: 0 -4px 15px rgba(0,0,0,0.06);">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span>📌</span>
                    <span id="progress-tracker-title" style="font-weight: 800; color: var(--primary); font-size: 14px;">Titre</span>
                </div>
                <span id="progress-tracker-percent" style="color: var(--text-3); font-size: 12px; font-weight: bold;">0%</span>
            </div>
            
            <!-- Dots Container with tight max-width to not be too wide -->
            <div class="progress-chapters-dots" id="progress-tracker-dots" style="display: flex; justify-content: space-between; align-items: center; position: relative; margin: 4px auto 0 auto; padding: 0; width: 100%; max-width: 250px;">
                <div class="progress-line-bg" style="position: absolute; top: 50%; left: 0; right: 0; height: 3px; background: var(--border); transform: translateY(-50%); border-radius: 2px;"></div>
                <div class="progress-line-fill" id="progress-tracker-fill" style="position: absolute; top: 50%; right: 0; height: 3px; background: var(--primary); transform: translateY(-50%); border-radius: 2px; width: 0%; transition: width 0.1s linear;"></div>
                <!-- dots injected dynamically -->
            </div>
        </div>
        """
        html = html.replace(bottom_nav_match.group(1), tracker_html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Rebuilt reader.html tracker position")

if __name__ == '__main__':
    rewrite_tracker()
