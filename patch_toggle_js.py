import re

def patch_js():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # We need to inject the toggle logic and resize observer into initUIControls
    old_init = re.search(r'function initUIControls\(\) \{[\s\S]*?const globalSidebar = document\.getElementById\(\'global-sidebar\'\);', js)
    
    if old_init:
        new_init = """function initUIControls() {
    // Sticky Video Toggle Logic
    const btnSticky = document.getElementById('btn-sticky-toggle');
    const videoWrapper = document.getElementById('video-wrapper');
    const sommaireWrapper = document.getElementById('sommaire-wrapper');
    
    if (btnSticky && videoWrapper && sommaireWrapper) {
        // Toggle pinned state
        btnSticky.addEventListener('click', () => {
            if (videoWrapper.classList.contains('pinned')) {
                // Unpin
                videoWrapper.classList.remove('pinned');
                videoWrapper.style.position = 'relative';
                btnSticky.style.opacity = '0.5';
                btnSticky.title = "Épingler la vidéo";
                sommaireWrapper.style.top = '0px';
            } else {
                // Pin
                videoWrapper.classList.add('pinned');
                videoWrapper.style.position = 'sticky';
                btnSticky.style.opacity = '1';
                btnSticky.title = "Désépingler la vidéo";
                sommaireWrapper.style.top = videoWrapper.offsetHeight + 'px';
            }
        });

        // Keep Sommaire right below the video dynamically
        new ResizeObserver(() => {
            if (videoWrapper.classList.contains('pinned')) {
                sommaireWrapper.style.top = videoWrapper.offsetHeight + 'px';
            }
        }).observe(videoWrapper);
    }

    const globalSidebar = document.getElementById('global-sidebar');"""
        js = js.replace(old_init.group(0), new_init)
        
        with open('reader.js', 'w', encoding='utf-8') as f:
            f.write(js)
        print("JS successfully patched.")
    else:
        print("Could not find initUIControls block")

if __name__ == '__main__':
    patch_js()
