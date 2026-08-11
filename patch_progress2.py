import re

def patch_progress():
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Remove the old reading-progress-container from the top
    html = re.sub(r'<!-- Reading Progress Bar -->.*?</div>\s*</div>\s*', '', html, flags=re.DOTALL)

    # 2. Add it inside sommaire-wrapper
    # Find sommaire-wrapper
    old_sommaire = re.search(r'<div class="sommaire-trigger-wrapper" id="sommaire-wrapper"([^>]*)>(.*?)</div>\s*<section class="reader-header">', html, re.DOTALL)
    
    if old_sommaire:
        attrs = old_sommaire.group(1)
        content = old_sommaire.group(2)
        
        new_sommaire = f"""<div class="sommaire-trigger-wrapper" id="sommaire-wrapper" {attrs}>
            {content}
            <!-- Reading Progress Bar glued to bottom of Sommaire -->
            <div id="reading-progress-container" style="position: absolute; bottom: 0; left: 0; width: 100%; height: 4px; background: rgba(0,0,0,0.05); pointer-events: none;">
                <div id="reading-progress-bar" style="height: 100%; width: 0%; background: var(--primary); transition: width 0.1s ease-out; box-shadow: 0 0 8px var(--primary);"></div>
            </div>
        </div>
        <section class="reader-header">"""
        
        html = html.replace(old_sommaire.group(0), new_sommaire)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    # 3. Update JS to use fallback for scroll calculation
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    old_scroll_logic = re.search(r'// Reading Progress Bar Logic.*?function initUIControls', js, re.DOTALL)
    
    new_scroll_logic = """// Reading Progress Bar Logic
window.addEventListener('scroll', () => {
    updateReadingProgress();
});

// Also listen to touchmove for mobile
window.addEventListener('touchmove', () => {
    updateReadingProgress();
});

function updateReadingProgress() {
    const readerActive = document.getElementById('reader-active-state');
    const progressBar = document.getElementById('reading-progress-bar');
    const tabReader = document.getElementById('tab-reader');
    
    if (readerActive && readerActive.style.display !== 'none' && progressBar && tabReader.classList.contains('active')) {
        const scrollTop = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
        const scrollHeight = Math.max(
            document.documentElement.scrollHeight,
            document.body.scrollHeight
        ) - window.innerHeight;
        
        if (scrollHeight > 0) {
            const progress = (scrollTop / scrollHeight) * 100;
            progressBar.style.width = Math.min(100, Math.max(0, progress)) + '%';
        } else {
            progressBar.style.width = '0%';
        }
    }
}

function initUIControls"""

    if old_scroll_logic:
        js = js.replace(old_scroll_logic.group(0), new_scroll_logic)
    
    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    print("Progress bar logic updated.")

if __name__ == '__main__':
    patch_progress()
