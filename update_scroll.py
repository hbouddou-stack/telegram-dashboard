import re

def update_karaoke_scroll():
    with open('reader.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Find the scrolling block
    old_scroll = """    if (firstActiveSeg) {
        const rect = firstActiveSeg.getBoundingClientRect();
        const viewHeight = window.innerHeight;
        
        // Smart Auto-scroll based on the FIRST element of the active group
        if (rect.top < viewHeight * 0.2 || rect.bottom > viewHeight * 0.8) {
            if (Date.now() - lastUserScrollTime > 3000) {
                isProgrammaticScroll = true;
                firstActiveSeg.scrollIntoView({ behavior: 'smooth', block: 'center' });
                // Reset programmatic flag after smooth scroll is expected to finish
                setTimeout(() => { isProgrammaticScroll = false; }, 800);
            }
        }
    }"""

    new_scroll = """    if (firstActiveSeg) {
        if (Date.now() - lastUserScrollTime > 3000) {
            const rect = firstActiveSeg.getBoundingClientRect();
            
            // Calculate sticky headers total height
            const videoWrapper = document.getElementById('video-wrapper');
            const summaryMenu = document.getElementById('sommaire-wrapper');
            let offsetHeight = 0;
            
            if (videoWrapper) {
                const style = window.getComputedStyle(videoWrapper);
                if (style.position === 'sticky' || style.position === 'fixed') {
                    offsetHeight += videoWrapper.offsetHeight;
                }
            }
            if (summaryMenu) {
                const style = window.getComputedStyle(summaryMenu);
                if (style.position === 'sticky' || style.position === 'fixed') {
                    offsetHeight += summaryMenu.offsetHeight;
                }
            }
            
            // Add a padding of 30px so the text is not squeezed against the menu
            const targetOffset = offsetHeight + 30;
            
            // If the element is too high (hidden under menus) OR too low (bottom of screen)
            if (rect.top < targetOffset || rect.top > window.innerHeight * 0.65) {
                isProgrammaticScroll = true;
                
                // Calculate absolute scroll position
                const absoluteTop = window.scrollY + rect.top;
                
                window.scrollTo({
                    top: absoluteTop - targetOffset,
                    behavior: 'smooth'
                });
                
                setTimeout(() => { isProgrammaticScroll = false; }, 800);
            }
        }
    }"""

    if old_scroll in js:
        js = js.replace(old_scroll, new_scroll)
        with open('reader.js', 'w', encoding='utf-8') as f:
            f.write(js)
        print("Successfully updated scroll logic in reader.js")
    else:
        print("Could not find old scroll block!")

if __name__ == '__main__':
    update_karaoke_scroll()
