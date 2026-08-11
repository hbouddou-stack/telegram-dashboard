import re

def patch_progress():
    # 1. Update HTML
    with open('reader.html', 'r', encoding='utf-8') as f:
        html = f.read()

    progress_html = """
              <!-- Reading Progress Bar -->
              <div id="reading-progress-container" style="position: fixed; top: 0; left: 0; width: 100%; height: 4px; background: transparent; z-index: 10000; pointer-events: none;">
                  <div id="reading-progress-bar" style="height: 100%; width: 0%; background: var(--primary); transition: width 0.1s ease-out; box-shadow: 0 0 8px var(--primary);"></div>
              </div>
              
              <!-- Top Navigation Bar for Reader only -->"""

    html = html.replace('<!-- Top Navigation Bar for Reader only -->', progress_html)

    with open('reader.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    # 2. Update JS
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    scroll_js = """
// Reading Progress Bar Logic
window.addEventListener('scroll', () => {
    const readerActive = document.getElementById('reader-active-state');
    const progressBar = document.getElementById('reading-progress-bar');
    const tabReader = document.getElementById('tab-reader');
    
    if (readerActive && readerActive.style.display !== 'none' && progressBar && tabReader.classList.contains('active')) {
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        
        if (scrollHeight > 0) {
            const progress = (scrollTop / scrollHeight) * 100;
            progressBar.style.width = Math.min(100, Math.max(0, progress)) + '%';
        } else {
            progressBar.style.width = '0%';
        }
    }
});

function initUIControls() {"""

    js = js.replace('function initUIControls() {', scroll_js)

    with open('reader.js', 'w', encoding='utf-8') as f:
        f.write(js)

    print("Progress bar logic injected.")

if __name__ == '__main__':
    patch_progress()
